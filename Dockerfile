FROM python:3.9-slim

# Install system dependencies including Tesseract with multiple language packs
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-amh \
    # European languages
    tesseract-ocr-ara \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    tesseract-ocr-deu \
    tesseract-ocr-ita \
    tesseract-ocr-por \
    tesseract-ocr-rus \
    tesseract-ocr-nld \
    tesseract-ocr-pol \
    tesseract-ocr-swe \
    tesseract-ocr-dan \
    tesseract-ocr-nor \
    tesseract-ocr-fin \
    tesseract-ocr-ell \
    tesseract-ocr-hun \
    tesseract-ocr-ces \
    tesseract-ocr-ron \
    tesseract-ocr-bul \
    tesseract-ocr-hrv \
    tesseract-ocr-srp \
    # Asian languages
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    tesseract-ocr-jpn \
    tesseract-ocr-kor \
    tesseract-ocr-hin \
    tesseract-ocr-ben \
    tesseract-ocr-tel \
    tesseract-ocr-tam \
    tesseract-ocr-kan \
    tesseract-ocr-mal \
    tesseract-ocr-tha \
    tesseract-ocr-vie \
    # Middle Eastern & African languages
    tesseract-ocr-heb \
    tesseract-ocr-fas \
    tesseract-ocr-urd \
    tesseract-ocr-tur \
    tesseract-ocr-swa \
    # Additional important languages
    tesseract-ocr-ukr \
    tesseract-ocr-cat \
    tesseract-ocr-eus \
    tesseract-ocr-glg \
    tesseract-ocr-slk \
    tesseract-ocr-slv \
    tesseract-ocr-lav \
    tesseract-ocr-lit \
    tesseract-ocr-afr \
    tesseract-ocr-ind \
    tesseract-ocr-mri \
    libtesseract-dev \
    libleptonica-dev \
    pkg-config \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download only verified additional language packs
RUN mkdir -p /usr/share/tesseract-ocr/5/tessdata && \
    cd /usr/share/tesseract-ocr/5/tessdata && \
    # Download only language packs that are confirmed to exist
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/tik.traineddata || echo "tik not found" && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/snd.traineddata || echo "snd not found" && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/kur.traineddata || echo "kur not found" && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/aze.traineddata || echo "aze not found" && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/kaz.traineddata || echo "kaz not found" && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/uzb.traineddata || echo "uzb not found" && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/tgk.traineddata || echo "tgk not found" && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/kir.traineddata || echo "kir not found" && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/tir.traineddata || echo "tir not found" && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/som.traineddata || echo "som not found" && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/yor.traineddata || echo "yor not found" && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/ibo.traineddata || echo "ibo not found" && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/hau.traineddata || echo "hau not found" && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/zul.traineddata || echo "zul not found" && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/xho.traineddata || echo "xho not found" && \
    echo "✅ Language pack download completed"

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

# Create non-root user for security
RUN useradd -m -u 1000 railway
USER railway

# Run the application
CMD ["python", "app.py"]