import threading
import tkinter as tk
import pyaudiowpatch as pyaudio
import os
from groq import Groq
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

# ---------------- CONFIGURATION ---------------- #
# Note: Hardcoded for testing. Consider environment variables for production.
DEEPGRAM_API_KEY = "99a39ac2f2a40f15ad234dbabac8c5a7c4c7c997"
GROQ_API_KEY = "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"

# ---------------- LOAD RESUME ---------------- #
def load_resume():
    file_path = "resume.txt"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
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

        # Start the background audio engine
        threading.Thread(target=self.run_audio_loop, daemon=True).start()
        self.root.mainloop()

    def get_ai_response(self, text):
        """Fetch answer from Groq based on transcribed text."""
        try:
            self.root.after(0, lambda: self.label.config(text="Analyzing Question...", fg="yellow"))
            
            chat_completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system", 
                        "content": f"You are an SAP Architect assistant. Give exactly 3 short bullet points. Use this resume: {RESUME_CONTEXT}"
                    },
                    {"role": "user", "content": text}
                ],
            )
            answer = chat_completion.choices[0].message.content
            self.root.after(0, lambda: self.label.config(text=answer, fg="white"))
            
        except Exception as e:
            error_msg = f"Groq Error: {str(e)}"
            self.root.after(0, lambda: self.label.config(text=error_msg, fg="red"))

    def run_audio_loop(self):
        """Main Audio Capture and Deepgram Stream."""
        try:
            client = DeepgramClient(DEEPGRAM_API_KEY)
            dg_connection = client.listen.live.v("1")

            def on_message(self_dg, result, **kwargs):
                transcript = result.channel.alternatives[0].transcript
                if result.is_final and len(transcript.split()) > 3:
                    # Trigger AI in a separate thread to keep audio flow smooth
                    threading.Thread(target=self.get_ai_response, args=(transcript,), daemon=True).start()

            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            
            # Start Deepgram Connection
            options = LiveOptions(model="nova-2", smart_format=True)
            dg_connection.start(options)

            # Setup PyAudioWPatch for System Audio (Loopback)
            p = pyaudio.PyAudio()
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

            loopback_index = None
            for device in p.get_loopback_device_info_generator():
                if default_speakers["name"] in device["name"]:
                    loopback_index = device["index"]
                    break
            
            # Match Hardware Sample Rate
            actual_rate = int(default_speakers["defaultSampleRate"])
            actual_channels = default_speakers["maxInputChannels"]

            self.root.after(0, lambda: self.label.config(text="Listening to Speakers/Headphones...", fg="#00FF00"))

            stream = p.open(
                format=pyaudio.paInt16,
                channels=actual_channels,
                rate=actual_rate,
                input=True,
                input_device_index=loopback_index,
                frames_per_buffer=1024
            )

            while True:
                data = stream.read(1024, exception_on_overflow=False)
                dg_connection.send(data)

        except Exception as e:
            error_msg = f"Audio Engine Error: {str(e)}"
            self.root.after(0, lambda: self.label.config(text=error_msg, fg="red"))
            print(error_msg)

if __name__ == "__main__":
    app = UniversalCopilot()