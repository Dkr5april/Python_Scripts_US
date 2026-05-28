import threading
import tkinter as tk
import pyaudiowpatch as pyaudio
import numpy as np
import queue
import sys
import time
import keyboard 
from groq import Groq
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

# ---------------- CONFIGURATION ---------------- #
DEEPGRAM_API_KEY = "99a39ac2f2a40f15ad234dbabac8c5a7c4c7c997"
GROQ_API_KEY = "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"
RESUME_CONTEXT = "Senior SAP Project Manager & Architect: 19 years exp, S/4HANA, Cloud ALM, BTP."

groq_client = Groq(api_key=GROQ_API_KEY)

class MobileCopilot:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.geometry("600x350+400+50")
        self.root.configure(bg="#1A1A1A")
        
        self.mode = 0 # 0=System, 1=Mic
        self.audio_queue = queue.Queue()
        self.is_running = True
        self.full_detail_cache = ""
        self.is_visible = True

        # --- UI ---
        self.header = tk.Frame(self.root, bg="#333", height=35)
        self.header.pack(fill="x")
        self.mode_label = tk.Label(self.header, text="SYSTEM AUDIO", fg="cyan", bg="#333", font=("Arial", 8, "bold"))
        self.mode_label.pack(side="left", padx=10)
        
        self.status = tk.Label(self.header, text="LIVE", fg="#00FF00", bg="#333", font=("Arial", 7))
        self.status.pack(side="right", padx=10)

        self.q_display = tk.Label(self.root, text="Waiting for speech...", fg="#888", bg="#1A1A1A", font=("Segoe UI", 9, "italic"), wraplength=550)
        self.q_display.pack(pady=5)

        self.text_area = tk.Text(self.root, fg="#00FFCC", bg="#1A1A1A", font=("Segoe UI", 11), wrap="word", bd=0, highlightthickness=0)
        self.text_area.pack(expand=True, fill="both", padx=15, pady=5)

        keyboard.add_hotkey('ctrl+shift+h', self.toggle_visibility)
        keyboard.add_hotkey('ctrl+shift+m', self.toggle_mode)
        self.root.bind("<Right>", lambda e: self.show_details())

        threading.Thread(target=self.audio_stream_engine, daemon=True).start()
        threading.Thread(target=self.deepgram_engine, daemon=True).start()
        self.root.mainloop()

    def toggle_visibility(self):
        if self.is_visible: self.root.withdraw()
        else: self.root.deiconify(); self.root.attributes("-topmost", True)
        self.is_visible = not self.is_visible

    def toggle_mode(self):
        self.mode = 1 if self.mode == 0 else 0
        self.mode_label.config(text="MIC AUDIO" if self.mode == 1 else "SYSTEM AUDIO", 
                               fg="orange" if self.mode == 1 else "cyan")

    def show_details(self):
        if self.full_detail_cache:
            self.text_area.delete('1.0', tk.END)
            self.text_area.insert(tk.END, self.full_detail_cache)

    def get_sap_advice(self, text):
        self.root.after(0, lambda: self.status.config(text="THINKING", fg="yellow"))
        self.root.after(0, lambda: self.q_display.config(text=f"Q: {text}"))
        try:
            res = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": f"SAP Architect Expert. Context: {RESUME_CONTEXT}. Respond with SUMMARY: [1 sentence] and DETAILS: [3 technical bullets]."},
                    {"role": "user", "content": text}
                ],
            )
            ans = res.choices[0].message.content
            if "DETAILS:" in ans:
                parts = ans.split("DETAILS:")
                summary = parts[0].replace("SUMMARY:", "").strip()
                self.full_detail_cache = parts[1].strip()
            else:
                summary = ans
            
            def update():
                self.text_area.delete('1.0', tk.END)
                self.text_area.insert(tk.END, summary)
                self.status.config(text="LIVE", fg="#00FF00")
            self.root.after(0, update)
        except: pass

    def audio_stream_engine(self):
        p = pyaudio.PyAudio()
        try:
            # We open the hardware at its NATIVE rate (48000) to avoid OSError -9997
            sys_s = p.open(format=pyaudio.paInt16, channels=1, rate=48000, input=True, input_device_index=10)
            
            mic_info = p.get_default_input_device_info()
            mic_rate = int(mic_info['defaultSampleRate'])
            mic_s = p.open(format=pyaudio.paInt16, channels=1, rate=mic_rate, input=True)

            while self.is_running:
                if self.mode == 0:
                    data = sys_s.read(1024, exception_on_overflow=False)
                    # Resample 48000 -> 16000 (take every 3rd sample)
                    audio = np.frombuffer(data, dtype=np.int16)[::3].tobytes()
                else:
                    data = mic_s.read(1024, exception_on_overflow=False)
                    # Dynamic resampling for Mic
                    skip = int(mic_rate / 16000)
                    audio = np.frombuffer(data, dtype=np.int16)[::skip].tobytes()
                
                self.audio_queue.put(audio)
        except Exception as e:
            print(f"Hardware Error: {e}")

    def deepgram_engine(self):
        dg = DeepgramClient(DEEPGRAM_API_KEY)
        while self.is_running:
            try:
                conn = dg.listen.live.v("1")
                def on_transcript(self_dg, result, **kwargs):
                    if result.speech_final: 
                        transcript = result.channel.alternatives[0].transcript
                        if len(transcript.split()) > 3:
                            threading.Thread(target=self.get_sap_advice, args=(transcript,), daemon=True).start()

                conn.on(LiveTranscriptionEvents.Transcript, on_transcript)
                conn.start(LiveOptions(
                    model="nova-2", 
                    language="en-US",
                    smart_format=True,
                    endpointing=500, # This is your 500ms gap
                    encoding="linear16",
                    channels=1,
                    sample_rate=16000
                ))

                while self.is_running:
                    chunk = self.audio_queue.get()
                    conn.send(chunk)
            except Exception as e:
                time.sleep(1)

if __name__ == "__main__":
    MobileCopilot()