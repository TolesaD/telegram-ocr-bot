FROM python:3.9-slim

# Set environment variables for build
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install only essential system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-amh \
    libtesseract-dev \
    libleptonica-dev \
    wget \
    curl \
    # Minimal OpenCV dependencies
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Download only English and Amharic language packs
RUN mkdir -p /usr/share/tesseract-ocr/5/tessdata && \
    cd /usr/share/tesseract-ocr/5/tessdata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/amh.traineddata && \
    echo "✅ Language packs downloaded"

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