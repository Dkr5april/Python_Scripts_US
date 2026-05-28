import threading
import tkinter as tk
from tkinter import scrolledtext
import pyaudiowpatch as pyaudio
import numpy as np
import queue
import time
import os
import sys
from groq import Groq
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

# ---------------- CONFIGURATION ---------------- #
DEEPGRAM_API_KEY = "99a39ac2f2a40f15ad234dbabac8c5a7c4c7c997"
GROQ_API_KEY = "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"
DEFAULT_CONTEXT = "SAP Architect: 19 years exp, HANA, S/4HANA."
LAT, LON = 16.1176, 80.9314 # Default Location Applied

groq_client = Groq(api_key=GROQ_API_KEY)

class AutoSenseCopilot:
    def __init__(self):
        self.active_context = self.load_interview_context()
        self.conversation_history = []
        self.audio_queue = queue.Queue(maxsize=2000)
        self.is_running = True
        self.current_source = "SYSTEM"
        self.mic_threshold = 300  # Adjust if your room is noisy

        # --- UI SETUP ---
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.geometry("600x550+400+50")
        self.root.configure(bg="#121212")

        self.header = tk.Frame(self.root, bg="#222", height=35)
        self.header.pack(fill="x")
        
        self.status_label = tk.Label(self.header, text="INIT HARDWARE...", fg="yellow", bg="#222", font=("Arial", 8, "bold"))
        self.status_label.pack(side="left", padx=10)
        
        self.ctx_label = tk.Label(self.header, text=f"CTX: {getattr(self, 'selected_filename', 'Default')}", fg="#888", bg="#222", font=("Arial", 7))
        self.ctx_label.pack(side="right", padx=10)

        self.text_area = scrolledtext.ScrolledText(self.root, bg="#121212", fg="#00FFCC", font=("Segoe UI", 13, "bold"), wrap=tk.WORD, bd=0, padx=15, pady=15)
        self.text_area.pack(expand=True, fill="both")
        self.text_area.config(state=tk.DISABLED)

        # Draggable logic
        self.header.bind("<Button-1>", self.start_move)
        self.header.bind("<B1-Motion>", self.do_move)

        # Threads
        threading.Thread(target=self.dual_engine, daemon=True).start()
        threading.Thread(target=self.deepgram_engine, daemon=True).start()
        
        self.root.mainloop()

    def load_interview_context(self):
        ctx_dir = "contexts"
        if not os.path.exists(ctx_dir): os.makedirs(ctx_dir)
        files = [f for f in os.listdir(ctx_dir) if f.endswith(".txt")]
        if not files: return DEFAULT_CONTEXT
        print("\n[TRACE] Select Context Index:")
        for i, f in enumerate(files): print(f"[{i}] {f}")
        try:
            c = int(input("Index: ") or 0)
            self.selected_filename = files[c]
            return open(os.path.join(ctx_dir, files[c]), "r").read().strip()
        except: return DEFAULT_CONTEXT

    def dual_engine(self):
        """Monitors both MIC and SYSTEM; autoswitches based on loudness"""
        p = pyaudio.PyAudio()
        try:
            # Open System Loopback at 48k
            sys_s = p.open(format=pyaudio.paInt16, channels=2, rate=48000, input=True, input_device_index=10)
            # Open Mic at 48k for clock sync
            mic_s = p.open(format=pyaudio.paInt16, channels=1, rate=48000, input=True)
            print("[TRACE] Dual hardware streams locked at 48000Hz")
        except Exception as e:
            print(f"[CRITICAL] Hardware Error: {e}")
            return

        while self.is_running:
            try:
                s_data = sys_s.read(1024, exception_on_overflow=False)
                m_data = mic_s.read(1024, exception_on_overflow=False)
                
                s_np = np.frombuffer(s_data, dtype=np.int16)[::2] # Mono
                m_np = np.frombuffer(m_data, dtype=np.int16)

                vol = np.abs(m_np).mean()
                
                # SENSE LOGIC
                if vol > self.mic_threshold:
                    self.current_source = "MIC"
                    final = m_np
                    self.status_label.config(text=f"LISTENING: MIC (VOL: {int(vol)})", fg="orange")
                else:
                    self.current_source = "SYSTEM"
                    final = s_np
                    self.status_label.config(text=f"LISTENING: SYSTEM", fg="cyan")

                # Resample 48k to 16k
                self.audio_queue.put(final[::3].tobytes())
            except Exception as e:
                print(f"[TRACE] Hardware loop warning: {e}")

    def deepgram_engine(self):
        client = DeepgramClient(DEEPGRAM_API_KEY)
        while self.is_running:
            try:
                dg_conn = client.listen.live.v("1")
                def on_msg(s, result, **kwargs):
                    txt = result.channel.alternatives[0].transcript
                    if txt and result.is_final and len(txt.split()) > 2:
                        print(f"[TRACE] HEARD ({self.current_source}): {txt}")
                        threading.Thread(target=self.get_ai_response, args=(txt,), daemon=True).start()
                
                dg_conn.on(LiveTranscriptionEvents.Transcript, on_msg)
                dg_conn.start(LiveOptions(model="nova-2", encoding="linear16", channels=1, sample_rate=16000))
                
                while self.is_running:
                    try:
                        chunk = self.audio_queue.get(timeout=0.05)
                        dg_conn.send(chunk)
                    except queue.Empty:
                        dg_conn.send(bytes(640))
            except Exception as e:
                print(f"[TRACE] Connection Reset: {e}")
                time.sleep(1)

    def get_ai_response(self, text):
        try:
            source_label = "INTERVIEWER" if self.current_source == "SYSTEM" else "ME"
            prompt = f"SAP Architect Partner. Context: {self.active_context}. If speaker is ME, check for technical accuracy and suggest missing keywords. If INTERVIEWER, provide 3 bullets for a perfect answer. Use high-level terminology."
            
            messages = [{"role": "system", "content": prompt}]
            for h in self.conversation_history[-4:]: messages.append(h)
            messages.append({"role": "user", "content": f"[{source_label}]: {text}"})

            res = groq_client.chat.completions.create(model="llama-3.1-8b-instant", messages=messages)
            ans = res.choices[0].message.content.strip()

            self.conversation_history.append({"role": "user", "content": f"[{source_label}]: {text}"})
            self.conversation_history.append({"role": "assistant", "content": ans})
            
            self.root.after(0, lambda: self.refresh_ui(text, ans))
        except Exception as e:
            print(f"[TRACE] AI Error: {e}")

    def refresh_ui(self, q, a):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete('1.0', tk.END)
        self.text_area.insert(tk.END, f"LAST INPUT: {q.upper()}\n\n", "faded")
        self.text_area.insert(tk.END, a)
        self.text_area.tag_config("faded", foreground="#444", font=("Segoe UI", 9))
        self.text_area.see(tk.END)
        self.text_area.config(state=tk.DISABLED)

    def start_move(self, event): self._x, self._y = event.x, event.y
    def do_move(self, event):
        x = self.root.winfo_x() + (event.x - self._x)
        y = self.root.winfo_y() + (event.y - self._y)
        self.root.geometry(f"+{x}+{y}")

if __name__ == "__main__":
    AutoSenseCopilot()