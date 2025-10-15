FROM python:3.11-slim

# Install system dependencies including Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-amh \
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
    tesseract-ocr-tur \
    tesseract-ocr-nld \
    tesseract-ocr-swe \
    tesseract-ocr-pol \
    tesseract-ocr-ukr \
    tesseract-ocr-ell \
    tesseract-ocr-bul \
    tesseract-ocr-ces \
    tesseract-ocr-dan \
    tesseract-ocr-fin \
    tesseract-ocr-heb \
    tesseract-ocr-hun \
    tesseract-ocr-ind \
    tesseract-ocr-nor \
    tesseract-ocr-ron \
    tesseract-ocr-srp \
    tesseract-ocr-slk \
    tesseract-ocr-slv \
    tesseract-ocr-tha \
    tesseract-ocr-vie \
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