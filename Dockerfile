FROM python:3.9-slim

# Install system dependencies - optimized for Railway
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
    tesseract-ocr-jpn \
    tesseract-ocr-kor \
    tesseract-ocr-ara \
    tesseract-ocr-hin \
    tesseract-ocr-ben \
    tesseract-ocr-tam \
    tesseract-ocr-tel \
    tesseract-ocr-kan \
    tesseract-ocr-mal \
    tesseract-ocr-tha \
    tesseract-ocr-vie \
    tesseract-ocr-tur \
    tesseract-ocr-pol \
    tesseract-ocr-amh \
    tesseract-ocr-ell \
    tesseract-ocr-heb \
    tesseract-ocr-fas \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Download additional language packs if needed
RUN wget -O /usr/share/tesseract-ocr/4.00/tessdata/afr.traineddata \
    https://github.com/tesseract-ocr/tessdata/raw/main/afr.traineddata

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]