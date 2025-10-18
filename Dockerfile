FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-amh \
    tesseract-ocr-ara \
    tesseract-ocr-chi-sim \
    tesseract-ocr-jpn \
    tesseract-ocr-kor \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    tesseract-ocr-deu \
    tesseract-ocr-por \
    tesseract-ocr-ita \
    tesseract-ocr-rus \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "app.py"]