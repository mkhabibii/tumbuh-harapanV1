import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, g, render_template
from flask_cors import CORS
import joblib
import pandas as pd
import sqlite3
from datetime import datetime
import google.genai as genai
from google.genai import types
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# --- Load environment variables ---
load_dotenv()

# --- Path settings ---
APP_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(APP_DIR, 'model_stunting.pkl')
DB_PATH = os.path.join(APP_DIR, 'database.db')

# --- Init app ---
app = Flask(__name__)
CORS(app)

# --- Configure Gemini AI (new google.genai SDK) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# --- Rate Limiter anti-abuse ---
# Maksimal 10 prediksi per IP per hari
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# --- Load ML model ---
try:
    model = joblib.load(MODEL_PATH)
    print("[OK] Model loaded successfully")
except FileNotFoundError:
    print(f"[WARN] Model file not found at {MODEL_PATH}")
    model = None

# --- Database helpers ---
def get_db():
    if '_database' not in g:
        g._database = sqlite3.connect(DB_PATH)
        g._database.row_factory = sqlite3.Row
    return g._database

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                age REAL,
                height REAL,
                gender INTEGER,
                status_gizi TEXT,
                probability REAL,
                asi TEXT,
                frekuensi_makan TEXT,
                ekonomi TEXT,
                created_at TEXT
            )
        """)
        for col in ['asi', 'frekuensi_makan', 'ekonomi']:
            try:
                cur.execute(f"ALTER TABLE checks ADD COLUMN {col} TEXT")
            except Exception:
                pass  
        conn.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('_database', None)
    if db is not None:
        db.close()

init_db()


# LABEL MAPPING untuk prompt Gemini
ASI_LABEL = {
    "ya": "Ya, mendapat ASI eksklusif penuh selama 6 bulan",
    "sebagian": "Sebagian (ASI + sufor/MPASI dini sebelum 6 bulan)",
    "tidak": "Tidak, menggunakan susu formula sejak lahir",
    "tidak_tahu": "Tidak diketahui"
}

FREKUENSI_LABEL = {
    "1": "hanya 1 kali sehari (sangat kurang dari standar)",
    "2": "2 kali sehari (di bawah standar)",
    "3": "3 kali sehari (sesuai standar WHO)",
    "4": "4 kali atau lebih sehari (baik)",
    "tidak_teratur": "tidak teratur atau anak susah makan"
}

EKONOMI_LABEL = {
    "rendah": "Rendah — akses pangan terbatas, rekomendasikan makanan terjangkau seperti telur, tempe, tahu",
    "menengah": "Menengah — cukup untuk memenuhi kebutuhan gizi pokok",
    "cukup": "Cukup — tidak ada kendala ekonomi untuk memenuhi gizi anak"
}

# ===================
# ROUTES
# ===================

@app.route("/")
def beranda():
    return render_template("beranda.html")

# Health check endpoint untuk UptimeRobot agar server tidak tidur
@app.route("/health")
def health():
    return jsonify({"status": "ok", "message": "Tumbuh Harapan is running"}), 200

@app.route("/tes-stunting", methods=["GET", "POST"])
@limiter.limit("10 per day", methods=["POST"])  
def tes_stunting():
    if request.method == "GET":
        return render_template("tes_stunting.html")

    if request.method == "POST":
        data = request.get_json()
        required_fields = ['age', 'height', 'gender']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        try:
            if model is None:
                return jsonify({'error': 'Model not loaded'}), 500

            age = float(data['age'])
            if age > 60:
                return jsonify({
                    'error': 'Usia tidak boleh lebih dari 60 bulan'
                }), 400

            height = float(data['height'])
            gender = int(data['gender'])

            df = pd.DataFrame([[gender, age, height]],
                              columns=['Jenis Kelamin', 'Umur (bulan)', 'Tinggi Badan (cm)'])

            pred = model.predict(df)[0]
            prob = float(model.predict_proba(df).max())

            status_map = {
                "severely stunted": "Berisiko stunting tinggi",
                "stunted": "Stunting",
                "normal": "Normal",
                "tinggi": "Tinggi"
            }
            status_display = status_map.get(pred.lower(), "Status Tidak Diketahui")

            # --- Ambil data opsional  ---
            asi = data.get('asi') or None
            frekuensi_makan = data.get('frekuensi_makan') or None
            ekonomi = data.get('ekonomi') or None

            # --- prompt Gemini ---
            gender_text = "Laki-laki" if gender == 1 else "Perempuan"

            # Konteks tambahan dari field opsional
            konteks_tambahan = ""
            if asi and asi in ASI_LABEL:
                konteks_tambahan += f"- Riwayat ASI eksklusif: {ASI_LABEL[asi]}\n"
            if frekuensi_makan and frekuensi_makan in FREKUENSI_LABEL:
                konteks_tambahan += f"- Frekuensi makan saat ini: {FREKUENSI_LABEL[frekuensi_makan]}\n"
            if ekonomi and ekonomi in EKONOMI_LABEL:
                konteks_tambahan += f"- Kondisi ekonomi keluarga: {EKONOMI_LABEL[ekonomi]}\n"

            prompt = (
                f"Anda adalah ahli gizi anak yang ramah, empatik, dan praktis. "
                f"Berikan saran berdasarkan kondisi nyata keluarga.\n\n"
                f"DATA ANAK:\n"
                f"- Usia: {age} bulan\n"
                f"- Tinggi badan: {height} cm\n"
                f"- Jenis kelamin: {gender_text}\n"
                f"- Status gizi: {status_display}\n"
            )

            if konteks_tambahan:
                prompt += f"\nINFORMASI TAMBAHAN:\n{konteks_tambahan}"

            prompt += (
                f"\nTUGAS:\n"
                f"Berikan tepat 4 saran gizi yang SPESIFIK dan PRAKTIS dalam bahasa Indonesia. "
                f"Pertimbangkan semua data di atas. Jika ada kendala ekonomi, "
                f"rekomendasikan bahan terjangkau (telur, tempe, tahu, ikan asin, dll). "
                f"Jika frekuensi makan kurang, sertakan saran menambah frekuensi. "
                f"Setiap saran maksimal 35 kata.\n\n"
                f"FORMAT (HANYA 4 poin bernomor, tanpa kalimat pembuka/penutup):\n"
                f"1. [saran pertama]\n"
                f"2. [saran kedua]\n"
                f"3. [saran ketiga]\n"
                f"4. [saran keempat]"
            )

            try:
                response = gemini_client.models.generate_content(
                    model="models/gemini-2.5-flash",
                    contents=prompt
                )
                saran = response.text
            except Exception as e:
                saran = (
                    "1. Berikan makanan bergizi seimbang setiap hari sesuai usia anak.\n"
                    "2. Pastikan anak mendapat protein hewani seperti telur, tempe, atau ikan setiap hari.\n"
                    "3. Konsultasikan kondisi anak dengan dokter atau ahli gizi terdekat.\n"
                    "4. Pantau tumbuh kembang anak secara rutin di Posyandu atau Puskesmas."
                )
                app.logger.error(f"Gemini API Error: {e}")

            # --- Simpan ke database ---
            conn = get_db()
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO checks
                  (age, height, gender, status_gizi, probability, asi, frekuensi_makan, ekonomi, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)
            ''', (age, height, gender, status_display, prob,
                  asi, frekuensi_makan, ekonomi,
                  datetime.utcnow().isoformat()))
            conn.commit()

            return jsonify({
                'status': status_display,
                'probability': prob,
                'age': age,
                'height': height,
                'gender': gender,
                'saran': saran
            })

        except Exception as e:
            app.logger.error(f"Prediction Error: {e}")
            return jsonify({'error': str(e)}), 400


# Handle rate limit exceeded (error 429)
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        'error': 'Terlalu banyak permintaan. Maksimal 10 prediksi per hari per pengguna. Coba lagi besok.',
        'status': 'rate_limited'
    }), 429


# ===================
# RUN SERVER
# ===================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 7860))
    app.run(host="0.0.0.0", port=port)