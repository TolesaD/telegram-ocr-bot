FROM python:3.9-slim

# Install system dependencies - optimized for all languages
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-all \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify Tesseract installation
RUN tesseract --version && tesseract --list-langs | head -20

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]