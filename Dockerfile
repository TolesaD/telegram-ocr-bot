FROM python:3.9-slim

# Install system dependencies including Tesseract with multiple language packs
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-amh \
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
    tesseract-ocr-heb \
    tesseract-ocr-fas \
    tesseract-ocr-urd \
    tesseract-ocr-tur \
    tesseract-ocr-swa \
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

# Download additional language packs that might not be in the package manager
RUN mkdir -p /usr/share/tesseract-ocr/5/tessdata && \
    cd /usr/share/tesseract-ocr/5/tessdata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/tik.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/snd.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/kur.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/aze.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/kaz.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/uzb.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/tgk.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/kir.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/tir.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/som.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/yor.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/ibo.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/hau.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/zul.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/xho.traineddata && \
    echo "✅ Additional language packs downloaded"

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