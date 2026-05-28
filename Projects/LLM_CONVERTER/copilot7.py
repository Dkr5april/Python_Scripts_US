import threading
import tkinter as tk
import pyaudiowpatch as pyaudio
import os
import numpy as np
import time
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
            self.root, text="System Ready - Waiting for audio stream...",
            fg="#00FF00", bg="#121212", font=("Segoe UI", 11),
            wraplength=480, justify="left"
        )
        self.label.pack(expand=True, fill="both", padx=15, pady=15)

        self.audio_queue = queue.Queue()
        self.label.bind("<Button-1>", self.start_move)
        self.label.bind("<B1-Motion>", self.do_move)

        threading.Thread(target=self.run_audio_engine, daemon=True).start()
        self.root.mainloop()

    def start_move(self, event):
        self.x, self.y = event.x, event.y
    def do_move(self, event):
        x = self.root.winfo_x() + (event.x - self.x)
        y = self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{x}+{y}")

    def get_ai_response(self, text):
        try:
            self.root.after(0, lambda: self.label.config(text="AI is thinking...", fg="yellow"))
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

    def run_audio_engine(self):
        while True:
            try:
                client = DeepgramClient(DEEPGRAM_API_KEY)
                dg_connection = client.listen.live.v("1")

                def on_message(self_dg, result, **kwargs):
                    transcript = result.channel.alternatives[0].transcript
                    if transcript:
                        print(f"Captured: {transcript}")
                        if result.is_final and len(transcript.split()) > 3:
                            threading.Thread(target=self.get_ai_response, args=(transcript,), daemon=True).start()

                dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
                
                options = LiveOptions(model="nova-2", smart_format=True, encoding="linear16", sample_rate=16000)
                dg_connection.start(options)

                # Separate thread to pull from queue and send to Deepgram
                def sender_thread():
                    while True:
                        data = self.audio_queue.get()
                        try:
                            dg_connection.send(data)
                        except:
                            break

                threading.Thread(target=sender_thread, daemon=True).start()

                p = pyaudio.PyAudio()
                wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
                default_output = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
                
                loopback_device = None
                for dev in p.get_loopback_device_info_generator():
                    if default_output["name"] in dev["name"]:
                        loopback_device = dev
                        break
                
                if not loopback_device:
                    loopback_device = list(p.get_loopback_device_info_generator())[0]

                hw_rate = int(loopback_device["defaultSampleRate"])
                hw_channels = loopback_device["maxInputChannels"]
                
                stream = p.open(format=pyaudio.paInt16, channels=hw_channels, rate=hw_rate,
                                input=True, input_device_index=loopback_device["index"], frames_per_buffer=1024)

                self.root.after(0, lambda: self.label.config(text="Stream Active - Listening...", fg="#00FF00"))

                while True:
                    raw_data = stream.read(1024, exception_on_overflow=False)
                    audio_data = np.frombuffer(raw_data, dtype=np.int16)
                    if hw_channels > 1: audio_data = audio_data[::hw_channels]
                    
                    resampled = np.interp(
                        np.linspace(0, len(audio_data), int(len(audio_data) * 16000 / hw_rate)),
                        np.arange(len(audio_data)),
                        audio_data
                    ).astype(np.int16)

                    # Push to queue instead of sending directly
                    self.audio_queue.put(resampled.tobytes())

            except Exception as e:
                print(f"Connection lost: {e}. Reconnecting...")
                time.sleep(2)

if __name__ == "__main__":
    app = UniversalCopilot()