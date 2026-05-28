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
RESUME_CONTEXT = "SAP Architect: 19 years exp, HANA, S/4HANA, Cloud ALM."
groq_client = Groq(api_key=GROQ_API_KEY)

class MobileCopilot:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.geometry("600x480+400+50")
        self.root.configure(bg="#1A1A1A")

        self.mode = 0 # 0: System, 1: Mic
        self.audio_queue = queue.Queue(maxsize=500)
        self.is_running = True
        
        # --- UI SETUP ---
        self.header = tk.Frame(self.root, bg="#333", height=40, cursor="fleur")
        self.header.pack(fill="x")
        
        self.mode_btn = tk.Button(self.header, text="MODE: SYSTEM", bg="#444", fg="cyan", 
                                  command=self.toggle_mode, font=("Arial", 9, "bold"))
        self.mode_btn.pack(side="left", padx=10, pady=5)
        
        self.exit_btn = tk.Button(self.header, text="X", bg="#900", fg="white", 
                                  command=self.on_closing, font=("Arial", 9, "bold"))
        self.exit_btn.pack(side="right", padx=10, pady=5)

        self.status = tk.Label(self.header, text="IDLE", fg="white", bg="#333", font=("Arial", 8))
        self.status.pack(side="right", padx=20)

        # Labels
        self.q_label = tk.Label(self.root, text="Waiting for audio...", fg="#AAAAAA", bg="#1A1A1A", 
                                font=("Segoe UI", 10, "italic"), wraplength=560, justify="left")
        self.q_label.pack(fill="x", padx=20, pady=(10, 0))

        self.text_area = tk.Label(self.root, text="", fg="#00FFCC", bg="#1A1A1A", 
                                  font=("Segoe UI", 12, "bold"), wraplength=560, justify="left", anchor="nw")
        self.text_area.pack(expand=True, fill="both", padx=20, pady=10)

        # --- MOVEMENT BINDINGS ---
        self.header.bind("<Button-1>", self.start_move)
        self.header.bind("<B1-Motion>", self.do_move)
        self._x = 0
        self._y = 0

        # --- RUN ENGINES ---
        threading.Thread(target=self.hardware_engine, daemon=True).start()
        threading.Thread(target=self.deepgram_engine, daemon=True).start()
        
        # Clean shutdown protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def start_move(self, event):
        self._x = event.x
        self._y = event.y

    def do_move(self, event):
        x = self.root.winfo_x() + (event.x - self._x)
        y = self.root.winfo_y() + (event.y - self._y)
        self.root.geometry(f"+{x}+{y}")

    def on_closing(self):
        print("[TRACE] Shutting down immediately...")
        self.is_running = False
        self.root.destroy()
        sys.exit(0)

    def toggle_mode(self):
        self.mode = 1 if self.mode == 0 else 0
        self.mode_btn.config(text="MODE: MIC" if self.mode == 1 else "MODE: SYSTEM",
                             fg="orange" if self.mode == 1 else "cyan")
        print(f"[TRACE] Switched to {'MIC' if self.mode == 1 else 'SYSTEM'}")

    def get_ai_response(self, text):
        self.root.after(0, lambda: self.status.config(text="THINKING...", fg="yellow"))
        self.root.after(0, lambda: self.q_label.config(text=f"Last Question: {text}"))
        try:
            res = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": f"SAP Architect Expert. 3 brief bullets. Context: {RESUME_CONTEXT}"},
                    {"role": "user", "content": text}
                ],
            )
            ans = res.choices[0].message.content.replace('*', '').strip()
            self.root.after(0, lambda: self.text_area.config(text=ans))
            self.root.after(0, lambda: self.status.config(text="READY", fg="#00FF00"))
        except Exception as e:
            print(f"[TRACE] AI Error: {e}")

    def hardware_engine(self):
        p = pyaudio.PyAudio()
        try:
            # Always-On System Loopback
            sys_s = p.open(format=pyaudio.paInt16, channels=2, rate=48000, input=True, input_device_index=10)
            # Always-On Mic
            mic_info = p.get_default_input_device_info()
            mic_s = p.open(format=pyaudio.paInt16, channels=1, rate=int(mic_info['defaultSampleRate']), input=True)

            while self.is_running:
                if self.mode == 0:
                    data = sys_s.read(512, exception_on_overflow=False)
                    audio = np.frombuffer(data, dtype=np.int16)[::2][::3]
                    self.audio_queue.put(audio.tobytes())
                else:
                    data = mic_s.read(512, exception_on_overflow=False)
                    # Dynamic downsample for mic
                    skip = int(mic_info['defaultSampleRate'] / 16000)
                    audio = np.frombuffer(data, dtype=np.int16)[::skip]
                    self.audio_queue.put(audio.tobytes())
        except Exception as e:
            print(f"[TRACE] Hardware Engine Error: {e}")

    def deepgram_engine(self):
        while self.is_running:
            try:
                dg_conn = DeepgramClient(DEEPGRAM_API_KEY).listen.live.v("1")
                def on_msg(s, result, **kwargs):
                    txt = result.channel.alternatives[0].transcript
                    if txt and len(txt.split()) > 2 and result.is_final:
                        print(f"[TRACE] Heard: {txt}")
                        threading.Thread(target=self.get_ai_response, args=(txt,), daemon=True).start()

                dg_conn.on(LiveTranscriptionEvents.Transcript, on_msg)
                dg_conn.start(LiveOptions(model="nova-2", encoding="linear16", channels=1, sample_rate=16000))

                while self.is_running:
                    try:
                        chunk = self.audio_queue.get(timeout=0.05)
                        dg_conn.send(chunk)
                    except queue.Empty:
                        dg_conn.send(bytes(512)) # Heartbeat
            except Exception as e:
                if self.is_running:
                    print(f"[TRACE] Connection Reset: {e}")
                    time.sleep(1)

if __name__ == "__main__":
    MobileCopilot()