# astro_packager.py (Twinkle Luxury Theme Engine - Fixed Paths)
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import licensing_core

class AstroPackagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🔱 కోటి సాఫ్ట్‌వేర్ ప్యాకేజర్ & లైసెన్స్ మేనేజర్ v2.0")
        self.root.geometry("700x650")
        self.root.configure(bg="#0b0f19") # Deep Cosmic Midnight Blue

        # --- TWINKLE STYLE CONFIGURATION ---
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # కస్టమ్ కాంబోబాక్స్/ఎంట్రీ స్టైల్స్
        self.style.configure("TCombobox", fieldbackground="#111827", background="#1f2937", foreground="#ffffff")
        
        # 1. メరుస్తున్న హెడర్ బ్యానర్ (Twinkle Effect)
        header_frame = tk.Frame(root, bg="#1e1b4b", bd=2, relief=tk.RIDGE)
        header_frame.pack(fill=tk.X, padx=25, pady=20)
        
        tk.Label(header_frame, text="✨ TWINKLE ASTRO PACKAGER ENGINE ✨", font=("Courier New", 15, "bold"), fg="#38bdf8", bg="#1e1b4b").pack(pady=5)
        tk.Label(header_frame, text="కోటి ఆటోమేషన్ సాఫ్ట్‌వేర్ లైసెన్సింగ్ సిస్టమ్", font=("Segoe UI", 10, "italic"), fg="#f472b6", bg="#1e1b4b").pack(pady=2)

        # 2. ఫైల్ సెలెక్షన్ ప్యానెల్ (Neon Borders Effect)
        file_frame = tk.LabelFrame(root, text=" 📂 సెలెక్ట్ పైథాన్ స్క్రిప్ట్ (.py) ", font=("Segoe UI", 10, "bold"), fg="#38bdf8", bg="#0f172a", bd=2, padx=15, pady=15)
        file_frame.pack(fill=tk.X, padx=25, pady=10)

        self.target_file_var = tk.StringVar()
        file_entry = tk.Entry(file_frame, textvariable=self.target_file_var, width=42, font=("Segoe UI", 10), bg="#1e293b", fg="#f8fafc", insertbackground="white", bd=1, relief=tk.SOLID)
        file_entry.pack(side=tk.LEFT, padx=5, ipady=3)
        
        browse_btn = tk.Button(file_frame, text="Browse File", bg="#38bdf8", fg="#0f172a", font=("Segoe UI", 9, "bold"), activebackground="#0ea5e9", cursor="hand2", bd=0, padx=15, pady=4, command=self.browse_file)
        browse_btn.pack(side=tk.LEFT, padx=5)

        # 3. లైసెన్స్ కాన్ఫిగరేషన్ ప్యానెల్ (Luxury Dark Theme)
        lic_frame = tk.LabelFrame(root, text=" 🔑 లింక్డ్ లైసెన్స్ & సెక్యూరిటీ గేట్ ", font=("Segoe UI", 10, "bold"), fg="#f472b6", bg="#0f172a", bd=2, padx=15, pady=15)
        lic_frame.pack(fill=tk.X, padx=25, pady=10)

        # User ID & Password Rows
        tk.Label(lic_frame, text="👤 User ID:", font=("Segoe UI", 10), fg="#94a3b8", bg="#0f172a").grid(row=0, column=0, sticky="w", pady=8)
        self.user_id_entry = tk.Entry(lic_frame, width=18, font=("Segoe UI", 10), bg="#1e293b", fg="#ffffff", insertbackground="white", bd=1, relief=tk.SOLID)
        self.user_id_entry.grid(row=0, column=1, sticky="w", pady=8, padx=5, ipady=2)
        self.user_id_entry.insert(0, "astro_user")

        tk.Label(lic_frame, text="🔒 Password:", font=("Segoe UI", 10), fg="#94a3b8", bg="#0f172a").grid(row=0, column=2, sticky="w", pady=8, padx=15)
        self.password_entry = tk.Entry(lic_frame, width=18, font=("Segoe UI", 10), bg="#1e293b", fg="#ffffff", insertbackground="white", bd=1, relief=tk.SOLID, show="*")
        self.password_entry.grid(row=0, column=3, sticky="w", pady=8, ipady=2)
        self.password_entry.insert(0, "pass123")

        # Separator Line
        sep = tk.Frame(lic_frame, height=1, bg="#334155")
        sep.grid(row=1, column=0, columnspan=4, sticky="ew", pady=10)

        # Validity Option With Twinkle Accent
        tk.Label(lic_frame, text="⚙️ వాలిడిటీ రకం:", font=("Segoe UI", 10), fg="#94a3b8", bg="#0f172a").grid(row=2, column=0, sticky="w", pady=5)
        self.lifelong_var = tk.BooleanVar()
        self.lifelong_chk = tk.Checkbutton(lic_frame, text="Lifelong Free Activation (జీవితకాలం ఉచితం ✨)", variable=self.lifelong_var, font=("Segoe UI", 10, "bold"), fg="#f59e0b", bg="#0f172a", activebackground="#0f172a", activeforeground="#f59e0b", selectcolor="#1e293b", command=self.toggle_days_entry)
        self.lifelong_chk.grid(row=2, column=1, columnspan=3, sticky="w", pady=5, padx=5)

        tk.Label(lic_frame, text="⏳ గడువు రోజులు (Days):", font=("Segoe UI", 10), fg="#94a3b8", bg="#0f172a").grid(row=3, column=0, sticky="w", pady=8)
        self.days_entry = tk.Entry(lic_frame, width=10, font=("Segoe UI", 10, "bold"), bg="#1e293b", fg="#34d399", insertbackground="white", bd=1, relief=tk.SOLID, justify="center")
        self.days_entry.grid(row=3, column=1, sticky="w", pady=8, padx=5, ipady=2)
        self.days_entry.insert(0, "30")

        # 4. బిల్డ్ బటన్ (Glowing Action Button)
        self.pack_btn = tk.Button(root, text="✨ సాఫ్ట్‌വേర్ ప్యాకేజ్ సిద్ధం చేయి (.EXE) ✨", font=("Segoe UI", 12, "bold"), fg="#0f172a", bg="#34d399", activebackground="#10b981", activeforeground="#ffffff", cursor="hand2", bd=0, width=38, pady=10, command=self.build_software)
        self.pack_btn.pack(pady=25)

        # 5. మోడరన్ స్టేటస్ బార్
        self.status_frame = tk.Frame(root, bg="#1e293b", height=35)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(self.status_frame, text="🟢 సిస్టమ్ సిద్ధంగా ఉంది. మీ ఫైల్‌ను ప్యాకేజ్ చేయవచ్చు...", font=("Segoe UI", 9), fg="#34d399", bg="#1e293b")
        self.status_label.pack(side=tk.LEFT, padx=15, pady=6)

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
        if filename:
            self.target_file_var.set(filename)
            self.status_label.config(text=f"📂 ఫైల్ లోడ్ అయింది: {os.path.basename(filename)}", fg="#38bdf8")

    def toggle_days_entry(self):
        if self.lifelong_var.get():
            self.days_entry.config(state=tk.DISABLED)
            self.status_label.config(text="✨ లైఫ్‌లాంగ్ ఫ్రీ ఆప్షన్ యాక్టివేట్ చేయబడింది!", fg="#f59e0b")
        else:
            self.days_entry.config(state=tk.NORMAL)
            self.status_label.config(text="⏳ పరిమిత రోజుల వాలిడిటీ మోడ్ యాక్టివ్.", fg="#34d399")

    def build_software(self):
        target_py = self.target_file_var.get()
        if not target_py or not os.path.exists(target_py):
            messagebox.showerror("Error", "దయచేసి సాఫ్ట్‌വേర్‌గా మార్చాల్సిన సరైన పైథాన్ ఫైల్‌ను ఎంచుకోండి!")
            return

        user_id = self.user_id_entry.get().strip()
        password = self.password_entry.get().strip()
        is_lifelong = self.lifelong_var.get()
        
        try:
            days = int(self.days_entry.get() if not is_lifelong else 0)
        except ValueError:
            messagebox.showerror("Error", "రోజుల సంఖ్య ఖచ్చితమైన అంకె అయి ఉండాలి!")
            return

        self.status_label.config(text="⚙️ ఎన్‌క్రిప్టెడ్ లైసెన్స్ ఫైల్ జనరేట్ అవుతోంది...", fg="#f59e0b")
        self.root.update()

        # 1. కోర్ మాడ్యూల్ రన్ చేసి లైసెన్స్ లాక్ చేయడం
        lic_data = licensing_core.create_default_license(user_id, password, days, lifelong=is_lifelong)

        # 2. సురక్షితమైన బిల్డ్ కోడ్ ఇంజెక్షన్
        self.status_label.config(text="📦 PyInstaller ద్వారా సాఫ్ట్‌വേర్ ప్యాకేజ్ అవుతోంది... (దయచేసి కొన్ని సెకన్లు ఆగండి)", fg="#f472b6")
        self.root.update()

        target_dir = os.path.dirname(target_py)
        base_name = os.path.basename(target_py).replace(".py", "")
        secured_py_path = os.path.join(target_dir, f"secured_{base_name}.py")
        
        with open(target_py, "r", encoding="utf-8") as orig_f:
            orig_code = orig_f.read()

        # ఒరిజినల్ స్క్రిప్ట్‌కు సెంట్రల్ లైసెన్స్ సెక్యూరిటీ గేట్ యాడ్ చేయడం
        secured_code = f"""
import licensing_core
if not licensing_core.validate_license():
    import sys
    sys.exit()

{orig_code}
        """
        with open(secured_py_path, "w", encoding="utf-8") as sec_f:
            sec_f.write(secured_code)

        # --- ఇక్కడే మార్పు చేశాను (PyInstaller కి లైసెన్స్ పాత్ ఇక్కడ యాడ్ అయింది) ---
        license_path = r"C:\backup\US_word_files\Interview_learnings\python_scripts\Projects\License"
        pyinstaller_cmd = f"pyinstaller --onefile --console --paths=\"{license_path}\" --clean \"{secured_py_path}\""
        
        exit_code = os.system(pyinstaller_cmd)

        # టెంపరరీ క్లీనప్
        if os.path.exists(secured_py_path):
            os.remove(secured_py_path)

        if exit_code == 0:
            self.status_label.config(text="✅ ప్యాకేజింగ్ విజయవంతమైంది! 'dist' ఫోల్డర్ లో సాఫ్ట్‌വേర్ రెడీగా ఉంది.", fg="#34d399")
            messagebox.showinfo("Success!", f"కోటి గారు! మీ సాఫ్ట్‌వేర్ సక్సెస్‌ఫుల్‌గా 'Twinkle' ఆర్కిటెక్చర్‌తో లాక్ చేయబడింది.\n\n"
                                             f"వినియోగదారునికి సాఫ్ట్‌വേర్ ఇచ్చేటప్పుడు '.exe' ఫైల్‌తో పాటు పక్కనే 'license.json' ఫైల్‌ను కూడా ఇవ్వండి.")
        else:
            self.status_label.config(text="❌ ప్యాకేజింగ్ విఫలమైంది. PyInstaller ఎర్రర్స్ చెక్ చేయండి.", fg="#ef4444")

if __name__ == "__main__":
    root = tk.Tk()
    app = AstroPackagerApp(root)
    root.mainloop()