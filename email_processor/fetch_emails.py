import os
import json
import openai
import email
from email import policy
from email.parser import BytesParser

# Load OpenAI API Key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Define category list
CATEGORIES = [
    "Food & Dining", "Travel", "Shopping", "Health", "Entertainment", "Utilities", "Other"
]

def extract_email_text(email_path):
    """Extracts plain text from an email file."""
    with open(email_path, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)
    return msg.get_body(preferencelist=('plain', 'html')).get_content()

def summarize_receipt(text):
    """Sends extracted text to OpenAI API for structured parsing."""
    prompt = (
        "Extract and summarize the following receipt information. "
        "Return a JSON object with: date_of_service, vendor, amount, and "
        f"a category guess from this list: {CATEGORIES}.\n\nReceipt:\n{text}"
    )
    
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    
    return json.loads(response["choices"][0]["message"]["content"])

def main(email_path, output_path):
    """Processes an email receipt and saves structured data as JSON."""
    text = extract_email_text(email_path)
    receipt_data = summarize_receipt(text)
    
    with open(output_path, "w") as f:
        json.dump(receipt_data, f, indent=4)
    
    print(f"Receipt JSON saved to {output_path}")

if __name__ == "__main__":
    email_file = os.getenv("EMAIL_FILE", "sample.eml")  # Default sample file
    output_json = os.getenv("OUTPUT_JSON", "receipt.json")
    main(email_file, output_json)
