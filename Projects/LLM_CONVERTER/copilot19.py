import threading
import tkinter as tk
import pyaudiowpatch as pyaudio
import numpy as np
import queue
import time
from groq import Groq
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

# ---------------- CONFIGURATION ---------------- #
DEEPGRAM_API_KEY = "99a39ac2f2a40f15ad234dbabac8c5a7c4c7c997"
GROQ_API_KEY = "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"
RESUME_CONTEXT = "SAP Architect: 19 years exp, HANA expert."
groq_client = Groq(api_key=GROQ_API_KEY)

class MicHunterCopilot:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.geometry("650x550+350+50")
        self.root.configure(bg="#111")

        self.mode = 0 
        self.audio_queue = queue.Queue(maxsize=100)
        self.is_running = True
        self.dg_conn = None 
        self.fragments = []
        self.last_heard = time.time()
        
        # --- UI ELEMENTS ---
        self.header = tk.Frame(self.root, bg="#222", height=50)
        self.header.pack(fill="x")
        
        self.mode_btn = tk.Button(self.header, text="MODE: SYSTEM", bg="#333", fg="cyan", 
                                  command=self.toggle_mode, font=("Arial", 10, "bold"), padx=10)
        self.mode_btn.pack(side="left", padx=10, pady=10)
        
        self.meter_label = tk.Label(self.header, text="LEVEL:", fg="white", bg="#222", font=("Arial", 8))
        self.meter_label.pack(side="left", padx=(20, 5))
        self.vol_canvas = tk.Canvas(self.header, width=100, height=15, bg="#000", highlightthickness=0)
        self.vol_canvas.pack(side="left")
        self.vol_bar = self.vol_canvas.create_rectangle(0, 0, 0, 15, fill="#00FF00")

        self.status_label = tk.Label(self.header, text="PIPE: IDLE", fg="yellow", bg="#222", font=("Arial", 8, "bold"))
        self.status_label.pack(side="right", padx=15)

        self.text_display = tk.Text(self.root, bg="#000", fg="#00FFCC", font=("Segoe UI", 12), wrap=tk.WORD, bd=0, padx=20, pady=10)
        self.text_display.pack(expand=True, fill="both")

        self.debug_console = tk.Text(self.root, bg="#1a1a1a", fg="#888", font=("Consolas", 8), height=6, bd=0, padx=10)
        self.debug_console.pack(fill="x")

        threading.Thread(target=self.audio_engine, daemon=True).start()
        threading.Thread(target=self.connection_engine, daemon=True).start()
        threading.Thread(target=self.context_waiter, daemon=True).start()
        
        self.root.mainloop()

    def log(self, msg):
        self.debug_console.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.debug_console.see(tk.END)

    def toggle_mode(self):
        self.mode = 1 if self.mode == 0 else 0
        txt = "MODE: MIC (You)" if self.mode == 1 else "MODE: SYSTEM (Interviewer)"
        color = "orange" if self.mode == 1 else "cyan"
        self.mode_btn.config(text=txt, fg=color)
        self.log(f"SWITCHED TO {txt}")
        with self.audio_queue.mutex: self.audio_queue.queue.clear()

    def audio_engine(self):
        p = pyaudio.PyAudio()
        
        def mic_worker():
            """Specialized worker for Physical Mic (ID 5)"""
            try:
                # Attempting to open Mic with 1 channel first (common for external mics)
                # If your mic is stereo, PyAudio will fail here and go to the 'except'
                stream = p.open(format=pyaudio.paInt16, channels=1, rate=48000, input=True, input_device_index=5)
                self.log("Mic (ID 5) started in MONO mode.")
            except:
                try:
                    stream = p.open(format=pyaudio.paInt16, channels=2, rate=48000, input=True, input_device_index=5)
                    self.log("Mic (ID 5) started in STEREO mode.")
                except Exception as e:
                    self.log(f"CRITICAL: Mic (ID 5) failed: {e}")
                    return

            while self.is_running:
                try:
                    raw = stream.read(1024, exception_on_overflow=False)
                    if self.mode == 1:
                        np_data = np.frombuffer(raw, dtype=np.int16)
                        vol = np.abs(np_data).mean()
                        self.root.after(0, lambda w=min(int(vol/5), 100): self.vol_canvas.coords(self.vol_bar, 0, 0, w, 15))
                        
                        # Downsample for Deepgram (16kHz)
                        processed = np_data[::3] if stream._channels == 1 else np_data[::2][::3]
                        if not self.audio_queue.full(): self.audio_queue.put(processed.tobytes())
                except: pass

        def sys_worker():
            """Worker for System Audio (ID 10)"""
            try:
                stream = p.open(format=pyaudio.paInt16, channels=2, rate=48000, input=True, input_device_index=10)
                self.log("System Audio (ID 10) started.")
                while self.is_running:
                    raw = stream.read(1024, exception_on_overflow=False)
                    if self.mode == 0:
                        np_data = np.frombuffer(raw, dtype=np.int16)
                        vol = np.abs(np_data).mean()
                        self.root.after(0, lambda w=min(int(vol/5), 100): self.vol_canvas.coords(self.vol_bar, 0, 0, w, 15))
                        processed = np_data[::2][::3]
                        if not self.audio_queue.full(): self.audio_queue.put(processed.tobytes())
            except Exception as e: self.log(f"System Error: {e}")

        threading.Thread(target=mic_worker, daemon=True).start()
        threading.Thread(target=sys_worker, daemon=True).start()

    def connection_engine(self):
        while self.is_running:
            try:
                client = DeepgramClient(DEEPGRAM_API_KEY)
                self.dg_conn = client.listen.live.v("1")
                def on_msg(s, result, **kwargs):
                    txt = result.channel.alternatives[0].transcript
                    if txt:
                        self.fragments.append(txt)
                        self.last_heard = time.time()
                        self.log(f"Cloud heard: {txt[:30]}...")
                self.dg_conn.on(LiveTranscriptionEvents.Transcript, on_msg)
                self.dg_conn.start(LiveOptions(model="nova-2", encoding="linear16", channels=1, sample_rate=16000))
                self.root.after(0, lambda: self.status_label.config(text="PIPE: LIVE", fg="#00FF00"))
                while self.is_running:
                    try:
                        chunk = self.audio_queue.get(timeout=0.5)
                        self.dg_conn.send(chunk)
                    except queue.Empty:
                        if self.dg_conn: self.dg_conn.send(bytes(2048))
            except:
                self.dg_conn = None
                time.sleep(2)

    def context_waiter(self):
        while self.is_running:
            time.sleep(0.4)
            if self.fragments and (time.time() - self.last_heard > 1.6):
                full_text = " ".join(self.fragments).strip()
                self.fragments = []
                threading.Thread(target=self.ask_ai, args=(full_text,), daemon=True).start()

    def ask_ai(self, text):
        try:
            res = groq_client.chat.completions.create(messages=[{"role": "user", "content": f"SAP Architect: {text}. 3 bullets."}], model="llama-3.1-8b-instant")
            ans = res.choices[0].message.content
            self.root.after(0, lambda: self.update_ui(text, ans))
        except: pass

    def update_ui(self, q, a):
        self.text_display.insert(tk.END, f"\nQ: {q}\n", "q_style")
        self.text_display.insert(tk.END, f"{a}\n", "a_style")
        self.text_display.tag_config("q_style", foreground="orange", font=("Arial", 10, "bold"))
        self.text_display.tag_config("a_style", foreground="#00FFCC")
        self.text_display.see(tk.END)

if __name__ == "__main__":
    MicHunterCopilot()