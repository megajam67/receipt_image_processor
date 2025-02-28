import os
import time
import json
import logging
import cv2
import pytesseract
import requests
import psycopg2
from PIL import Image
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('receipt_processor')

# API Configuration
AI_API_KEY = os.getenv('AI_API_KEY')
AI_API_URL = os.getenv('AI_API_URL')

# Database Configuration
DB_HOST = os.getenv('DB_HOST', 'db')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'receipts')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

# Directories
INPUT_DIR = os.getenv('INPUT_DIR', '/app/input')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', '/app/output')


def preprocess_image(image_path):
    """
    Preprocess the image to improve OCR accuracy.
    """
    # Read the image
    img = cv2.imread(image_path)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply thresholding to handle shadows and uneven lighting
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    
    # Apply noise removal
    cleaned = cv2.medianBlur(thresh, 3)
    
    # Save the preprocessed image temporarily
    temp_path = os.path.join(OUTPUT_DIR, "temp_cleaned.jpg")
    cv2.imwrite(temp_path, cleaned)
    
    return temp_path


def extract_text(image_path):
    """
    Extract text from the image using OCR.
    """
    # Preprocess the image
    preprocessed_path = preprocess_image(image_path)
    
    # Perform OCR
    try:
        text = pytesseract.image_to_string(Image.open(preprocessed_path))

        # Ensure extracted text appears in logs
        logger.info(f"Extracted Text for {image_path}:\n{text}")


        # Remove the temporary file
        if os.path.exists(preprocessed_path):
            os.remove(preprocessed_path)
            
        return text
    except Exception as e:
        logger.error(f"Error during OCR: {e}")
        # Clean up in case of error
        if os.path.exists(preprocessed_path):
            os.remove(preprocessed_path)
        return ""


def send_to_ai_api(text):
    """
    Send the extracted text to an AI API for summary and data extraction.
    """
    try:
        headers = {
            'Authorization': f'Bearer {AI_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Construct a prompt that asks for specific fields
        prompt = f"""
        Extract the following information from this receipt text:
        1. Date of service (in YYYY-MM-DD format)
        2. Payee/Vendor name
        3. Total amount
        4. Expense category or purpose (if available)
        
        Receipt text:
        {text}
        
        Return ONLY a JSON object with keys: date, payee, amount, category
        """
        
        payload = {
            'model': 'gpt-4', # Or the model of your choice
            'messages': [
                {'role': 'system', 'content': 'You are an AI that extracts structured data from receipt text.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.3
        }
        
        response = requests.post(AI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        # Extract the content from the AI response
        result = response.json()
        ai_message = result.get('choices', [{}])[0].get('message', {}).get('content', '{}')
        
        # Try to parse the JSON response
        try:
            extracted_data = json.loads(ai_message)
            return extracted_data
        except json.JSONDecodeError:
            # If AI didn't return proper JSON, try to extract data manually
            logger.warning(f"AI didn't return proper JSON. Raw response: {ai_message}")
            extracted_data = {
                'date': extract_date_from_text(ai_message),
                'payee': extract_payee_from_text(ai_message),
                'amount': extract_amount_from_text(ai_message),
                'category': extract_category_from_text(ai_message)
            }
            return extracted_data
            
    except Exception as e:
        logger.error(f"Error calling AI API: {e}")
        return {
            'date': None,
            'payee': None,
            'amount': None,
            'category': None
        }


def extract_date_from_text(text):
    """Fallback method to extract date from text."""
    # Simple implementation - could be improved
    import re
    date_patterns = [
        r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
        r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
        r'\d{2}-\d{2}-\d{4}'   # MM-DD-YYYY
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def extract_payee_from_text(text):
    """Fallback method to extract payee from text."""
    # This would need a more sophisticated implementation
    # For now, return None to indicate extraction failure
    return None


def extract_amount_from_text(text):
    """Fallback method to extract amount from text."""
    import re
    # Look for currency patterns but return only the numeric portion
    match = re.search(r'\$\s*(\d+(?:\.\d{2})?)', text)
    if match:
        return float(match.group(1))  # Convert directly to a float (removes "$")
    return None


def extract_category_from_text(text):
    """Fallback method to extract category from text."""
    # This would need a more sophisticated implementation
    # For now, return None to indicate extraction failure
    return None


def save_to_database(receipt_data, original_filename):
    """
    Save the extracted receipt data to the PostgreSQL database.
    """
    # Add additional fields
    receipt_data['original_filename'] = original_filename
    receipt_data['processed_at'] = datetime.now().isoformat()
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        # Create a cursor
        cur = conn.cursor()
        
        # Execute the INSERT query
        cur.execute(
            """
            INSERT INTO receipts (
                date_of_service, 
                payee, 
                amount, 
                expense_category, 
                original_filename, 
                processed_at
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                receipt_data.get('date'),
                receipt_data.get('payee'),
                receipt_data.get('amount'),
                receipt_data.get('category'),
                receipt_data.get('original_filename'),
                receipt_data.get('processed_at')
            )
        )
        
        # Commit the transaction
        conn.commit()
        
        # Close the cursor and connection
        cur.close()
        conn.close()
        
        logger.info(f"Successfully saved receipt data for {original_filename} to database")
        return True
        
    except Exception as e:
        logger.error(f"Error saving to database: {e}")
        return False


def save_output_json(receipt_data, original_filename):
    """
    Save the extracted receipt data to a JSON file for reference.
    """
    try:
        # Create the output filename
        base_name = os.path.splitext(os.path.basename(original_filename))[0]
        output_filename = f"{base_name}_processed.json"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        # Write the JSON file
        with open(output_path, 'w') as json_file:
            json.dump(receipt_data, json_file, indent=2)
            
        logger.info(f"Saved output JSON to {output_path}")
        
    except Exception as e:
        logger.error(f"Error saving output JSON: {e}")


def process_receipt_image(image_path):
    """
    Process a receipt image through the entire pipeline.
    """
    try:
        logger.info(f"Processing image: {image_path}")
        
        # Extract text from the image
        text = extract_text(image_path)
        if not text:
            logger.error(f"No text could be extracted from {image_path}")
            return False
            
        # Send to AI API for data extraction
        receipt_data = send_to_ai_api(text)
        
        # Save the extracted data
        original_filename = os.path.basename(image_path)
        
        # Save to database
        db_result = save_to_database(receipt_data, original_filename)
        
        # Save output JSON for reference
        save_output_json(receipt_data, original_filename)
        
        return db_result
        
    except Exception as e:
        logger.error(f"Error processing receipt {image_path}: {e}")
        return False


class ReceiptHandler(FileSystemEventHandler):
    """
    Watchdog handler to process new images as they are added to the input directory.
    """
    def on_created(self, event):
        if event.is_directory:
            return
            
        file_path = event.src_path
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Check if the file is an image
        if file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif']:
            # Wait a bit to ensure the file is completely written
            time.sleep(1)
            process_receipt_image(file_path)


def scan_existing_files():
    """
    Scan for existing files in the input directory on startup.
    """
    for filename in os.listdir(INPUT_DIR):
        file_path = os.path.join(INPUT_DIR, filename)
        if os.path.isfile(file_path):
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif']:
                process_receipt_image(file_path)


def main():
    """
    Main function to start the receipt processing service.
    """
    logger.info("Starting Receipt Processing Service")
    
    # Process any existing files
    scan_existing_files()
    
    # Set up a file watcher
    event_handler = ReceiptHandler()
    observer = Observer()
    observer.schedule(event_handler, INPUT_DIR, recursive=False)
    observer.start()
    
    try:
        logger.info(f"Watching for new files in {INPUT_DIR}")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()


if __name__ == "__main__":
    main()