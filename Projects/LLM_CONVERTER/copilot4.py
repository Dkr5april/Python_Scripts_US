import threading
import tkinter as tk
import pyaudiowpatch as pyaudio
import os
from groq import Groq
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

# ---------------- CONFIGURATION ---------------- #
DEEPGRAM_API_KEY = "99a39ac2f2a40f15ad234dbabac8c5a7c4c7c997"
GROQ_API_KEY = "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"

# ---------------- LOAD RESUME ---------------- #
def load_resume():
    file_path = "resume.txt"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return "No resume.txt found. Please create it in the script folder."

RESUME_CONTEXT = load_resume()
groq_client = Groq(api_key=GROQ_API_KEY)

# ---------------- APP LOGIC ---------------- #
class UniversalCopilot:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SAP Assistant")
        
        # UI Styling (Stealth Overlay)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.85)
        self.root.geometry("500x280+400+50")
        self.root.configure(bg="#121212")

        self.label = tk.Label(
            self.root,
            text="Initializing Audio Engine...",
            fg="#00FF00",
            bg="#121212",
            font=("Segoe UI", 11),
            wraplength=480,
            justify="left"
        )
        self.label.pack(expand=True, fill="both", padx=15, pady=15)

        # Allow dragging the window
        self.label.bind("<Button-1>", self.start_move)
        self.label.bind("<B1-Motion>", self.do_move)

        threading.Thread(target=self.run_audio_loop, daemon=True).start()
        self.root.mainloop()

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def get_ai_response(self, text):
        try:
            self.root.after(0, lambda: self.label.config(text="Analyzing Question...", fg="yellow"))
            chat_completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": f"SAP Architect Assistant. 3 short bullets. Resume: {RESUME_CONTEXT}"},
                    {"role": "user", "content": text}
                ],
            )
            answer = chat_completion.choices[0].message.content
            self.root.after(0, lambda: self.label.config(text=answer, fg="white"))
        except Exception as e:
            self.root.after(0, lambda: self.label.config(text=f"Groq Error: {e}", fg="red"))

    def run_audio_loop(self):
        try:
            client = DeepgramClient(DEEPGRAM_API_KEY)
            dg_connection = client.listen.live.v("1")

            def on_message(self_dg, result, **kwargs):
                transcript = result.channel.alternatives[0].transcript
                if result.is_final and len(transcript.split()) > 3:
                    threading.Thread(target=self.get_ai_response, args=(transcript,), daemon=True).start()

            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            dg_connection.start(LiveOptions(model="nova-2", smart_format=True))

            p = pyaudio.PyAudio()
            
            # --- IMPROVED DEVICE DETECTION ---
            loopback_device = None
            try:
                # Try to find the WASAPI loopback for the default speaker
                wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
                default_output = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
                
                for dev in p.get_loopback_device_info_generator():
                    if default_output["name"] in dev["name"]:
                        loopback_device = dev
                        break
            except:
                # Fallback: Just grab the first available loopback device
                for dev in p.get_loopback_device_info_generator():
                    loopback_device = dev
                    break

            if not loopback_device:
                raise Exception("No Loopback device found. Ensure speakers are active.")

            # Apply hardware settings
            actual_rate = int(loopback_device["defaultSampleRate"])
            
            self.root.after(0, lambda: self.label.config(text=f"Listening: {loopback_device['name']}", fg="#00FF00"))

            stream = p.open(
                format=pyaudio.paInt16,
                channels=loopback_device["maxInputChannels"], # Use native channels to avoid -9996
                rate=actual_rate,
                input=True,
                input_device_index=loopback_device["index"],
                frames_per_buffer=1024
            )

            while True:
                data = stream.read(1024, exception_on_overflow=False)
                dg_connection.send(data)

        except Exception as e:
            self.root.after(0, lambda: self.label.config(text=f"Audio Engine Error: {str(e)}", fg="red"))

if __name__ == "__main__":
    app = UniversalCopilot()