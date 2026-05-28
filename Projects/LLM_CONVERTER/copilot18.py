import threading
import tkinter as tk
from tkinter import scrolledtext
import pyaudiowpatch as pyaudio
import numpy as np
import queue
import time
import os
from groq import Groq
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

# ---------------- CONFIGURATION ---------------- #
DEEPGRAM_API_KEY = "99a39ac2f2a40f15ad234dbabac8c5a7c4c7c997"
GROQ_API_KEY = "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"
DEFAULT_CONTEXT = "SAP Architect: 19 years exp, HANA, S/4HANA, BTP, Basis."

# Default Location Metadata (Stored)
LAT, LON = 16.1176, 80.9314 

groq_client = Groq(api_key=GROQ_API_KEY)

class StableCopilot:
    def __init__(self):
        self.active_context = DEFAULT_CONTEXT 
        self.conversation_history = []
        self.audio_queue = queue.Queue(maxsize=5000)
        self.is_running = True
        self.current_source = "SYSTEM"
        
        self.sentence_buffer = []
        self.last_speech_time = time.time()
        self.mic_threshold = 150   
        self.scroll_speed = 0.0006 

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.geometry("700x550+350+50")
        self.root.configure(bg="#0A0A0A")

        # Header
        self.header = tk.Frame(self.root, bg="#1A1A1A", height=35)
        self.header.pack(fill="x")
        self.status_label = tk.Label(self.header, text="CONNECTION STABLE", fg="cyan", bg="#1A1A1A", font=("Arial", 9, "bold"))
        self.status_label.pack(side="left", padx=15)
        self.vol_label = tk.Label(self.header, text="VOL: 0", fg="#444", bg="#1A1A1A", font=("Arial", 8))
        self.vol_label.pack(side="right", padx=15)

        # Text Area
        self.text_area = tk.Text(self.root, bg="#0A0A0A", fg="#FFFFFF", font=("Segoe UI", 16, "bold"), 
                                wrap=tk.WORD, bd=0, padx=30, pady=30, highlightthickness=0)
        self.text_area.pack(expand=True, fill="both")
        self.text_area.config(state=tk.DISABLED)

        self.header.bind("<Button-1>", self.start_move)
        self.header.bind("<B1-Motion>", self.do_move)

        self.auto_scroll_loop()
        threading.Thread(target=self.dual_hardware_engine, daemon=True).start()
        threading.Thread(target=self.deepgram_engine, daemon=True).start()
        threading.Thread(target=self.buffer_monitor_loop, daemon=True).start()
        
        self.root.mainloop()

    def buffer_monitor_loop(self):
        while self.is_running:
            time.sleep(0.4)
            if self.sentence_buffer and (time.time() - self.last_speech_time > 1.3):
                full_text = " ".join(self.sentence_buffer).strip()
                if len(full_text.split()) > 3:
                    threading.Thread(target=self.get_ai_response, args=(full_text,), daemon=True).start()
                self.sentence_buffer = []

    def dual_hardware_engine(self):
        p = pyaudio.PyAudio()
        try:
            # Re-using the logic that worked perfectly before
            sys_s = p.open(format=pyaudio.paInt16, channels=2, rate=48000, input=True, input_device_index=10)
            mic_s = p.open(format=pyaudio.paInt16, channels=1, rate=48000, input=True)
        except Exception as e:
            print(f"[ERROR] Stream Init: {e}")
            return

        while self.is_running:
            try:
                s_raw = sys_s.read(1024, exception_on_overflow=False)
                m_raw = mic_s.read(1024, exception_on_overflow=False)
                m_np = np.frombuffer(m_raw, dtype=np.int16)
                vol = np.abs(m_np).mean()
                self.vol_label.config(text=f"VOL: {int(vol)}")

                if vol > self.mic_threshold:
                    self.current_source = "MIC"
                    self.status_label.config(text="LISTENING: YOU", fg="orange")
                    active_audio = m_np
                else:
                    self.current_source = "SYSTEM"
                    self.status_label.config(text="LISTENING: INTERVIEWER", fg="cyan")
                    active_audio = np.frombuffer(s_raw, dtype=np.int16)[::2]

                # Keep sending data 100% of the time
                self.audio_queue.put(active_audio[::3].tobytes())
            except: continue

    def deepgram_engine(self):
        client = DeepgramClient(DEEPGRAM_API_KEY)
        while self.is_running:
            try:
                dg_conn = client.listen.live.v("1")
                def on_msg(s, result, **kwargs):
                    transcript = result.channel.alternatives[0].transcript
                    if transcript and result.is_final:
                        self.sentence_buffer.append(transcript)
                        self.last_speech_time = time.time()

                dg_conn.on(LiveTranscriptionEvents.Transcript, on_msg)
                # Reduced endpointing to prevent 1011 timeout
                dg_conn.start(LiveOptions(model="nova-2", encoding="linear16", channels=1, sample_rate=16000, endpointing=300))
                
                while self.is_running:
                    try:
                        chunk = self.audio_queue.get(timeout=0.05)
                        dg_conn.send(chunk)
                    except queue.Empty:
                        # CRITICAL: Always send something to keep socket alive
                        dg_conn.send(np.zeros(512, dtype=np.int16).tobytes())
            except:
                time.sleep(1)

    def get_ai_response(self, text):
        try:
            sys_msg = f"SAP Architect. Role: {self.active_context}. ONLY 3 bullets. No intro."
            res = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": text}]
            )
            ans = res.choices[0].message.content.strip()
            self.root.after(0, lambda: self.update_display(text, ans))
        except: pass

    def update_display(self, q, a):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, f"\n\n--- {q[:45]}... ---\n", "faded")
        self.text_area.insert(tk.END, a + "\n", "bright")
        self.text_area.tag_config("faded", foreground="#444", font=("Segoe UI", 10, "italic"))
        self.text_area.tag_config("bright", foreground="#00FFCC")
        self.text_area.see(tk.END)
        self.text_area.config(state=tk.DISABLED)

    def auto_scroll_loop(self):
        try:
            curr = self.text_area.yview()[0]
            if curr < 0.98: self.text_area.yview_moveto(curr + self.scroll_speed)
        except: pass
        self.root.after(50, self.auto_scroll_loop)

    def start_move(self, event): self._x, self._y = event.x, event.y
    def do_move(self, event):
        x, y = self.root.winfo_x() + (event.x - self._x), self.root.winfo_y() + (event.y - self._y)
        self.root.geometry(f"+{x}+{y}")

if __name__ == "__main__":
    StableCopilot()