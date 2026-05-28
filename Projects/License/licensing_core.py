import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from tkinter import messagebox, simpledialog
import tkinter as tk
from cryptography.fernet import Fernet

LICENSE_FILE = r"C:\backup\US_word_files\Interview_learnings\python_scripts\Projects\License\license.json"
# విండోస్ లోని రహస్య AppData ఫోల్డర్ లో యాంకర్ ఫైల్ పాత్
HIDDEN_ANCHOR_DIR = os.path.join(os.environ.get('APPDATA', 'C:\\'), "AstroCore")
HIDDEN_ANCHOR_FILE = os.path.join(HIDDEN_ANCHOR_DIR, "system_anchor.dat")

WHATSAPP_NUMBER = "+91 9886653054"  # మీ నెంబర్ ఇక్కడ మార్చుకోండి
EMAIL_ID = "koteswara.davuluri@gmail.com"

# ఎన్‌క్రిప్షన్ కోసం ఒక సురక్షితమైన మాస్టర్ కీ (దీన్ని ఎవరికీ చెప్పకండి)
import base64
SECRET_KEY = base64.urlsafe_b64encode(b"KoteswaraRaoDavuluriAstro1979Key") 
cipher = Fernet(SECRET_KEY)

def get_hardware_uuid():
    """వినియోగదారుని కంప్యూటర్ యొక్క యూనిక్ మదర్‌బోర్డ్/సిస్టమ్ UUID ని సేకరిస్తుంది"""
    try:
        if sys.platform == "win32":
            cmd = "wmic csproduct get uuid"
            uuid_out = subprocess.check_output(cmd, shell=True).decode().split()
            return uuid_out[1] if len(uuid_out) > 1 else "WIN-GENERIC-UUID"
        else:
            return "NON-WINDOWS-DEVICE"
    except Exception:
        return "GENERIC-HARDWARE-ID"

def create_default_license(user_id, password, validity_days, lifelong=False):
    """అడ్మిన్ డ్యాష్‌బోర్డ్ నుండి ఎన్‌క్రిప్టెడ్ లైసెన్స్ ఫైల్‌ను సృష్టిస్తుంది"""
    issued_date = datetime.now()
    if lifelong:
        expiry_date = "LIFELONG"
    else:
        expiry_date = (issued_date + timedelta(days=validity_days)).strftime("%Y-%m-%d %H:%M:%S")
        
    # హార్డ్‌వేర్ ఐడిని కూడా లైసెన్స్ లోపల లాక్ చేస్తున్నాం
    lic_data = {
        "user_id": user_id,
        "password": password,
        "issued_on": issued_date.strftime("%Y-%m-%d %H:%M:%S"),
        "expiry_on": expiry_date,
        "lifelong": lifelong,
        "hw_id": get_hardware_uuid()
    }
    
    # డేటాను ఎన్‌క్రిప్ట్ చేసి సేవ్ చేయడం
    encrypted_data = cipher.encrypt(json.dumps(lic_data).encode())
    with open(LICENSE_FILE, "wb") as f:
        f.write(encrypted_data)
        
    # హిడెన్ యాంకర్ ఫోల్డర్ క్రియేట్ చేసి ఫస్ట్ రన్ డేటాను బ్యాకప్ ఉంచడం
    if not os.path.exists(HIDDEN_ANCHOR_DIR):
        os.makedirs(HIDDEN_ANCHOR_DIR)
    
    anchor_data = {"first_run": lic_data["issued_on"], "hw_id": lic_data["hw_id"]}
    enc_anchor = cipher.encrypt(json.dumps(anchor_data).encode())
    with open(HIDDEN_ANCHOR_FILE, "wb") as f:
        f.write(enc_anchor)
        
    return lic_data

def validate_license():
    """సాఫ్ట్‌వేర్ రన్ అయ్యేటప్పుడు రిజిస్ట్రీ లేదా ఫైల్ లెవెల్ హ్యాకింగ్‌ను అడ్డుకునే మాస్టర్ వెరిఫికేషన్ గేట్"""
    current_hw_id = get_hardware_uuid()
    
    # 1. లోకల్ లైసెన్స్ ఫైల్ చెకింగ్
    if not os.path.exists(LICENSE_FILE):
        # ఒకవేళ యూజర్ హ్యాక్ చేయడానికి లైసెన్స్ ఫైల్ డిలీట్ చేస్తే, హిడెన్ యాంకర్ ద్వారా పట్టుకుంటాం
        if os.path.exists(HIDDEN_ANCHOR_FILE):
            messagebox.showerror("సెక్యూరిటీ అలర్ట్", f"లైసెన్స్ ఫైల్ టాంపరింగ్ లేదా డిలీట్ చేయబడింది!\n\nసాఫ్ట్‌వేర్ రీ-యాక్టివేషన్ కోసం సంప్రదించండి:\n📧 {EMAIL_ID}\n💬 WhatsApp: {WHATSAPP_NUMBER}")
        else:
            messagebox.showerror("లైసెన్స్ లోపం", f"లైసెన్స్ ఫైల్ లభించలేదు!\n\nసంప్రదించండి:\n📧 {EMAIL_ID}\n💬 WhatsApp: {WHATSAPP_NUMBER}")
        return False

    try:
        with open(LICENSE_FILE, "rb") as f:
            enc_content = f.read()
        lic_data = json.loads(cipher.decrypt(enc_content).decode())
    except Exception:
        messagebox.showerror("సెక్యూరిటీ అలర్ట్", "లైసెన్స్ ఫైల్ డేటాను మార్చడానికి ప్రయత్నించారు (Data Tampering)! సాఫ్ట్‌వేర్ లాక్ చేయబడింది.")
        return False

    # 2. హార్డ్‌వేర్ ఐడి వెరిఫికేషన్ (యాంటీ-పైరసీ - ఒకరి ఫైల్ ఇంకొకరికి పనిచేయదు)
    if lic_data["hw_id"] != current_hw_id:
        messagebox.showerror("లైసెన్స్ లోపం", "ఈ లైసెన్స్ వేరే కంప్యూటర్ కు చెందినది! పైరసీ అనుమతించబడదు.")
        return False

    # 3. యూజర్ లాగిన్ క్రెడెన్షియల్స్ వెరిఫికేషన్
    root = tk.Tk()
    root.withdraw()
    
    input_user = simpledialog.askstring("లాగిన్", "User ID ఎంటర్ చేయండి:", parent=root)
    input_pass = simpledialog.askstring("లాగిన్", "Password ఎంటర్ చేయండి:", show='*', parent=root)

    if input_user != lic_data["user_id"] or input_pass != lic_data["password"]:
        messagebox.showerror("లాగిన్ ఫెయిల్", "తప్పుడు User ID లేదా Password!")
        return False

    # 4. వాలిడిటీ/ఎక్స్‌పైరీ మరియు హిడెన్ యాంకర్ క్రాస్ వెరిఫికేషన్
    if lic_data["lifelong"]:
        return True

    # సిస్టమ్ హిడెన్ యాంకర్ లోడ్ చేయడం
    if os.path.exists(HIDDEN_ANCHOR_FILE):
        try:
            with open(HIDDEN_ANCHOR_FILE, "rb") as f:
                enc_anc = f.read()
            anchor_data = json.loads(cipher.decrypt(enc_anc).decode())
            # ఒకవేళ యూజర్ కంప్యూటర్ డేట్ వెనక్కి మార్చినా (Backdating Hack), ఈ ఫస్ట్ రన్ డేట్ పట్టుకుంటుంది
            first_run_dt = datetime.strptime(anchor_data["first_run"], "%Y-%m-%d %H:%M:%S")
            if datetime.now() < first_run_dt:
                messagebox.showerror("టైమ్ టాంపరింగ్", "మీరు సిస్టమ్ డేట్ మార్చడానికి ప్రయత్నించారు! సాఫ్ట్‌వేర్ ఓపెన్ కాదు.")
                return False
        except Exception:
            pass

    expiry_dt = datetime.strptime(lic_data["expiry_on"], "%Y-%m-%d %H:%M:%S")
    if datetime.now() > expiry_dt:
        messagebox.showerror("లైసెన్స్ గడువు ముగిసింది", 
                             f"మీ సాఫ్ట్‌వేర్ వాలిడిటీ ముగిసింది!\n\nలైసెన్స్ పొడిగించుకోవడానికి సంప్రదించండి:\n"
                             f"💬 WhatsApp: {WHATSAPP_NUMBER}\n"
                             f"📧 Email: {EMAIL_ID}")
        return False

    remaining_days = (expiry_dt - datetime.now()).days
    messagebox.showinfo("లైసెన్స్ యాక్టివ్", f"లాగిన్ విజయవంతమైంది!\nఇంకా {remaining_days} రోజుల వాలిడిటీ మిగిలి ఉంది.")
    return True