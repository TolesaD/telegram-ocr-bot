FROM python:3.9-slim-bullseye

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-all \
    libgl1-mesa-glx \
    libglib2.0-0 \
    pkg-config \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a non-root user (good practice)
RUN useradd -m -r user && chown -R user:user /app
USER user

# Verify installation
RUN tesseract --version
RUN tesseract --list-langs | head -10

# Start the bot
CMD ["python", "bot.py"]