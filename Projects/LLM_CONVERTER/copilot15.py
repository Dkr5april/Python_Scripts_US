import threading
import tkinter as tk
import pyaudiowpatch as pyaudio
import os
import time
import numpy as np
import queue
import sys
from groq import Groq
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

# ---------------- CONFIGURATION ---------------- #
DEEPGRAM_API_KEY = "99a39ac2f2a40f15ad234dbabac8c5a7c4c7c997"
GROQ_API_KEY = "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"
RESUME_CONTEXT = "SAP Architect: 19 years exp, HANA, S/4HANA."
groq_client = Groq(api_key=GROQ_API_KEY)

class MicFixedCopilot:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.geometry("600x480+400+50")
        self.root.configure(bg="#1A1A1A")

        self.mode = 0  # 0: System, 1: Mic
        self.audio_queue = queue.Queue(maxsize=2000)
        self.is_running = True
        
        # --- UI Header ---
        self.header = tk.Frame(self.root, bg="#333", height=40, cursor="fleur")
        self.header.pack(fill="x")
        self.mode_btn = tk.Button(self.header, text="MODE: SYSTEM", bg="#444", fg="cyan", 
                                  command=self.toggle_mode, font=("Arial", 9, "bold"))
        self.mode_btn.pack(side="left", padx=10, pady=5)
        self.exit_btn = tk.Button(self.header, text="CLOSE", bg="#900", fg="white", 
                                  command=self.on_closing, font=("Arial", 9, "bold"))
        self.exit_btn.pack(side="right", padx=10, pady=5)

        self.text_area = tk.Label(self.root, text="System: OK | Mic: Pending Fix...", fg="#00FFCC", bg="#1A1A1A", font=("Segoe UI", 12, "bold"), wraplength=560, anchor="nw")
        self.text_area.pack(expand=True, fill="both", padx=20, pady=20)

        self.header.bind("<Button-1>", self.start_move)
        self.header.bind("<B1-Motion>", self.do_move)

        threading.Thread(target=self.hardware_engine, daemon=True).start()
        threading.Thread(target=self.deepgram_engine, daemon=True).start()
        self.root.mainloop()

    def start_move(self, event): self._x, self._y = event.x, event.y
    def do_move(self, event):
        x = self.root.winfo_x() + (event.x - self._x)
        y = self.root.winfo_y() + (event.y - self._y)
        self.root.geometry(f"+{x}+{y}")

    def on_closing(self):
        self.is_running = False
        self.root.destroy()
        os._exit(0)

    def toggle_mode(self):
        self.mode = 1 if self.mode == 0 else 0
        self.mode_btn.config(text="MODE: MIC" if self.mode == 1 else "MODE: SYSTEM", fg="orange" if self.mode == 1 else "cyan")
        print(f"\n[TRACE] MODE SWITCH: {'MIC' if self.mode == 1 else 'SYSTEM'}")

    def hardware_engine(self):
        p = pyaudio.PyAudio()
        
        # 48000Hz Setup
        sys_s = p.open(format=pyaudio.paInt16, channels=2, rate=48000, input=True, input_device_index=10)
        
        # 44100Hz Setup (Based on your trace)
        m_info = p.get_default_input_device_info()
        m_rate = int(m_info['defaultSampleRate'])
        mic_s = p.open(format=pyaudio.paInt16, channels=1, rate=m_rate, input=True)

        print(f"[TRACE] Engine Calibrated: Sys(48k) Mic({m_rate})")

        while self.is_running:
            try:
                if self.mode == 0:
                    data = sys_s.read(960, exception_on_overflow=False) # 20ms
                    audio_np = np.frombuffer(data, dtype=np.int16)[::2] # Mono
                    audio_16k = audio_np[::3] # 48k -> 16k
                else:
                    # For 44.1k Mic, we need to read a chunk that aligns with 16k
                    chunk_size = int(m_rate * 0.04) # 40ms chunk
                    data = mic_s.read(chunk_size, exception_on_overflow=False)
                    audio_np = np.frombuffer(data, dtype=np.int16)
                    
                    # NATIVE RESAMPLING: We use linear indices to map 44.1k to 16k
                    indices = np.round(np.linspace(0, len(audio_np) - 1, int(len(audio_np) * 16000 / m_rate))).astype(int)
                    audio_16k = audio_np[indices]

                self.audio_queue.put(audio_16k.tobytes())
            except Exception as e:
                print(f"[TRACE ERROR] Hardware Loop: {e}")

    def deepgram_engine(self):
        while self.is_running:
            try:
                dg_conn = DeepgramClient(DEEPGRAM_API_KEY).listen.live.v("1")
                def on_msg(s, result, **kwargs):
                    txt = result.channel.alternatives[0].transcript
                    if txt and result.is_final:
                        print(f"[TRACE] HEARD: {txt}")
                        threading.Thread(target=self.get_ai_response, args=(txt,), daemon=True).start()

                dg_conn.on(LiveTranscriptionEvents.Transcript, on_msg)
                dg_conn.start(LiveOptions(model="nova-2", encoding="linear16", channels=1, sample_rate=16000))

                while self.is_running:
                    try:
                        chunk = self.audio_queue.get(timeout=0.05)
                        dg_conn.send(chunk)
                    except queue.Empty:
                        dg_conn.send(bytes(640)) # Heartbeat
            except Exception as e:
                print(f"[TRACE] WebSocket Reset: {e}")
                time.sleep(1)

    def get_ai_response(self, text):
        try:
            res = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "system", "content": "SAP Expert. 3 Bullets."}, {"role": "user", "content": text}]
            )
            ans = res.choices[0].message.content.strip()
            self.root.after(0, lambda: self.text_area.config(text=ans))
        except: pass

if __name__ == "__main__":
    MicFixedCopilot()