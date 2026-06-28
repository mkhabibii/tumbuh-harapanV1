FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install sistem dependencies scikit-learn & pandas
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt agar cache layer Docker efisien
COPY requirements.txt .

# Install dependencies Python
RUN pip install --no-cache-dir -r requirements.txt

# Copy semua file project ke dalam container
COPY . .

# HuggingFace Spaces menggunakan port 7860
EXPOSE 7860

# Jalankan server menggunakan Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:7860", "--workers", "2", "--timeout", "120"]
