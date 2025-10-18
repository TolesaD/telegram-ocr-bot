FROM python:3.9-slim

     # Install system dependencies
     RUN apt-get update && apt-get install -y \
         tesseract-ocr \
         tesseract-ocr-all \
         libtesseract-dev \
         libleptonica-dev \
         pkg-config \
         && apt-get clean \
         && rm -rf /var/lib/apt/lists/*

     # Set working directory
     WORKDIR /app

     # Copy requirements
     COPY requirements.txt .

     # Install Python dependencies
     RUN pip install --no-cache-dir -r requirements.txt

     # Copy application code
     COPY . .

     # Set environment variables
     ENV PYTHONUNBUFFERED=1
     ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata

     # Run the application
     CMD ["python", "app.py"]