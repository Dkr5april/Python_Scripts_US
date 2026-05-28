import threading
import tkinter as tk
from tkinter import ttk # Added for the slider
import pyaudiowpatch as pyaudio
import numpy as np
import queue
import time
import re
from groq import Groq
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

# ---------------- CONFIGURATION ---------------- #
DEEPGRAM_API_KEY = "99a39ac2f2a40f15ad234dbabac8c5a7c4c7c997"
GROQ_API_KEY = "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"
MIC_ID = 5  
SYS_ID = 10 
THRESHOLD = 150 

SYSTEM_PROMPT = """You are a SAP Project manager, so context should be limited to that only:
Level 1: Short bullet points only.
Level 2: Expand bullets.
Level 3: Deep technical architecture.
Level 4: Real production scenario.
Level 5: Advanced edge cases/optimization.
"""

groq_client = Groq(api_key=GROQ_API_KEY)

class LevelUpCopilot:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SAP Project Management Level up")
        self.root.geometry("700x650+300+50")
        self.root.configure(bg="#111")
        self.root.attributes("-topmost", True)
        
        # --- GLASS EFFECT (Initial Transparency) ---
        self.root.attributes("-alpha", 0.85)

        self.mode = 0 
        self.audio_queue = queue.Queue(maxsize=150)
        self.is_running = True
        self.dg_conn = None 
        self.fragments = []
        self.last_heard = time.time()
        self.full_response = {}
        self.current_level = 1

        self.build_ui()
        
        threading.Thread(target=self.audio_engine, daemon=True).start()
        threading.Thread(target=self.cloud_engine, daemon=True).start()
        threading.Thread(target=self.context_engine, daemon=True).start()
        
        self.root.mainloop()

    def update_transparency(self, value):
        self.root.attributes("-alpha", float(value))

    def build_ui(self):
        header = tk.Frame(self.root, bg="#222")
        header.pack(fill="x")

        self.mode_btn = tk.Button(header, text="MODE: SYSTEM", bg="#333", fg="cyan", 
                                  command=self.toggle_mode, font=("Arial", 10, "bold"))
        self.mode_btn.pack(side="left", padx=10, pady=10)

        self.next_btn = tk.Button(header, text="Next Level ➜", bg="#444", fg="white",
                                  command=self.next_level, font=("Arial", 10, "bold"))
        self.next_btn.pack(side="left", padx=10)

        # --- GLASS SLIDER ---
        tk.Label(header, text="Glass:", bg="#222", fg="white", font=("Arial", 8)).pack(side="left", padx=(5,0))
        self.alpha_slider = ttk.Scale(header, from_=0.3, to=1.0, value=0.85, orient="horizontal", 
                                      command=self.update_transparency, length=80)
        self.alpha_slider.pack(side="left", padx=5)

        self.vol_canvas = tk.Canvas(header, width=100, height=15, bg="#000", highlightthickness=0)
        self.vol_canvas.pack(side="right", padx=15)
        self.vol_bar = self.vol_canvas.create_rectangle(0, 0, 0, 15, fill="#00FF00")

        # --- RESUME / CONTEXT INPUT BOX ---
        ctx_frame = tk.Frame(self.root, bg="#111")
        ctx_frame.pack(fill="x", padx=20, pady=5)
        tk.Label(ctx_frame, text="RESUME / PROJECT CONTEXT:", bg="#111", fg="#777", font=("Arial", 8, "bold")).pack(side="top", anchor="w")
        self.context_box = tk.Text(self.root, height=3, bg="#1a1a1a", fg="#aaa", font=("Arial", 9), insertbackground="white", bd=0)
        self.context_box.pack(fill="x", padx=20, pady=(0,10))
        self.context_box.insert("1.0", "Paste context here...")

        self.text_display = tk.Text(self.root, bg="#000", fg="#00FFCC", font=("Segoe UI", 12), 
                                    wrap=tk.WORD, bd=0, padx=20, pady=20)
        self.text_display.pack(expand=True, fill="both")
        
        self.debug_console = tk.Text(self.root, bg="#1a1a1a", fg="#888", font=("Consolas", 8), height=5)
        self.debug_console.pack(fill="x")

    def log(self, msg):
        self.debug_console.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.debug_console.see(tk.END)

    def toggle_mode(self):
        self.mode = 1 if self.mode == 0 else 0
        self.mode_btn.config(text="MODE: MIC" if self.mode == 1 else "MODE: SYSTEM",
                             fg="orange" if self.mode == 1 else "cyan")

    def audio_engine(self):
        p = pyaudio.PyAudio()
        def capture(device_id, target_mode, name):
            try:
                stream = p.open(format=pyaudio.paInt16, channels=2, rate=48000, input=True, input_device_index=device_id)
                while self.is_running:
                    raw = stream.read(1024, exception_on_overflow=False)
                    if self.mode == target_mode:
                        np_data = np.frombuffer(raw, dtype=np.int16)
                        vol = np.abs(np_data).mean()
                        self.root.after(0, lambda w=min(int(vol/10), 100): self.vol_canvas.coords(self.vol_bar, 0, 0, w, 15))
                        
                        if vol > THRESHOLD:
                            processed = np_data[::2][::3]
                            if not self.audio_queue.full(): self.audio_queue.put(processed.tobytes())
            except Exception as e: self.log(f"Audio Error: {e}")

        threading.Thread(target=capture, args=(SYS_ID, 0, "SYSTEM"), daemon=True).start()
        threading.Thread(target=capture, args=(MIC_ID, 1, "MIC"), daemon=True).start()

    def cloud_engine(self):
        while self.is_running:
            try:
                client = DeepgramClient(DEEPGRAM_API_KEY)
                self.dg_conn = client.listen.live.v("1")
                def on_msg(s, result, **kwargs):
                    txt = result.channel.alternatives[0].transcript
                    if txt:
                        self.fragments.append(txt)
                        self.last_heard = time.time()
                self.dg_conn.on(LiveTranscriptionEvents.Transcript, on_msg)
                self.dg_conn.start(LiveOptions(model="nova-2", language="en-IN", smart_format=True, encoding="linear16", channels=1, sample_rate=16000))
                while self.is_running:
                    try:
                        chunk = self.audio_queue.get(timeout=1.0)
                        self.dg_conn.send(chunk)
                    except queue.Empty:
                        if self.dg_conn: self.dg_conn.send(bytes(2048))
            except Exception as e: 
                self.log(f"Cloud Engine Error: {e}")
                time.sleep(2)

    def context_engine(self):
        while self.is_running:
            time.sleep(0.1) # Check faster
            # REDUCED DELAY: Changed from 3.0 to 1.5 for faster response
            if self.fragments and (time.time() - self.last_heard > 1.5):
                full_q = " ".join(self.fragments).strip()
                self.fragments = []
                threading.Thread(target=self.ask_ai, args=(full_q,), daemon=True).start()

    def ask_ai(self, text):
        try:
            # COMBINING SYSTEM PROMPT WITH USER CONTEXT BOX
            user_context = self.context_box.get("1.0", tk.END).strip()
            dynamic_prompt = f"{SYSTEM_PROMPT}\n\nAdditional Context/Resume: {user_context}"
            
            self.log("Asking Groq...")
            start_time = time.time()
            res = groq_client.chat.completions.create(
                messages=[{"role": "system", "content": dynamic_prompt}, {"role": "user", "content": text}],
                model="llama-3.1-8b-instant"
            )
            latency = time.time() - start_time
            self.log(f"AI Response in {latency:.2f}s")
            content = res.choices[0].message.content
            parts = re.split(r'[Ll]evel\s*', content)
            structured = {}
            for p in parts:
                if ":" in p:
                    lvl = p.split(":")[0].strip()
                    body = p.split(":", 1)[1].strip()
                    structured[lvl] = body
            self.full_response = structured
            self.current_level = 1
            display_answer = structured.get("1", "No Level 1 found.")
            self.root.after(0, lambda: self.display_fresh(text, display_answer, latency))
        except Exception as e: self.log(f"AI Error: {e}")

    def display_fresh(self, q, a, lat):
        self.text_display.delete("1.0", tk.END)
        self.text_display.insert(tk.END, f"Q: {q}\n", "q_style")
        self.text_display.insert(tk.END, f"[{lat:.2f}s latency]\n", "lat_style")
        self.text_display.insert(tk.END, f"\n--- LEVEL 1 ---\n{a}\n", "l1_style")
        self.text_display.tag_config("q_style", foreground="orange", font=("Arial", 11, "bold"))
        self.text_display.tag_config("lat_style", foreground="#555", font=("Arial", 8))
        self.text_display.tag_config("l1_style", foreground="#00FFCC")

    def next_level(self):
        self.current_level += 1
        lvl_str = str(self.current_level)
        if lvl_str in self.full_response:
            self.text_display.insert(tk.END, f"\n--- LEVEL {lvl_str} ---\n", "lvl_head")
            self.text_display.insert(tk.END, f"{self.full_response[lvl_str]}\n")
            self.text_display.tag_config("lvl_head", foreground="yellow", font=("Arial", 10, "bold"))
            self.text_display.see(tk.END)
        else:
            self.log(f"Level {lvl_str} not available.")

if __name__ == "__main__":
    LevelUpCopilot()