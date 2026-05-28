import threading
import tkinter as tk
from tkinter import ttk
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

# IDs based on your specific logs
MIC_ID = 5  
SYS_ID = 10 
THRESHOLD = 150 

SYSTEM_PROMPT = "You are a SAP Project manager. Provide architectural and project guidance."
groq_client = Groq(api_key=GROQ_API_KEY)

class LevelUpCopilot:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SAP CO-PILOT - FINAL STABILITY")
        self.root.geometry("700x750+300+50")
        self.root.configure(bg="#111")
        self.root.attributes("-topmost", True)

        self.audio_queue = queue.Queue(maxsize=200)
        self.is_running = True
        self.mode = 0 
        self.fragments = []
        self.last_heard = time.time()

        self.build_ui()
        self.p = pyaudio.PyAudio()
        
        # Start Threads
        threading.Thread(target=self.audio_engine, daemon=True).start()
        threading.Thread(target=self.cloud_engine, daemon=True).start()
        threading.Thread(target=self.context_engine, daemon=True).start()
        
        self.root.mainloop()

    def build_ui(self):
        header = tk.Frame(self.root, bg="#222")
        header.pack(fill="x")
        self.mode_btn = tk.Button(header, text="MODE: SYSTEM", bg="#333", fg="cyan", command=self.toggle_mode)
        self.mode_btn.pack(side="left", padx=10, pady=10)
        self.text_display = tk.Text(self.root, bg="#000", fg="#00FFCC", font=("Arial", 12), wrap=tk.WORD, bd=0)
        self.text_display.pack(expand=True, fill="both", padx=20, pady=10)
        self.debug_console = tk.Text(self.root, bg="#111", fg="#666", font=("Consolas", 8), height=10)
        self.debug_console.pack(fill="x")

    def log(self, msg):
        ts = time.strftime('%H:%M:%S')
        self.debug_console.insert(tk.END, f"[{ts}] {msg}\n")
        self.debug_console.see(tk.END)

    def toggle_mode(self):
        self.mode = 1 if self.mode == 0 else 0
        self.mode_btn.config(text="MODE: MIC" if self.mode == 1 else "MODE: SYSTEM", fg="orange" if self.mode == 1 else "cyan")

    def audio_engine(self):
        def capture(device_id, target_mode, label):
            try:
                info = self.p.get_device_info_by_index(device_id)
                is_loopback = "loopback" in info["name"].lower()
                
                # Open stream with loopback support if needed
                stream = self.p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=int(info["defaultSampleRate"]),
                    input=True,
                    input_device_index=device_id,
                    frames_per_buffer=1024
                )
                
                self.log(f"SUCCESS: {label} (ID {device_id}) is active.")
                
                while self.is_running:
                    data = stream.read(1024, exception_on_overflow=False)
                    if self.mode == target_mode:
                        np_data = np.frombuffer(data, dtype=np.int16)
                        if np.abs(np_data).mean() > THRESHOLD:
                            # Resample logic (from 48k or 44.1k down to 16k)
                            step = int(info["defaultSampleRate"] / 16000)
                            resampled = np_data[::step].tobytes()
                            if not self.audio_queue.full():
                                self.audio_queue.put(resampled)
            except Exception as e:
                self.log(f"SKIPPING {label}: {e}")

        # Try to start both, but the script won't stop if one fails
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
                        if result.is_final: self.trigger_ai()

                self.dg_conn.on(LiveTranscriptionEvents.Transcript, on_msg)
                self.dg_conn.start(LiveOptions(model="nova-2", language="en-IN", encoding="linear16", channels=1, sample_rate=16000, endpointing=500))

                while self.is_running:
                    try:
                        chunk = self.audio_queue.get(timeout=0.5)
                        self.dg_conn.send(chunk)
                    except queue.Empty:
                        if self.dg_conn: self.dg_conn.send(b'\x00' * 512)
            except Exception as e:
                self.log(f"Deepgram Error: {e}")
                time.sleep(2)

    def context_engine(self):
        while self.is_running:
            time.sleep(0.1)
            if self.fragments and (time.time() - self.last_heard > 1.8):
                self.trigger_ai()

    def trigger_ai(self):
        if not self.fragments: return
        query = " ".join(self.fragments).strip()
        self.fragments = []
        threading.Thread(target=self.ask_ai, args=(query,), daemon=True).start()

    def ask_ai(self, text):
        try:
            res = groq_client.chat.completions.create(
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": text}],
                model="llama-3.1-8b-instant"
            )
            ans = res.choices[0].message.content
            self.root.after(0, lambda: self.display(text, ans))
        except Exception as e: self.log(f"AI Error: {e}")

    def display(self, q, a):
        self.text_display.delete("1.0", tk.END)
        self.text_display.insert(tk.END, f"Q: {q}\n\n{a}")

if __name__ == "__main__":
    LevelUpCopilot()