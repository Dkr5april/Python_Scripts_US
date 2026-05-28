import threading
import tkinter as tk
import pyaudiowpatch as pyaudio
import os
import time
import numpy as np
import queue
import sys
import keyboard  # Requires: pip install keyboard
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
        self.root.geometry("600x400+400+50")
        self.root.configure(bg="#1A1A1A")
        
        self.mode = 0 
        self.audio_queue = queue.Queue(maxsize=500)
        self.is_running = True
        self.full_detail_cache = ""
        self.is_visible = True

        # --- UI SETUP ---
        self.header = tk.Frame(self.root, bg="#333", height=40, cursor="fleur")
        self.header.pack(fill="x")
        
        self.mode_btn = tk.Button(self.header, text="SYSTEM", bg="#444", fg="cyan", 
                                  command=self.toggle_mode, font=("Arial", 8, "bold"))
        self.mode_btn.pack(side="left", padx=5, pady=5)

        self.next_btn = tk.Button(self.header, text="NEXT >", bg="#222", fg="yellow", 
                                  command=self.show_full_detail, font=("Arial", 8, "bold"))
        self.next_btn.pack(side="left", padx=5)
        
        self.exit_btn = tk.Button(self.header, text="X", bg="#900", fg="white", 
                                  command=self.on_closing, font=("Arial", 8, "bold"))
        self.exit_btn.pack(side="right", padx=5, pady=5)

        self.status = tk.Label(self.header, text="IDLE", fg="#888", bg="#333", font=("Arial", 7))
        self.status.pack(side="right", padx=10)

        self.q_label = tk.Label(self.root, text="Listening...", fg="#666", bg="#1A1A1A", 
                                font=("Segoe UI", 9, "italic"), wraplength=560, justify="left")
        self.q_label.pack(fill="x", padx=20, pady=(10, 0))

        self.container = tk.Frame(self.root, bg="#1A1A1A")
        self.container.pack(expand=True, fill="both", padx=20, pady=10)

        self.text_area = tk.Text(self.container, fg="#00FFCC", bg="#1A1A1A", 
                                 font=("Segoe UI", 11), wrap="word", bd=0, highlightthickness=0)
        self.text_area.pack(side="left", expand=True, fill="both")

        # --- HOTKEYS ---
        # CTRL+SHIFT+H: Hide/Show window (Invisible Mode)
        keyboard.add_hotkey('ctrl+shift+h', self.toggle_visibility)
        # Right Arrow: Show Details
        self.root.bind("<Right>", lambda e: self.show_full_detail())

        self.header.bind("<Button-1>", self.start_move)
        self.header.bind("<B1-Motion>", self.do_move)

        threading.Thread(target=self.hardware_engine, daemon=True).start()
        threading.Thread(target=self.deepgram_engine, daemon=True).start()
        
        self.root.mainloop()

    def toggle_visibility(self):
        if self.is_visible:
            self.root.withdraw()
        else:
            self.root.deiconify()
            self.root.attributes("-topmost", True)
        self.is_visible = not self.is_visible

    def start_move(self, event):
        self._x = event.x
        self._y = event.y

    def do_move(self, event):
        x = self.root.winfo_x() + (event.x - self._x)
        y = self.root.winfo_y() + (event.y - self._y)
        self.root.geometry(f"+{x}+{y}")

    def on_closing(self):
        self.is_running = False
        self.root.destroy()
        sys.exit(0)

    def toggle_mode(self):
        self.mode = 1 if self.mode == 0 else 0
        self.mode_btn.config(text="MIC" if self.mode == 1 else "SYSTEM",
                             fg="orange" if self.mode == 1 else "cyan")

    def get_ai_response(self, text):
        self.root.after(0, lambda: self.status.config(text="THINKING...", fg="yellow"))
        self.root.after(0, lambda: self.q_label.config(text=f"Q: {text}"))
        try:
            res = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": f"""SAP Expert.
                    SUMMARY: One short sentence.
                    DETAILS: 3 technical bullets.
                    Context: {RESUME_CONTEXT}"""},
                    {"role": "user", "content": text}
                ],
            )
            raw = res.choices[0].message.content
            
            if "DETAILS:" in raw:
                parts = raw.split("DETAILS:")
                summary = parts[0].replace("SUMMARY:", "").strip()
                self.full_detail_cache = parts[1].strip()
            else:
                summary = raw
                self.full_detail_cache = "No additional details."

            def update_ui():
                self.text_area.delete('1.0', tk.END)
                self.text_area.insert(tk.END, summary)
                self.status.config(text="READY", fg="#00FF00")
            
            self.root.after(0, update_ui)
        except Exception as e:
            print(f"AI Error: {e}")

    def show_full_detail(self):
        self.text_area.delete('1.0', tk.END)
        self.text_area.insert(tk.END, self.full_detail_cache)

    def hardware_engine(self):
        p = pyaudio.PyAudio()
        try:
            sys_s = p.open(format=pyaudio.paInt16, channels=2, rate=48000, input=True, input_device_index=10)
            mic_info = p.get_default_input_device_info()
            mic_s = p.open(format=pyaudio.paInt16, channels=1, rate=int(mic_info['defaultSampleRate']), input=True)

            while self.is_running:
                if self.mode == 0:
                    data = sys_s.read(512, exception_on_overflow=False)
                    audio = np.frombuffer(data, dtype=np.int16)[::2][::3]
                    self.audio_queue.put(audio.tobytes())
                else:
                    data = mic_s.read(512, exception_on_overflow=False)
                    skip = int(mic_info['defaultSampleRate'] / 16000)
                    audio = np.frombuffer(data, dtype=np.int16)[::skip]
                    self.audio_queue.put(audio.tobytes())
        except Exception as e:
            print(f"Hardware Error: {e}")

    def deepgram_engine(self):
        while self.is_running:
            try:
                dg_conn = DeepgramClient(DEEPGRAM_API_KEY).listen.live.v("1")
                def on_msg(s, result, **kwargs):
                    txt = result.channel.alternatives[0].transcript
                    if txt and len(txt.split()) > 3 and result.is_final:
                        threading.Thread(target=self.get_ai_response, args=(txt,), daemon=True).start()

                dg_conn.on(LiveTranscriptionEvents.Transcript, on_msg)
                dg_conn.start(LiveOptions(model="nova-2", encoding="linear16", channels=1, sample_rate=16000))

                while self.is_running:
                    try:
                        chunk = self.audio_queue.get(timeout=0.05)
                        dg_conn.send(chunk)
                    except queue.Empty:
                        dg_conn.send(bytes(512)) 
            except Exception:
                if self.is_running:
                    time.sleep(1)

if __name__ == "__main__":
    MobileCopilot()