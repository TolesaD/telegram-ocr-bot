FROM python:3.9-slim

# Install system dependencies including Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-amh \
    tesseract-ocr-ara \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    tesseract-ocr-deu \
    tesseract-ocr-rus \
    tesseract-ocr-chi-sim \
    tesseract-ocr-jpn \
    tesseract-ocr-kor \
    libtesseract-dev \
    libleptonica-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

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