import threading
import tkinter as tk
import pyaudiowpatch as pyaudio
import os
import numpy as np # Needed for simple resampling
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
        self.root.geometry("500x280+400+50")
        self.root.configure(bg="#121212")

        self.label = tk.Label(
            self.root, text="🔄 Initializing Resampler...",
            fg="#00FF00", bg="#121212", font=("Segoe UI", 11),
            wraplength=480, justify="left"
        )
        self.label.pack(expand=True, fill="both", padx=15, pady=15)

        threading.Thread(target=self.run_audio_loop, daemon=True).start()
        self.root.mainloop()

    def get_ai_response(self, text):
        try:
            self.root.after(0, lambda: self.label.config(text="Analyzing...", fg="yellow"))
            res = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": f"SAP Interview Assistant. 3 bullets. Context: {RESUME_CONTEXT}"},
                    {"role": "user", "content": text}
                ],
            )
            ans = res.choices[0].message.content
            self.root.after(0, lambda: self.label.config(text=ans, fg="white"))
        except Exception as e:
            print(f"Groq Error: {e}")

    def run_audio_loop(self):
        try:
            client = DeepgramClient(DEEPGRAM_API_KEY)
            dg_connection = client.listen.live.v("1")

            def on_message(self_dg, result, **kwargs):
                transcript = result.channel.alternatives[0].transcript
                if transcript:
                    print(f"Captured: {transcript}")
                    if result.is_final and len(transcript.split()) > 2:
                        threading.Thread(target=self.get_ai_response, args=(transcript,), daemon=True).start()

            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            
            # Use Nova-2 on 16khz (standard for speech)
            options = LiveOptions(model="nova-2", smart_format=True, encoding="linear16", sample_rate=16000)
            dg_connection.start(options)

            p = pyaudio.PyAudio()
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_output_name = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])["name"]
            
            loopback_device = None
            for dev in p.get_loopback_device_info_generator():
                if default_output_name in dev["name"]:
                    loopback_device = dev
                    break
            
            if not loopback_device:
                loopback_device = list(p.get_loopback_device_info_generator())[0]

            hw_rate = int(loopback_device["defaultSampleRate"])
            hw_channels = loopback_device["maxInputChannels"]
            
            self.root.after(0, lambda: self.label.config(text=f"Listening: {loopback_device['name']}"))

            stream = p.open(
                format=pyaudio.paInt16,
                channels=hw_channels,
                rate=hw_rate,
                input=True,
                input_device_index=loopback_device["index"],
                frames_per_buffer=2048 # Increased buffer for stability
            )

            while True:
                raw_data = stream.read(2048, exception_on_overflow=False)
                
                # --- SIMPLE DOWN-SAMPLING TO 16kHz ---
                # This ensures Deepgram never gets overwhelmed by high-res audio
                audio_data = np.frombuffer(raw_data, dtype=np.int16)
                if hw_channels > 1:
                    audio_data = audio_data[::hw_channels] # Convert to Mono
                
                # Downsample from hardware rate to 16000Hz
                resampled_data = np.interp(
                    np.linspace(0, len(audio_data), int(len(audio_data) * 16000 / hw_rate)),
                    np.arange(len(audio_data)),
                    audio_data
                ).astype(np.int16)

                dg_connection.send(resampled_data.tobytes())

        except Exception as e:
            print(f"Audio Error: {e}")
            self.root.after(0, lambda: self.label.config(text="Connection Lost. Restarting...", fg="red"))

if __name__ == "__main__":
    app = UniversalCopilot()