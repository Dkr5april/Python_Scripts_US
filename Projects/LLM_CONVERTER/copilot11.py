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

groq_client = Groq(api_key=GROQ_API_KEY)

class SharedModeCopilot:
    def __init__(self, mic_id, sys_id):
        self.audio_queue = queue.Queue(maxsize=10000)
        self.is_running = True
        self.current_source = "SYSTEM"
        self.sentence_buffer = []
        self.last_speech_time = time.time()
        
        self.HW_RATE = 48000 
        self.mic_id = mic_id
        self.sys_id = sys_id

        self.root = tk.Tk()
        self.root.title("SAP Copilot - Final Shared Sync")
        self.root.attributes("-topmost", True)
        self.root.geometry("650x450")
        self.root.configure(bg="#050505")

        # Header Status
        self.status_bar = tk.Frame(self.root, bg="#111", height=35)
        self.status_bar.pack(fill="x")
        self.status = tk.Label(self.status_bar, text="WAITING FOR AUDIO...", fg="yellow", bg="#111", font=("Arial", 9, "bold"))
        self.status.pack(side="left", padx=10)
        
        # New: Activity Meter
        self.meter = tk.Canvas(self.status_bar, width=100, height=10, bg="#222", highlightthickness=0)
        self.meter.pack(side="right", padx=15)
        self.meter_fill = self.meter.create_rectangle(0, 0, 0, 10, fill="#00FF00")

        self.text_area = tk.Text(self.root, bg="black", fg="#00FFCC", font=("Segoe UI", 13), 
                                wrap=tk.WORD, bd=0, padx=20, pady=20)
        self.text_area.pack(expand=True, fill="both")

        threading.Thread(target=self.audio_capture, daemon=True).start()
        threading.Thread(target=self.cloud_service, daemon=True).start()
        self.root.mainloop()

    def audio_capture(self):
        p = pyaudio.PyAudio()
        try:
            # We open with 1024 frames per buffer to reduce latency
            mic_s = p.open(format=pyaudio.paInt16, channels=2, rate=self.HW_RATE, input=True, input_device_index=self.mic_id, frames_per_buffer=1024)
            sys_s = p.open(format=pyaudio.paInt16, channels=2, rate=self.HW_RATE, input=True, input_device_index=self.sys_id, frames_per_buffer=1024)
        except Exception as e:
            self.root.after(0, lambda: self.status.config(text=f"MIC ERROR: {e}", fg="red"))
            return

        while self.is_running:
            try:
                m_raw = mic_s.read(1024, exception_on_overflow=False)
                s_raw = sys_s.read(1024, exception_on_overflow=False)
                
                m_np = np.frombuffer(m_raw, dtype=np.int16)[::2] # Get Left Channel
                vol = np.abs(m_np).mean()

                # Update Visual Meter
                meter_w = min(int(vol / 5), 100)
                self.root.after(0, lambda v=meter_w: self.meter.coords(self.meter_fill, 0, 0, v, 10))

                if vol > 200: # Threshold for your voice
                    self.current_source = "MIC"
                    self.root.after(0, lambda: self.status.config(text="CAPTURING: YOU", fg="orange"))
                    self.audio_queue.put(m_np[::3].tobytes()) # Downsample to 16k
                else:
                    self.current_source = "SYSTEM"
                    self.root.after(0, lambda: self.status.config(text="CAPTURING: SYSTEM", fg="cyan"))
                    s_mono = np.frombuffer(s_raw, dtype=np.int16)[::2]
                    self.audio_queue.put(s_mono[::3].tobytes())
            except: pass

    def cloud_service(self):
        client = DeepgramClient(DEEPGRAM_API_KEY)
        while self.is_running:
            try:
                dg_conn = client.listen.live.v("1")
                def on_msg(s, result, **kwargs):
                    txt = result.channel.alternatives[0].transcript
                    if txt and result.is_final:
                        print(f"TRANSCRIPT: {txt}")
                        self.sentence_buffer.append(txt)
                        self.last_speech_time = time.time()

                dg_conn.on(LiveTranscriptionEvents.Transcript, on_msg)
                dg_conn.start(LiveOptions(model="nova-2", encoding="linear16", channels=1, sample_rate=16000, interim_results=False))

                while self.is_running:
                    chunk = self.audio_queue.get()
                    dg_conn.send(chunk)
                    
                    if self.sentence_buffer and (time.time() - self.last_speech_time > 1.2):
                        full_text = " ".join(self.sentence_buffer)
                        self.sentence_buffer = []
                        self.process_ai(full_text)
            except:
                time.sleep(2)

    def process_ai(self, text):
        try:
            res = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "system", "content": "SAP Architect. 3 technical points. Short."},
                          {"role": "user", "content": text}]
            )
            ans = res.choices[0].message.content
            self.root.after(0, lambda: self.text_area.insert(tk.END, f"\n--- {text[:40]} ---\n{ans}\n"))
            self.root.after(0, lambda: self.text_area.see(tk.END))
        except: pass

if __name__ == "__main__":
    SharedModeCopilot(5, 10)