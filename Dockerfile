FROM python:3.9-slim

# Install system dependencies including Tesseract with multiple language packs
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-amh \
    # Essential European languages
    tesseract-ocr-ara \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    tesseract-ocr-deu \
    tesseract-ocr-ita \
    tesseract-ocr-por \
    tesseract-ocr-rus \
    # Essential Asian languages
    tesseract-ocr-chi-sim \
    tesseract-ocr-jpn \
    tesseract-ocr-kor \
    tesseract-ocr-hin \
    # Additional important languages
    tesseract-ocr-ukr \
    tesseract-ocr-tur \
    libtesseract-dev \
    libleptonica-dev \
    pkg-config \
    wget \
    # OpenCV headless dependencies (compatible versions)
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Download only essential language packs
RUN mkdir -p /usr/share/tesseract-ocr/5/tessdata && \
    cd /usr/share/tesseract-ocr/5/tessdata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/amh.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/ara.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/fra.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/spa.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/deu.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/rus.traineddata && \
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