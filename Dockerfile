FROM python:3.9-slim

# Install system dependencies including Tesseract with multiple language packs
RUN apt-get update && apt-get install -y \
    # Tesseract OCR and languages
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-amh \
    # Essential languages only to reduce size
    tesseract-ocr-ara \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    tesseract-ocr-deu \
    tesseract-ocr-ita \
    tesseract-ocr-por \
    tesseract-ocr-rus \
    tesseract-ocr-chi-sim \
    tesseract-ocr-jpn \
    tesseract-ocr-kor \
    tesseract-ocr-hin \
    # Tesseract development
    libtesseract-dev \
    libleptonica-dev \
    pkg-config \
    # OpenCV headless dependencies (updated for compatibility)
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    # Utilities
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download only essential language packs
RUN mkdir -p /usr/share/tesseract-ocr/5/tessdata && \
    cd /usr/share/tesseract-ocr/5/tessdata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/amh.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/ara.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/fra.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/spa.traineddata && \
    echo "✅ Essential language packs downloaded"

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata
ENV OMP_THREAD_LIMIT=1
ENV OMP_NUM_THREADS=1

# Create non-root user for security
RUN useradd -m -u 1000 railway
USER railway

# Run the application
CMD ["python", "app.py"]