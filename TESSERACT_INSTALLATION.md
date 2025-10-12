# Tesseract OCR Installation Guide

## Windows
1. Download Tesseract installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (recommended: install to `C:\Program Files\Tesseract-OCR\`)
3. Add Tesseract to your PATH:
   - Press Win + R, type `sysdm.cpl`
   - Click "Environment Variables"
   - In "System Variables", find "Path", click "Edit"
   - Add: `C:\Program Files\Tesseract-OCR\`
4. Restart your command prompt/terminal

## Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install tesseract-ocr
sudo apt install libtesseract-dev