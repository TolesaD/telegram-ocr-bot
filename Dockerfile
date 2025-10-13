FROM python:3.9-slim

# Install system dependencies including Tesseract with ALL languages
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-all \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Verify Tesseract installation
RUN tesseract --version && tesseract --list-langs | head -20

# Start the bot
CMD ["python", "bot.py"]