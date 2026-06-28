---
title: Tumbuh Harapan
emoji: 🌱
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# 🌱 Tumbuh Harapan
> **Aplikasi Deteksi Dini Stunting Berbasis Machine Learning & Generative AI**

**Tumbuh Harapan** adalah platform digital interaktif yang dirancang untuk membantu orang tua, posyandu, dan tenaga medis melakukan pemantauan tumbuh kembang anak secara mandiri guna mencegah risiko stunting. Platform ini mendukung pencapaian SDGs Target 3 (*Good Health and Well-being*) di Indonesia.

---

## 🚀 Fitur Utama

1. **Deteksi Stunting Instan (Machine Learning)**
   - Menggunakan model klasifikasi berbasis Machine Learning (Scikit-Learn) yang dilatih menggunakan Standar Pertumbuhan Anak WHO (Z-Score Tinggi-per-Umur).
   - Klasifikasi akurat dalam 4 kategori status gizi: *Normal*, *Tinggi*, *Stunting*, dan *Berisiko Stunting Tinggi*.

2. **Saran Gizi Kontekstual & Personal (Google Gemini AI)**
   - Menghasilkan saran rekomendasi makanan pendukung secara cerdas dan personal menggunakan **Google Gemini 2.5 Flash**.
   - **Konteks Fleksibel**: Saran gizi disesuaikan secara real-time berdasarkan usia anak, riwayat ASI eksklusif, frekuensi makan harian, serta kondisi ekonomi keluarga (menyarankan alternatif makanan bergizi namun terjangkau seperti tempe, telur, dan tahu untuk ekonomi menengah ke bawah).

3. **Anti-Abuse Protection (Rate Limiter)**
   - Dilengkapi sistem proteksi *Flask-Limiter* (maksimal 10 prediksi per IP per hari) guna menjaga keamanan kuota dan stabilitas API.

4. **Peta Integrasi Fasilitas Kesehatan (Geolocation & Google Maps)**
   - Pencarian satu klik untuk fasilitas rujukan terdekat: *Puskesmas*, *Klinik Bersalin*, dan *Dokter Spesialis Anak* berbasis lokasi pengguna saat ini.

5. **Modern & Responsive UI/UX**
   - Antarmuka berestetika tinggi dilengkapi animasi pemrosesan (*Lottie loading animations*) dan sangat responsif di perangkat desktop maupun smartphone.

---

## 🛠️ Stack Teknologi

- **Core Framework:** Python (Flask), WSGI (Gunicorn)
- **Machine Learning:** Scikit-Learn (dengan serialisasi `joblib`), Pandas, Numpy
- **Generative AI:** Google Gemini SDK (`google-genai` dengan model `gemini-2.5-flash`)
- **Database & Storage:** SQLite3 (untuk logging history deteksi), Git Large File Storage (LFS)
- **Security & Limits:** Flask-Limiter (anti-abuse rate limiting), Flask-CORS
- **Frontend Stack:** HTML5, Vanilla JavaScript, CSS3 (TailwindCSS framework)
- **Deployment:** Docker Container, Hugging Face Spaces

---

## 📦 Menjalankan Secara Lokal

### Prerequisites
- Python 3.10 / 3.11
- Git & Git LFS

### Langkah Setup

1. **Clone repository & masuk ke folder project:**
   ```bash
   git clone https://github.com/mkhabibii/tumbuh-harapanV1.git
   cd tumbuh-harapanV1
   ```

2. **Buat & aktifkan Virtual Environment:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   ```

3. **Install dependensi:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Konfigurasi Environment Variables:**
   Buat file `.env` di direktori root dan isi dengan API Key Gemini kamu:
   ```env
   GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere
   SECRET_KEY=tulis_apa_saja_yang_panjang_dan_aman
   FLASK_ENV=development
   ```

5. **Jalankan Aplikasi:**
   ```bash
   python app.py
   ```
   Buka `http://localhost:7860` di browser Anda.

---

## 🐳 Konfigurasi Deploy (Hugging Face Docker)
Aplikasi ini sudah dipaketkan menggunakan **Docker** sehingga dapat dideploy secara instan di Hugging Face Spaces. Seluruh file biner besar seperti model machine learning (`model_stunting.pkl`) dan file aset gambar dilacak secara aman menggunakan **Git LFS**.



