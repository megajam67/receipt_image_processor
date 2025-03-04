import imaplib
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST", "imap.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 993))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")  # Your Gmail address
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # Your Gmail App Password

def test_gmail_connection():
    """Attempts to connect to Gmail's IMAP server and login."""
    print(f"🔍 Testing IMAP connection to {EMAIL_HOST}:{EMAIL_PORT} as {EMAIL_USERNAME}")

    try:
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL(EMAIL_HOST, EMAIL_PORT)
        mail.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        
        # List available mailboxes
        status, mailboxes = mail.list()
        if status == "OK":
            print("✅ IMAP Connection Successful! Available mailboxes:")
            for mbox in mailboxes:
                print(mbox.decode())

        mail.logout()
    except imaplib.IMAP4.error as e:
        print(f"❌ IMAP Login Failed: {e}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_gmail_connection()
