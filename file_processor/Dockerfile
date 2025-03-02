FROM python:3.9-slim

WORKDIR /file_processor

# Install system dependencies for Tesseract OCR and other tools
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libpq-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN apt-get update && apt-get install -y poppler-utils

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create directories for input and output files
RUN mkdir -p /app/input /app/output

# Run the application
CMD ["python", "process_files.py"]