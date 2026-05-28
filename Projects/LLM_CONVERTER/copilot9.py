import threading
import tkinter as tk
import pyaudiowpatch as pyaudio
import os
import time
import numpy as np
import queue
from groq import Groq
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

# ---------------- CONFIGURATION ---------------- #
DEEPGRAM_API_KEY = "99a39ac2f2a40f15ad234dbabac8c5a7c4c7c997"
GROQ_API_KEY = "gsk_y5E8dKTA8pUjZmj41hPXWGdyb3FYrIx6QgKZFvgkxEzimmOIK)M5F"

def load_resume():
    if os.path.exists("resume.txt"):
        with open("resume.txt", "r", encoding="utf-8") as f:
            return f.read()
    return "SAP Architect Resume Context Loaded."

RESUME_CONTEXT = load_resume()
groq_client = Groq(api_key=GROQ_API_KEY)

class UniversalCopilot:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.9)
        self.root.geometry("500x300+400+50")
        self.root.configure(bg="#121212")

        self.label = tk.Label(
            self.root, text="System Ready - Listening to Realtek...",
            fg="#00FF00", bg="#121212", font=("Segoe UI", 11),
            wraplength=480, justify="left"
        )
        self.label.pack(expand=True, fill="both", padx=15, pady=15)

        self.audio_queue = queue.Queue() # Data buffer
        self.is_running = True

        # Draggable
        self.label.bind("<Button-1>", self.start_move)
        self.label.bind("<B1-Motion>", self.do_move)

        threading.Thread(target=self.run_engine, daemon=True).start()
        self.root.mainloop()

    def start_move(self, event):
        self.x, self.y = event.x, event.y
    def do_move(self, event):
        x = self.root.winfo_x() + (event.x - self.x)
        y = self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{x}+{y}")

    def get_ai_response(self, text):
        try:
            self.root.after(0, lambda: self.label.config(text="Analyzing...", fg="yellow"))
            res = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": f"SAP Interview Mode. 3 bullets. Context: {RESUME_CONTEXT}"},
                    {"role": "user", "content": text}
                ],
            )
            ans = res.choices[0].message.content
            self.root.after(0, lambda: self.label.config(text=ans, fg="white"))
        except Exception as e:
            print(f"AI Error: {e}")

    def run_engine(self):
        while self.is_running:
            try:
                client = DeepgramClient(DEEPGRAM_API_KEY)
                dg_conn = client.listen.live.v("1")

                def on_message(self_dg, result, **kwargs):
                    transcript = result.channel.alternatives[0].transcript
                    if transcript:
                        print(f"Captured: {transcript}")
                        if result.is_final and len(transcript.split()) > 3:
                            threading.Thread(target=self.get_ai_response, args=(transcript,), daemon=True).start()

                dg_conn.on(LiveTranscriptionEvents.Transcript, on_message)
                
                options = LiveOptions(model="nova-2", smart_format=True, encoding="linear16", channels=1, sample_rate=16000)
                dg_conn.start(options)

                # --- NEW: DEDICATED SENDER THREAD ---
                def sender():
                    while self.is_running:
                        try:
                            data = self.audio_queue.get(timeout=1)
                            dg_conn.send(data)
                        except queue.Empty:
                            # Send silence to keep connection alive if no audio
                            dg_conn.send(bytes(3200)) 
                        except:
                            break
                
                threading.Thread(target=sender, daemon=True).start()

                p = pyaudio.PyAudio()
                # HW_RATE: 48000, HW_CHANNELS: 2, DEVICE_INDEX: 10
                stream = p.open(format=pyaudio.paInt16, channels=2, rate=48000,
                                input=True, input_device_index=10, frames_per_buffer=2048)

                while self.is_running:
                    raw_data = stream.read(2048, exception_on_overflow=False)
                    audio_np = np.frombuffer(raw_data, dtype=np.int16)
                    # Convert 48kHz Stereo -> 16kHz Mono
                    downsampled = audio_np[::2][::3]
                    self.audio_queue.put(downsampled.tobytes())

            except Exception as e:
                print(f"Connection lost: {e}. Reconnecting in 2s...")
                time.sleep(2)

if __name__ == "__main__":
    app = UniversalCopilot()