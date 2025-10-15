FROM python:3.11-slim

# Install system dependencies including Tesseract and ALL language packs
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-spa \
    tesseract-ocr-fra \
    tesseract-ocr-deu \
    tesseract-ocr-ita \
    tesseract-ocr-por \
    tesseract-ocr-rus \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    tesseract-ocr-jpn \
    tesseract-ocr-kor \
    tesseract-ocr-ara \
    tesseract-ocr-hin \
    tesseract-ocr-ben \
    tesseract-ocr-tam \
    tesseract-ocr-tel \
    tesseract-ocr-mar \
    tesseract-ocr-urd \
    tesseract-ocr-guj \
    tesseract-ocr-kan \
    tesseract-ocr-mal \
    tesseract-ocr-ori \
    tesseract-ocr-pan \
    tesseract-ocr-san \
    tesseract-ocr-sin \
    tesseract-ocr-nep \
    tesseract-ocr-tha \
    tesseract-ocr-vie \
    tesseract-ocr-ind \
    tesseract-ocr-msa \
    tesseract-ocr-fil \
    tesseract-ocr-mya \
    tesseract-ocr-khm \
    tesseract-ocr-lao \
    tesseract-ocr-mon \
    tesseract-ocr-bod \
    tesseract-ocr-heb \
    tesseract-ocr-fas \
    tesseract-ocr-tur \
    tesseract-ocr-kur \
    tesseract-ocr-pus \
    tesseract-ocr-snd \
    tesseract-ocr-uig \
    tesseract-ocr-kaz \
    tesseract-ocr-uzb \
    tesseract-ocr-tgk \
    tesseract-ocr-amh \
    tesseract-ocr-afr \
    tesseract-ocr-swa \
    tesseract-ocr-yor \
    tesseract-ocr-hau \
    tesseract-ocr-ibo \
    tesseract-ocr-zul \
    tesseract-ocr-xho \
    tesseract-ocr-som \
    tesseract-ocr-orm \
    tesseract-ocr-nld \
    tesseract-ocr-swe \
    tesseract-ocr-pol \
    tesseract-ocr-ukr \
    tesseract-ocr-ell \
    tesseract-ocr-bul \
    tesseract-ocr-ces \
    tesseract-ocr-dan \
    tesseract-ocr-fin \
    tesseract-ocr-hun \
    tesseract-ocr-nor \
    tesseract-ocr-ron \
    tesseract-ocr-srp \
    tesseract-ocr-slk \
    tesseract-ocr-slv \
    tesseract-ocr-cat \
    tesseract-ocr-hrv \
    tesseract-ocr-est \
    tesseract-ocr-isl \
    tesseract-ocr-lav \
    tesseract-ocr-lit \
    tesseract-ocr-mkd \
    tesseract-ocr-mlt \
    tesseract-ocr-sqi \
    tesseract-ocr-eus \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the application
CMD ["python", "app.py"]