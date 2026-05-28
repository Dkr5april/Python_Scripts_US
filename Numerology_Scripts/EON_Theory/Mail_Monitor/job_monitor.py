import os
import imaplib
import email
from email.header import decode_header
import time
import json
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError 

# --- 1. CONFIGURATION & SETUP ---

# Load variables from .env file
load_dotenv()

# Dictionary to hold all configuration variables
settings = {
    "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
    "IMAP_EMAIL_ADDRESS": os.getenv("IMAP_EMAIL_ADDRESS"),
    "IMAP_PASSWORD": os.getenv("IMAP_PASSWORD"),
    "IMAP_SERVER": os.getenv("IMAP_SERVER", "imap.gmail.com"), # Use default if not set
    "ALERT_EMAIL": os.getenv("ALERT_EMAIL")
}

def check_config():
    """Checks for required keys before running the app."""
    required_keys = ["GEMINI_API_KEY", "IMAP_EMAIL_ADDRESS", "IMAP_PASSWORD"]
    
    missing_keys = [key for key in required_keys if not settings.get(key)]
    
    if missing_keys:
        print("-" * 50)
        raise EnvironmentError(f"ERROR: Missing critical environment variables in .env file: {', '.join(missing_keys)}")
    
    print("Configuration loaded successfully. Initializing AI and IMAP...")

# --- 2. AI PROCESSING FUNCTION ---

def analyze_email_for_job(subject: str, body: str) -> dict:
    """Uses the Gemini API to classify an email as a job posting and extract details."""
    
    # Initialize the client
    try:
        client = genai.Client(api_key=settings["GEMINI_API_KEY"])
    except Exception as e:
        print(f"ERROR: Could not initialize Gemini client. Check GEMINI_API_KEY. Details: {e}")
        return {"is_relevant_job": False}

    # Define the System Prompt
    system_prompt = """
    You are an expert recruitment analyst. Your task is to analyze the provided email subject and body.
    You must determine if the text is a genuine job opportunity, a recruitment message, or a general industry news update. 
    The user is specifically interested in job postings related to SAP SLT, Replication, ABAP, and Data Transformation.
    If it is a relevant job posting, set "is_relevant_job" to true and extract the details.
    Always respond with ONLY a single JSON object that strictly adheres to the schema below.
    """
    
    # Define the Structured Output Schema
    response_schema = {
        "type": "object",
        "properties": {
            "is_relevant_job": {"type": "boolean", "description": "True if the email is a relevant job posting, false otherwise."},
            "job_title": {"type": "string", "description": "The specific title of the job mentioned."},
            "company": {"type": "string", "description": "The name of the company hiring."},
            "location": {"type": "string", "description": "The city, state, or country, or 'Remote'."},
            "key_skills_match": {"type": "array", "items": {"type": "string"}, "description": "List of key skills (SAP SLT, ABAP, etc.) that were matched."},
            "alert_summary": {"type": "string", "description": "A brief, one-sentence summary for the notification."}
        },
        "required": ["is_relevant_job"]
    }

    user_content = f"EMAIL SUBJECT: {subject}\n\nEMAIL BODY:\n{body[:4000]}" # Limit body size

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[user_content],
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=response_schema
            )
        )
        return json.loads(response.text)
        
    except APIError as e:
        print(f"ERROR: Gemini API call failed. Check key and network. Details: {e}")
        return {"is_relevant_job": False}
    except Exception as e:
        print(f"ERROR during AI processing: {e}")
        # Sometimes the model returns non-JSON, so catch general errors
        return {"is_relevant_job": False}

# --- 3. IMAP MONITORING LOGIC ---

def fetch_unread_emails():
    """Connects to Gmail via IMAP and fetches unread message bodies."""
    
    email_address = settings["IMAP_EMAIL_ADDRESS"]
    password = settings["IMAP_PASSWORD"]
    imap_server = settings["IMAP_SERVER"]

    mail = None
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_address, password)
        mail.select("inbox")
        
        status, messages = mail.search(None, 'UNSEEN')
        email_ids = messages[0].split()
        
        emails_to_process = []
        for e_id in email_ids:
            # Fetch the email body
            status, msg_data = mail.fetch(e_id, '(RFC822)')
            if status == 'OK':
                msg = email.message_from_bytes(msg_data[0][1])
                
                # Decode subject
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")
                    
                # Extract the body content (simplistic approach for plain text)
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        ctype = part.get_content_type()
                        cdisp = part.get('Content-Disposition', '')
                        if ctype == 'text/plain' and 'attachment' not in cdisp:
                            body = part.get_payload(decode=True).decode(errors='ignore')
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors='ignore')
                        
                emails_to_process.append({
                    "subject": subject,
                    "body": body,
                    "message_id": e_id.decode()
                })
        
        return emails_to_process

    except imaplib.IMAP4.error as e:
        print(f"IMAP Login Failed: {e}")
        print("ACTION REQUIRED: Check your IMAP_PASSWORD (App Password) and ensure IMAP is enabled in Gmail settings.")
        return []
    finally:
        if mail:
            mail.logout()


def start_monitoring():
    """The main loop that checks for new emails and triggers AI analysis."""
    print("=" * 50)
    print("Starting SAP SLT Job Alert Monitor...")
    print("Checking inbox every 10 minutes...")
    print("=" * 50)
    
    while True:
        new_emails = fetch_unread_emails()
        
        if new_emails:
            print(f"\n[FOUND] {len(new_emails)} new unread email(s). Analyzing...")
            
            for i, mail_data in enumerate(new_emails):
                print(f"--- Processing Email {i+1} ---")
                print(f"Subject: {mail_data['subject'][:80]}...")
                
                # --- CALL AI CLASSIFICATION ---
                ai_result = analyze_email_for_job(mail_data['subject'], mail_data['body'])
                
                if ai_result.get("is_relevant_job"):
                    # --- ALERTING LOGIC ---
                    summary = ai_result.get('alert_summary', f"Job: {ai_result.get('job_title', 'Unknown')}")
                    
                    print("\n[!!! ALERT !!!] RELEVANT JOB DETECTED!")
                    print(f"Summary: {summary}")
                    print(f"   Title: {ai_result.get('job_title', 'N/A')}")
                    print(f"   Company: {ai_result.get('company', 'N/A')}")
                    print(f"   Location: {ai_result.get('location', 'N/A')}")
                    print("---------------------------------------")
                    
                    # TODO: Implement actual email/push alert sending using the ALERT_EMAIL
                    
                else:
                    print("Classification: Not a relevant SAP SLT job posting.")
                
                # OPTIONAL: Mark the email as READ to prevent re-processing
                # if you want to leave it UNREAD for now, skip this part.
                
        else:
            print(f"[{time.strftime('%H:%M:%S')}] No new emails. Sleeping...")
            
        time.sleep(600) # Wait 10 minutes (600 seconds)

# --- 4. MAIN ENTRY POINT ---

if __name__ == '__main__':
    try:
        check_config()
        start_monitoring()
    except EnvironmentError as e:
        print(f"\nFATAL ERROR: {e}")
        print("Please fix the missing keys in your .env file.")
    except Exception as e:
        print(f"\nFATAL UNEXPECTED ERROR: {e}")