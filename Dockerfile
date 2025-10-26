FROM python:3.9-slim

# Set environment variables for build
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install system dependencies including ALL Tesseract language packs
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-amh \
    # European languages
    tesseract-ocr-fra tesseract-ocr-spa tesseract-ocr-deu tesseract-ocr-ita \
    tesseract-ocr-por tesseract-ocr-rus tesseract-ocr-ukr tesseract-ocr-pol \
    tesseract-ocr-nld tesseract-ocr-swe tesseract-ocr-dan tesseract-ocr-nor \
    tesseract-ocr-fin tesseract-ocr-ell tesseract-ocr-hun tesseract-ocr-ces \
    tesseract-ocr-ron tesseract-ocr-bul tesseract-ocr-hrv tesseract-ocr-srp \
    # Asian languages
    tesseract-ocr-chi-sim tesseract-ocr-chi-tra tesseract-ocr-jpn \
    tesseract-ocr-kor tesseract-ocr-hin tesseract-ocr-ben tesseract-ocr-tel \
    tesseract-ocr-tam tesseract-ocr-kan tesseract-ocr-mal tesseract-ocr-tha \
    tesseract-ocr-vie \
    # Middle Eastern languages
    tesseract-ocr-ara tesseract-ocr-fas tesseract-ocr-urd tesseract-ocr-heb \
    tesseract-ocr-tur \
    # Additional languages
    tesseract-ocr-afr tesseract-ocr-ind tesseract-ocr-swa \
    libtesseract-dev \
    libleptonica-dev \
    pkg-config \
    wget \
    curl \
    # OpenCV dependencies
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Download additional language data for better accuracy
RUN mkdir -p /usr/share/tesseract-ocr/5/tessdata && \
    cd /usr/share/tesseract-ocr/5/tessdata && \
    # Download essential language packs with fallbacks
    for lang in eng amh ara chi_sim chi_tra jpn kor rus hin ben spa fra deu ita por heb tur; do \
        if [ ! -f "${lang}.traineddata" ]; then \
            wget -q "https://github.com/tesseract-ocr/tessdata/raw/main/${lang}.traineddata" || \
            wget -q "https://github.com/tesseract-ocr/tessdata/raw/main/legacy/tessdata/${lang}.traineddata" || \
            echo "Failed to download ${lang}"; \
        fi; \
    done && \
    echo "✅ Language packs installed"

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