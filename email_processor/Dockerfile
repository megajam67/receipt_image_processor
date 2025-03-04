# Use a minimal Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /email_processor

# Install system dependencies required for PostgreSQL integration
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the dependencies file
COPY requirements.txt .

# Install Python dependencies
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create directories for emails and output JSON files
RUN mkdir -p /email_processor/emails /email_processor/output

# Set the default command to run the email processing script
CMD ["python", "process_emails.py"]
