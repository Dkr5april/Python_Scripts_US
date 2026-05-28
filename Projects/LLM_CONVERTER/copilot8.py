import threading
import tkinter as tk
import pyaudiowpatch as pyaudio
import os
import time
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
            self.root, text="READY: Play your video now...",
            fg="#00FF00", bg="#121212", font=("Segoe UI", 11),
            wraplength=480, justify="left"
        )
        self.label.pack(expand=True, fill="both", padx=15, pady=15)

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
            self.root.after(0, lambda: self.label.config(text="Thinking...", fg="yellow"))
            res = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": f"SAP Interview Mode. 3 bullet points. Resume: {RESUME_CONTEXT}"},
                    {"role": "user", "content": text}
                ],
            )
            ans = res.choices[0].message.content
            self.root.after(0, lambda: self.label.config(text=ans, fg="white"))
        except Exception as e:
            print(f"AI Error: {e}")

    def run_engine(self):
        client = DeepgramClient(DEEPGRAM_API_KEY)
        
        while True:
            try:
                dg_conn = client.listen.live.v("1")

                def on_message(self_dg, result, **kwargs):
                    transcript = result.channel.alternatives[0].transcript
                    if transcript:
                        print(f"Captured: {transcript}")
                        if result.is_final and len(transcript.split()) > 3:
                            threading.Thread(target=self.get_ai_response, args=(transcript,), daemon=True).start()

                dg_conn.on(LiveTranscriptionEvents.Transcript, on_message)
                
                # Standard settings for high stability
                options = LiveOptions(model="nova-2", smart_format=True, encoding="linear16", channels=1, sample_rate=16000)
                dg_conn.start(options)

                p = pyaudio.PyAudio()
                # Find Headset Loopback
                wasapi = p.get_host_api_info_by_type(pyaudio.paWASAPI)
                default_output = p.get_device_info_by_index(wasapi["defaultOutputDevice"])
                
                loopback_idx = None
                for dev in p.get_loopback_device_info_generator():
                    if default_output["name"] in dev["name"]:
                        loopback_idx = dev["index"]
                        break

                # Force 16kHz directly from the source to prevent "1011" timeouts
                stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                                input=True, input_device_index=loopback_idx)

                self.root.after(0, lambda: self.label.config(text="Listening...", fg="#00FF00"))

                while True:
                    data = stream.read(1024, exception_on_overflow=False)
                    dg_conn.send(data)

            except Exception as e:
                print(f"Reconnecting... {e}")
                time.sleep(2)

if __name__ == "__main__":
    app = UniversalCopilot()