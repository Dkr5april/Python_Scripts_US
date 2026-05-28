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
RESUME_CONTEXT = "SAP Architect: 19 years exp."
groq_client = Groq(api_key=GROQ_API_KEY)

class FullTraceCopilot:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.geometry("600x480+400+50")
        self.root.configure(bg="#1A1A1A")

        self.mode = 0  # 0: System, 1: Mic
        self.audio_queue = queue.Queue(maxsize=2000)
        self.is_running = True
        
        # UI
        self.header = tk.Frame(self.root, bg="#333", height=40, cursor="fleur")
        self.header.pack(fill="x")
        self.mode_btn = tk.Button(self.header, text="MODE: SYSTEM", bg="#444", fg="cyan", command=self.toggle_mode)
        self.mode_btn.pack(side="left", padx=10)
        self.exit_btn = tk.Button(self.header, text="CLOSE", bg="#900", fg="white", command=self.on_closing)
        self.exit_btn.pack(side="right", padx=10)

        self.text_area = tk.Label(self.root, text="TRACE ACTIVE - Check PowerShell", fg="#00FFCC", bg="#1A1A1A", font=("Segoe UI", 12), wraplength=560)
        self.text_area.pack(expand=True, fill="both")

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
        print(f"\n[TRACE] MODE SWITCH: {'MIC' if self.mode == 1 else 'SYSTEM'}")

    def hardware_engine(self):
        p = pyaudio.PyAudio()
        
        # System Hardware Info
        sys_info = p.get_device_info_by_index(10)
        sys_rate = int(sys_info['defaultSampleRate'])
        sys_s = p.open(format=pyaudio.paInt16, channels=2, rate=sys_rate, input=True, input_device_index=10)
        
        # Mic Hardware Info
        m_info = p.get_default_input_device_info()
        m_rate = int(m_info['defaultSampleRate'])
        mic_s = p.open(format=pyaudio.paInt16, channels=1, rate=m_rate, input=True)

        print(f"[TRACE] HARDWARE INITIALIZED")
        print(f" -> System Device [10]: {sys_info['name']} @ {sys_rate}Hz")
        print(f" -> Mic Device [Default]: {m_info['name']} @ {m_rate}Hz")

        while self.is_running:
            try:
                t_start = time.perf_counter()
                if self.mode == 0:
                    data = sys_s.read(1024, exception_on_overflow=False)
                    audio_np = np.frombuffer(data, dtype=np.int16)[::2] # Mono
                    # Resample to 16k
                    skip = int(sys_rate / 16000)
                    audio_final = audio_np[::skip]
                else:
                    data = mic_s.read(1024, exception_on_overflow=False)
                    audio_np = np.frombuffer(data, dtype=np.int16)
                    skip = int(m_rate / 16000)
                    audio_final = audio_np[::skip]

                # REAL VALUE TRACE
                raw_bytes = len(data)
                sent_samples = len(audio_final)
                self.audio_queue.put(audio_final.tobytes())
                
                # Only print every ~1 second to keep console readable
                if self.audio_queue.qsize() % 50 == 0:
                    print(f"[TRACE] Capture: Raw={raw_bytes}b | Downsampled={sent_samples} samples | Q={self.audio_queue.qsize()}")
            except Exception as e:
                print(f"[TRACE ERROR] Hardware: {e}")

    def deepgram_engine(self):
        while self.is_running:
            try:
                print("[TRACE] Attempting Deepgram Handshake...")
                dg_conn = DeepgramClient(DEEPGRAM_API_KEY).listen.live.v("1")
                
                def on_msg(s, result, **kwargs):
                    txt = result.channel.alternatives[0].transcript
                    if txt and result.is_final:
                        print(f"[TRACE] HEARD: {txt}")
                        threading.Thread(target=self.get_ai_response, args=(txt,), daemon=True).start()

                dg_conn.on(LiveTranscriptionEvents.Transcript, on_msg)
                dg_conn.start(LiveOptions(model="nova-2", encoding="linear16", channels=1, sample_rate=16000))
                print("[TRACE] DEEPGRAM WEB_SOCKET OPEN")

                while self.is_running:
                    try:
                        chunk = self.audio_queue.get(timeout=0.1)
                        dg_conn.send(chunk)
                    except queue.Empty:
                        dg_conn.send(bytes(640)) # Heartbeat
            except Exception as e:
                print(f"[TRACE CRITICAL] Deepgram Error: {e}")
                time.sleep(2)

    def get_ai_response(self, text):
        try:
            res = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": text}]
            )
            print(f"[TRACE] AI Response Received")
            self.root.after(0, lambda: self.text_area.config(text=res.choices[0].message.content))
        except Exception as e:
            print(f"[TRACE ERROR] Groq: {e}")

if __name__ == "__main__":
    FullTraceCopilot()