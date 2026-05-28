import asyncio
import threading
import tkinter as tk
import pyaudiowpatch as pyaudio
import os
from groq import Groq
# Note the updated imports for Deepgram v3
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

# ---------------- CONFIG ---------------- #
# Hardcoded keys (Remove os.getenv so it reads the string directly)
DEEPGRAM_API_KEY = "99a39ac2f2a40f15ad234dbabac8c5a7c4c7c997"
GROQ_API_KEY = "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"

# ---------------- LOAD RESUME ---------------- #
def load_resume():
    if os.path.exists("resume.txt"):
        with open("resume.txt", "r", encoding="utf-8") as f:
            return f.read()
    return "No resume.txt found. Please ensure it is in the same folder."

RESUME_CONTEXT = load_resume()
groq_client = Groq(api_key=GROQ_API_KEY)

# ---------------- APP ---------------- #
class UniversalCopilot:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.9)
        self.root.geometry("500x250+400+50")
        self.root.configure(bg="#121212")

        self.label = tk.Label(
            self.root,
            text="System Ready... Listening to Speakers",
            fg="#00FF00",
            bg="#121212",
            font=("Arial", 11),
            wraplength=480,
            justify="left"
        )
        self.label.pack(expand=True, fill="both", padx=10)

        # Start the audio loop in a background thread
        threading.Thread(target=self.run_audio_loop, daemon=True).start()
        self.root.mainloop()

    def get_ai_response(self, text):
        try:
            self.root.after(0, lambda: self.label.config(text="Thinking...", fg="yellow"))
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an SAP Architect assistant. Give 3 short bullet points for:\n{RESUME_CONTEXT}"
                    },
                    {"role": "user", "content": text}
                ]
            )
            answer = response.choices[0].message.content
            self.root.after(0, lambda: self.label.config(text=answer, fg="white"))
        except Exception as e:
            self.root.after(0, lambda: self.label.config(text=f"Groq Error: {e}", fg="red"))

    def run_audio_loop(self):
        # Initialize Deepgram Client
        client = DeepgramClient(DEEPGRAM_API_KEY)
        dg_connection = client.listen.live.v("1")

        def on_message(self, result, **kwargs):
            transcript = result.channel.alternatives[0].transcript
            if transcript and len(transcript.split()) > 3:
                # Run AI fetch in a new thread so we don't block the audio
                threading.Thread(target=app.get_ai_response, args=(transcript,), daemon=True).start()

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

        options = LiveOptions(model="nova-2", smart_format=True)
        dg_connection.start(options)

        # Setup PyAudioWPatch for Loopback (Headphones/Speakers)
        p = pyaudio.PyAudio()
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

        loopback_index = None
        for device in p.get_loopback_device_info_generator():
            if default_speakers["name"] in device["name"]:
                loopback_index = device["index"]
                break

        stream = p.open(
            format=pyaudio.paInt16,
            channels=1, # 1 channel is more stable for Deepgram
            rate=16000, # 16kHz is standard for speech-to-text
            input=True,
            input_device_index=loopback_index,
            frames_per_buffer=1024
        )

        try:
            while True:
                data = stream.read(1024)
                dg_connection.send(data)
        except Exception as e:
            print(f"Audio Stream Error: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

if __name__ == "__main__":
    app = UniversalCopilot()