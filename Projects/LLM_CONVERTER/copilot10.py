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
GROQ_API_KEY = "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"

def load_resume():
    if os.path.exists("resume.txt"):
        with open("resume.txt", "r", encoding="utf-8") as f:
            return f.read()
    return "SAP Architect: 19 years exp, HANA, S/4HANA, Cloud ALM."

RESUME_CONTEXT = load_resume()
groq_client = Groq(api_key=GROQ_API_KEY)

class UltimateCopilot:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SAP Interview Assistant")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)
        self.root.geometry("600x380+400+50")
        self.root.configure(bg="#1A1A1A")

        # Status Bar
        self.status_label = tk.Label(self.root, text="INITIALIZING...", fg="cyan", bg="#333", font=("Arial", 9))
        self.status_label.pack(fill="x")

        # Main Output Area
        self.text_area = tk.Label(
            self.root, text="Waiting for SAP question...",
            fg="#FFFFFF", bg="#1A1A1A", font=("Segoe UI", 12),
            wraplength=560, justify="left", anchor="nw"
        )
        self.text_area.pack(expand=True, fill="both", padx=20, pady=20)

        self.audio_queue = queue.Queue(maxsize=200)
        self.is_running = True

        # Drag functionality
        self.text_area.bind("<Button-1>", self.start_move)
        self.text_area.bind("<B1-Motion>", self.do_move)

        threading.Thread(target=self.main_audio_engine, daemon=True).start()
        self.root.mainloop()

    def start_move(self, event):
        self.x, self.y = event.x, event.y
    def do_move(self, event):
        x = self.root.winfo_x() + (event.x - self.x)
        y = self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{x}+{y}")

    def fetch_sap_answer(self, question):
        try:
            self.root.after(0, lambda: self.status_label.config(text="AI THINKING...", fg="yellow"))
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": f"You are a Senior SAP Architect. Give 3 short, strategic bullet points. Context: {RESUME_CONTEXT}"},
                    {"role": "user", "content": f"Briefly answer: {question}"}
                ],
            )
            answer = response.choices[0].message.content
            # Clean up formatting for the overlay
            display_text = answer.replace('*', '').strip()
            self.root.after(0, lambda: self.text_area.config(text=display_text, fg="#00FFCC"))
            self.root.after(0, lambda: self.status_label.config(text="READY", fg="#00FF00"))
        except Exception as e:
            print(f"Groq Error: {e}")

    def main_audio_engine(self):
        """Method: The High-Speed Threaded Relay"""
        p = pyaudio.PyAudio()
        
        # Hardware Config (From your report)
        HW_RATE = 48000
        HW_CHANNELS = 2
        DEVICE_INDEX = 10

        while self.is_running:
            try:
                dg_client = DeepgramClient(DEEPGRAM_API_KEY)
                dg_conn = dg_client.listen.live.v("1")

                def on_message(self_dg, result, **kwargs):
                    transcript = result.channel.alternatives[0].transcript
                    if transcript and len(transcript.split()) > 4:
                        print(f"Captured: {transcript}")
                        if result.is_final:
                            threading.Thread(target=self.fetch_sap_answer, args=(transcript,), daemon=True).start()

                dg_conn.on(LiveTranscriptionEvents.Transcript, on_message)
                
                # Method: Push Raw Format to Deepgram to avoid local CPU lag
                options = LiveOptions(model="nova-2", smart_format=True, encoding="linear16", channels=1, sample_rate=16000)
                dg_conn.start(options)

                # Dedicated Sender Thread (Keeps WebSocket alive)
                def audio_sender():
                    while self.is_running:
                        try:
                            chunk = self.audio_queue.get(timeout=1)
                            dg_conn.send(chunk)
                        except queue.Empty:
                            dg_conn.send(bytes(3200)) # Method: Keep-Alive Heartbeat
                        except: break

                threading.Thread(target=audio_sender, daemon=True).start()

                # Open hardware
                stream = p.open(format=pyaudio.paInt16, channels=HW_CHANNELS, rate=HW_RATE,
                                input=True, input_device_index=DEVICE_INDEX, frames_per_buffer=2048)
                
                self.root.after(0, lambda: self.status_label.config(text="LISTENING (48kHz)", fg="#00FF00"))

                while self.is_running:
                    raw_audio = stream.read(2048, exception_on_overflow=False)
                    # Method: Efficient Downsampling
                    audio_np = np.frombuffer(raw_audio, dtype=np.int16)
                    mono_16k = audio_np[::HW_CHANNELS][::3] # Take 1 channel, take every 3rd sample
                    self.audio_queue.put(mono_16k.tobytes())

            except Exception as e:
                print(f"Restarting Connection: {e}")
                time.sleep(2)

if __name__ == "__main__":
    UltimateCopilot()