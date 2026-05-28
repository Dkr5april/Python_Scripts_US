import threading
import tkinter as tk
import pyaudiowpatch as pyaudio
import os
from groq import Groq

# ---------------- DEEPGRAM IMPORTS (5.3.2 CORRECT) ---------------- #
from deepgram import DeepgramClient, LiveTranscriptionEvents
from deepgram.clients.listen.v1 import LiveOptions

# ---------------- CONFIGURATION ---------------- #

DEEPGRAM_API_KEY = os.getenv("99a39ac2f2a40f15ad234dbabac8c5a7c4c7c997")
GROQ_API_KEY = os.getenv("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")

if not DEEPGRAM_API_KEY:
    raise ValueError("DEEPGRAM_API_KEY environment variable not set")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")

# ---------------- LOAD RESUME ---------------- #

def load_resume():
    file_path = "resume.txt"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return "No resume.txt found."

RESUME_CONTEXT = load_resume()
groq_client = Groq(api_key=GROQ_API_KEY)

# ---------------- MAIN APP ---------------- #

class UniversalCopilot:

    def __init__(self):
        self.root = tk.Tk()

        # Stealth Window
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.92)
        self.root.geometry("500x250+400+50")
        self.root.configure(bg="#121212")

        self.label = tk.Label(
            self.root,
            text="System Ready. Waiting for speech...",
            fg="#00FF00",
            bg="#121212",
            font=("Arial", 11),
            wraplength=480,
            justify="left"
        )
        self.label.pack(expand=True, fill="both", padx=10)

        threading.Thread(target=self.start_audio, daemon=True).start()

        self.root.mainloop()

    # ---------------- GROQ RESPONSE ---------------- #

    def get_ai_response(self, text):
        try:
            self.root.after(
                0,
                lambda: self.label.config(text="Thinking...", fg="yellow")
            )

            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an SAP Architect interview assistant. "
                            "Provide exactly 3 short, punchy bullet points "
                            "based on this resume:\n\n"
                            f"{RESUME_CONTEXT}"
                        ),
                    },
                    {"role": "user", "content": text},
                ],
            )

            answer = response.choices[0].message.content

            self.root.after(
                0,
                lambda: self.label.config(text=answer, fg="white")
            )

        except Exception as e:
            self.root.after(
                0,
                lambda: self.label.config(text=f"Groq Error: {e}", fg="red")
            )

    # ---------------- DEEPGRAM AUDIO ---------------- #

    def start_audio(self):
        try:
            deepgram = DeepgramClient(DEEPGRAM_API_KEY)

            dg_connection = deepgram.listen.live()

            # Transcript callback
            def on_message(self_dg, result, **kwargs):
                try:
                    transcript = result.channel.alternatives[0].transcript
                    if result.is_final and transcript and len(transcript.split()) > 3:
                        threading.Thread(
                            target=self.get_ai_response,
                            args=(transcript,),
                            daemon=True
                        ).start()
                except Exception:
                    pass

            dg_connection.on(
                LiveTranscriptionEvents.Transcript,
                on_message
            )

            options = LiveOptions(
                model="nova-3",
                smart_format=True,
                encoding="linear16",
                sample_rate=48000,
                channels=2
            )

            dg_connection.start(options)

            # ---------------- LOOPBACK AUDIO ---------------- #

            p = pyaudio.PyAudio()

            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_speakers = p.get_device_info_by_index(
                wasapi_info["defaultOutputDevice"]
            )

            loopback_index = None

            for device in p.get_loopback_device_info_generator():
                if default_speakers["name"] in device["name"]:
                    loopback_index = device["index"]
                    break

            if loopback_index is None:
                raise Exception("Loopback device not found")

            def stream_callback(in_data, frame_count, time_info, status):
                dg_connection.send(in_data)
                return (None, pyaudio.paContinue)

            stream = p.open(
                format=pyaudio.paInt16,
                channels=2,
                rate=48000,
                input=True,
                input_device_index=loopback_index,
                frames_per_buffer=1024,
                stream_callback=stream_callback,
            )

            stream.start_stream()

            while stream.is_active():
                pass

        except Exception as e:
            self.root.after(
                0,
                lambda: self.label.config(text=f"Audio Error: {e}", fg="red")
            )


# ---------------- RUN ---------------- #

if __name__ == "__main__":
    UniversalCopilot()
