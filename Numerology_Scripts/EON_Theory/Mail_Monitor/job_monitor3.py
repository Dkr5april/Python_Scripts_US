import os
import imaplib
import email
from email.header import decode_header
import time
import json
import datetime
import requests 
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
    "IMAP_SERVER": os.getenv("IMAP_SERVER", "imap.gmail.com"), 
    "DAYS_TO_CHECK": int(os.getenv("DAYS_TO_CHECK", 1)),
    "MONITOR_INTERVAL_MINUTES": int(os.getenv("MONITOR_INTERVAL_MINUTES", 30)),
    "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
    "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID")
}

# --- 2. AI & FILTERING CRITERIA ---

# Define your strict criteria for the AI's instruction:
JOB_SKILL_CATEGORIES = {
    "Cloud & ALM": ["SAP BTP", "Cloud ALM", "CALM", "Hyperscaler", "AWS", "Azure", "GCP for SAP", "RISE with SAP", "Cloud Connector", "SCC", "IAS/IPS", "DevOps", "CI/CD", "Terraform", "Ansible", "Docker", "Kubernetes"],
    "S/4HANA & Database": ["S/4HANA Migration", "S/4HANA Conversion", "SAP HANA Database Administration", "DMO", "Database Migration Option", "NZDT", "Fiori Launchpad", "SAP Gateway", "SAP Activate", "SLT Replication Server", "LaMa"],
    "System Maintenance": ["Software Update Manager", "SUM", "Kernel Upgrade", "ZDO", "Support Packages", "EHP", "OSS Notes", "SNOTE", "TMS", "Solution Manager", "SolMan", "ChaRM", "Client Copy", "DBA"],
    "Performance & Troubleshooting": ["System Performance Tuning", "ST03N", "ST02", "SM21", "ST22", "Background Job Management", "SM37", "High Availability", "DR", "Backup & Recovery"],
    "Security & OS": ["SU01", "PFCG", "SAP Security Hardening", "SSO", "SAML 2.0", "Linux", "SUSE", "Red Hat", "Windows Server", "SOX", "GDPR", "SAP Router", "Web Dispatcher", "Shell", "Python", "PowerShell"]
}

TARGET_JOB_TITLES = [
    "SAP Basis Administrator", "SAP Basis Consultant", "SAP HANA Administrator", "SAP Security/GTS Administrator",
    "SAP Basis Lead", "SAP Basis Team Lead", "SAP Basis Manager", "SAP Basis Architect", 
    "SAP Technical Architect", "SAP Cloud Architect", "SAP BTP Administrator", 
    "DevOps Engineer for SAP", "SAP CALM Specialist"
]

MIN_KEYWORDS_REQUIRED = 5
MIN_CATEGORIES_REQUIRED = 2


def check_config():
    """Checks for required keys before running the app."""
    required_keys = ["GEMINI_API_KEY", "IMAP_EMAIL_ADDRESS", "IMAP_PASSWORD", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
    
    missing_keys = [key for key in required_keys if not settings.get(key)]
    
    if missing_keys:
        print("-" * 50)
        raise EnvironmentError(f"ERROR: Missing critical environment variables in .env file: {', '.join(missing_keys)}")
    
    print("Configuration loaded successfully. Initializing AI, IMAP, and Telegram...")

# --- 3. TELEGRAM ALERTING FUNCTION ---

def send_telegram_alert(text: str):
    """Sends a message directly to Telegram via the Bot API."""
    token = settings["TELEGRAM_BOT_TOKEN"]
    chat_id = settings["TELEGRAM_CHAT_ID"]
    
    if not token or not chat_id:
        print("ALERT ERROR: Telegram credentials missing in .env. Cannot send alert.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # Use HTML formatting for better readability
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html_text = f"<b>🚨 CRITICAL JOB ALERT</b>\n\n{text}"
    
    payload = {
        'chat_id': chat_id,
        'text': html_text,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status() 
        print("✅ ALERT SENT successfully to Telegram.")
        return True
    except Exception as e:
        print(f"ALERT ERROR: Failed to send Telegram message: {e}")
        return False

# --- 4. NEW: FAILURE ALERT FUNCTION ---

def send_failure_alert(error_message: str):
    """Sends a critical message directly to Telegram when the script encounters a fatal error."""
    token = settings["TELEGRAM_BOT_TOKEN"]
    chat_id = settings["TELEGRAM_CHAT_ID"]
    
    if not token or not chat_id:
        print("FATAL ERROR: Script failed and Telegram credentials missing.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # Use HTML formatting for high visibility
    # Escape HTML characters in the error message for safety
    safe_error_message = error_message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html_text = (
        f"<b>❌ FATAL SCRIPT ERROR</b>\n\n"
        f"The SAP Job Monitor script has terminated unexpectedly.\n\n"
        f"<b>Error Details:</b>\n"
        f"<pre>{safe_error_message}</pre>" # Use <pre> tag for code/error display
    )
    
    payload = {
        'chat_id': chat_id,
        'text': html_text,
        'parse_mode': 'HTML'
    }
    
    try:
        requests.post(url, data=payload)
        print("\n❌ FATAL ERROR ALERT SENT to Telegram.")
    except Exception as e:
        print(f"CRITICAL: Could not send failure alert to Telegram: {e}")

# --- 5. IMAP UTILITIES ---

def mark_email_as_read(message_id: str):
    """Connects to IMAP and marks the email corresponding to the message_id as SEEN."""
    mail = None
    try:
        mail = imaplib.IMAP4_SSL(settings["IMAP_SERVER"])
        mail.login(settings["IMAP_EMAIL_ADDRESS"], settings["IMAP_PASSWORD"])
        mail.select("inbox")
        
        # Use the message_id (e_id) to flag the email as SEEN
        mail.store(message_id, '+FLAGS', '\\Seen')
        print(f"📧 Marked email {message_id} as READ (\\Seen).")

    except imaplib.IMAP4.error as e:
        print(f"ERROR: Failed to mark email as read: {e}")
    finally:
        if mail:
            mail.logout()

# --- 6. AI PROCESSING FUNCTION ---

def analyze_email_for_job(subject: str, body: str) -> dict:
    
    try:
        client = genai.Client(api_key=settings["GEMINI_API_KEY"])
    except Exception as e:
        print(f"ERROR: Could not initialize Gemini client. Check GEMINI_API_KEY. Details: {e}")
        return {"is_relevant_job": False}

    skill_details = "\n".join([f"- {cat}: {', '.join(skills)}" for cat, skills in JOB_SKILL_CATEGORIES.items()])

    # Define the System Prompt
    system_prompt = f"""
    You are an expert SAP Technology recruitment analyst. Your task is to analyze the email subject and body.
    
    RULES FOR CLASSIFICATION:
    1. The email must be a genuine job opportunity or recruitment outreach.
    2. The email must explicitly mention one of these target job titles: {', '.join(TARGET_JOB_TITLES)}.
    3. The email must contain a MINIMUM of {MIN_KEYWORDS_REQUIRED} technical keywords overall from the categories below.
    4. The keywords mentioned must span AT LEAST {MIN_CATEGORIES_REQUIRED} different categories below.
    
    **REQUIRED SKILL CATEGORIES:**
    {skill_details}
    
    If it meets ALL four rules, set "is_relevant_job" to true and extract the details. Otherwise, set it to false.
    Always respond with ONLY a single JSON object that strictly adheres to the schema below.
    """
    
    # Define the Structured Output Schema
    response_schema = {
        "type": "object",
        "properties": {
            "is_relevant_job": {"type": "boolean", "description": "True if the email is a relevant job posting meeting all criteria, false otherwise."},
            "job_title": {"type": "string", "description": "The specific title of the job mentioned (e.g., 'Senior SAP Cloud Architect')."},
            "company": {"type": "string", "description": "The name of the company hiring."},
            "location": {"type": "string", "description": "The city, state, or country, or 'Remote'."},
            "matched_keywords_count": {"type": "integer", "description": f"The total count of keywords matched (should be >= {MIN_KEYWORDS_REQUIRED})."},
            "matched_categories": {"type": "array", "items": {"type": "string"}, "description": "List of categories (e.g., 'Cloud & ALM') that were matched (should be >= {MIN_CATEGORIES_REQUIRED})."},
            "alert_summary": {"type": "string", "description": "A brief, one-sentence summary for the notification."}
        },
        "required": ["is_relevant_job", "job_title", "company", "location"]
    }

    user_content = f"EMAIL SUBJECT: {subject}\n\nEMAIL BODY:\n{body[:4000]}"

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
        print(f"ERROR during AI processing (likely failed JSON parsing): {e}")
        return {"is_relevant_job": False}


# --- 7. IMAP MONITORING LOGIC (Dynamic Date Filter) ---
def fetch_unread_emails():
    """Connects to Gmail via IMAP and fetches unread message bodies RECEIVED within the last N days."""
    
    email_address = settings["IMAP_EMAIL_ADDRESS"]
    password = settings["IMAP_PASSWORD"]
    imap_server = settings["IMAP_SERVER"]
    days_back = settings["DAYS_TO_CHECK"] 

    mail = None
    emails_to_process = []
    
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_address, password)
        mail.select("inbox")
        
        start_date = datetime.date.today() - datetime.timedelta(days=days_back - 1) 
        start_date_imap = start_date.strftime("%d-%b-%Y")
        
        # Search for UNSEEN emails received SINCE the start date
        search_query = f'(UNSEEN SINCE "{start_date_imap}")'
        
        status, messages = mail.search(None, search_query)
        email_ids = messages[0].split()
        
        for e_id in email_ids:
            # Fetch and decode subject/body 
            status, msg_data = mail.fetch(e_id, '(RFC822)')
            if status == 'OK':
                msg = email.message_from_bytes(msg_data[0][1])
                
                subject_tuple = decode_header(msg.get("Subject", "No Subject"))[0]
                subject = subject_tuple[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(subject_tuple[1] if subject_tuple[1] else "utf-8", errors='ignore')
                    
                body = ""
                for part in msg.walk():
                    ctype = part.get_content_type()
                    cdisp = part.get('Content-Disposition', '')
                    if ctype == 'text/plain' and 'attachment' not in cdisp:
                        try:
                            body = part.get_payload(decode=True).decode(errors='ignore')
                        except:
                            body = "Could not decode body content."
                        break
                        
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


# --- 8. MAIN MONITORING LOOP ---

def start_monitoring():
    """The main loop that checks for new emails and triggers AI analysis and Telegram alert."""
    days = settings["DAYS_TO_CHECK"]
    interval_minutes = settings["MONITOR_INTERVAL_MINUTES"]
    interval_seconds = interval_minutes * 60 
    
    print("=" * 50)
    print(f"Starting Highly Filtered SAP Job Monitor...")
    print(f"Filter: Last {days} Day(s). Interval: {interval_minutes} Minute(s).")
    print("Email will be marked as read upon successful Telegram alert.")
    print("=" * 50)
    
    while True:
        # The core monitoring logic (fetch, analyze, alert, mark read) is in the loop
        new_emails = fetch_unread_emails()
        
        if new_emails:
            print(f"\n[FOUND] {len(new_emails)} new unread email(s) in the last {days} day(s). Analyzing...")
            
            for i, mail_data in enumerate(new_emails):
                print(f"--- Processing Email {i+1} ---")
                print(f"Subject: {mail_data['subject'][:80]}...")
                
                # --- CALL AI CLASSIFICATION ---
                ai_result = analyze_email_for_job(mail_data['subject'], mail_data['body'])
                
                if ai_result.get("is_relevant_job"):
                    # --- ALERTING LOGIC ---
                    summary = ai_result.get('alert_summary', 'CRITICAL MATCH')
                    matched_categories = ai_result.get('matched_categories', [])
                    
                    telegram_message = (
                        f"Title: {ai_result.get('job_title', 'N/A')}\n"
                        f"Company: {ai_result.get('company', 'N/A')}\n"
                        f"Location: {ai_result.get('location', 'N/A')}\n"
                        f"Keywords Found: {ai_result.get('matched_keywords_count', 'N/A')}\n"
                        f"Skill Areas: {', '.join(matched_categories)}\n\n"
                        f"Source Subject: {mail_data['subject']}"
                    )
                    
                    # 1. Send the Alert via Telegram
                    alert_sent = send_telegram_alert(telegram_message)
                    
                    # 2. CRITICAL: Mark as Read ONLY if the Telegram alert succeeded
                    if alert_sent:
                        mark_email_as_read(mail_data["message_id"])

                    # 3. Print Local Confirmation
                    print(f"\n[!!! ALERT !!!] CRITICAL MATCH DETECTED! (Alert sent to Telegram)")
                    print(f"   Summary: {summary}")
                    print(f"   Title: {ai_result.get('job_title', 'N/A')}")
                    print("---------------------------------------")
                    
                else:
                    print("Classification: Did not meet the strict job title or multi-skill criteria.")
                
        else:
            print(f"[{time.strftime('%H:%M:%S')}] No new unread emails found. Sleeping for {interval_minutes} minutes...")
            
        time.sleep(interval_seconds) 

# --- 9. MAIN ENTRY POINT (FINAL, ROBUST WRAPPER) ---

if __name__ == '__main__':
    try:
        check_config()
        start_monitoring()
    except EnvironmentError as e:
        # Catches missing critical .env keys (e.g., API key, login credentials)
        error_msg = f"ENVIRONMENT SETUP FAILURE: {e}"
        print(f"\nFATAL ERROR: {error_msg}")
        send_failure_alert(error_msg)
        print("Please fix the missing keys in your .env file.")
    except Exception as e:
        # Catches all other unexpected runtime crashes (network, logic error, etc.)
        error_msg = f"UNEXPECTED SCRIPT TERMINATION:\n{type(e).__name__}: {e}"
        print(f"\nFATAL UNEXPECTED ERROR: {e}")
        send_failure_alert(error_msg)