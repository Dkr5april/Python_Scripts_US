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
DEFAULT_CONTEXT = "SAP Architect: 19 years exp, HANA, S/4HANA, BTP, Basis."

# Your stored default location metadata
LAT, LON = 16.1176, 80.9314 

groq_client = Groq(api_key=GROQ_API_KEY)

class TeleprompterCopilot:
    def __init__(self):
        self.active_context = self.load_interview_context()
        self.conversation_history = []
        self.audio_queue = queue.Queue(maxsize=2000)
        self.is_running = True
        self.current_source = "SYSTEM"
        
        # SENSITIVITY SETTINGS
        self.mic_threshold = 400   
        self.scroll_speed = 0.0008 

        # --- UI SETUP ---
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.geometry("700x550+350+50")
        self.root.configure(bg="#0A0A0A")

        self.header = tk.Frame(self.root, bg="#1A1A1A", height=35)
        self.header.pack(fill="x")
        
        self.status_label = tk.Label(self.header, text="SYSTEM SYNC", fg="cyan", bg="#1A1A1A", font=("Arial", 9, "bold"))
        self.status_label.pack(side="left", padx=15)
        
        self.vol_label = tk.Label(self.header, text="MIC VOL: 0", fg="#555", bg="#1A1A1A", font=("Arial", 8))
        self.vol_label.pack(side="right", padx=15)

        self.text_area = tk.Text(self.root, bg="#0A0A0A", fg="#FFFFFF", font=("Segoe UI", 16, "bold"), 
                                wrap=tk.WORD, bd=0, padx=30, pady=30, highlightthickness=0)
        self.text_area.pack(expand=True, fill="both")
        self.text_area.config(state=tk.DISABLED)

        self.header.bind("<Button-1>", self.start_move)
        self.header.bind("<B1-Motion>", self.do_move)

        self.auto_scroll_loop()
        threading.Thread(target=self.dual_hardware_engine, daemon=True).start()
        threading.Thread(target=self.deepgram_engine, daemon=True).start()
        
        print(f"[TRACE] Started with Location Ref: {LAT}, {LON}")
        self.root.mainloop()

    def load_interview_context(self):
        ctx_dir = "contexts"
        if not os.path.exists(ctx_dir): os.makedirs(ctx_dir)
        files = [f for f in os.listdir(ctx_dir) if f.endswith(".txt")]
        if not files: return DEFAULT_CONTEXT
        print("\n--- SELECT INTERVIEW CONTEXT ---")
        for i, f in enumerate(files): print(f"[{i}] {f}")
        try:
            choice_str = input("Enter Index (or Enter for 0): ").strip()
            choice = int(choice_str) if choice_str else 0
            # --- FIXED SYNTAX HERE ---
            with open(os.path.join(ctx_dir, files[choice]), "r") as f:
                content = f.read().strip()
                self.selected_filename = files[choice]
                return content
        except Exception as e:
            print(f"[TRACE] Context Load Error: {e}. Using Default.")
            return DEFAULT_CONTEXT

    def auto_scroll_loop(self):
        if self.is_running:
            try:
                current_v = self.text_area.yview()[0]
                if current_v < 0.98: 
                    self.text_area.yview_moveto(current_v + self.scroll_speed)
            except: pass
            self.root.after(50, self.auto_scroll_loop)

    def dual_hardware_engine(self):
        p = pyaudio.PyAudio()
        try:
            sys_s = p.open(format=pyaudio.paInt16, channels=2, rate=48000, input=True, input_device_index=10)
            mic_s = p.open(format=pyaudio.paInt16, channels=1, rate=48000, input=True)
        except Exception as e:
            print(f"[CRITICAL ERROR] Hardware Init: {e}")
            return

        while self.is_running:
            try:
                s_raw = sys_s.read(1024, exception_on_overflow=False)
                m_raw = mic_s.read(1024, exception_on_overflow=False)
                s_np = np.frombuffer(s_raw, dtype=np.int16)[::2]
                m_np = np.frombuffer(m_raw, dtype=np.int16)
                vol = np.abs(m_np).mean()
                self.vol_label.config(text=f"MIC VOL: {int(vol)}")

                if vol > self.mic_threshold:
                    self.current_source = "MIC"
                    self.status_label.config(text="LISTENING: YOU", fg="orange")
                    final_audio = m_np
                else:
                    self.current_source = "SYSTEM"
                    self.status_label.config(text="LISTENING: INTERVIEWER", fg="cyan")
                    final_audio = s_np

                self.audio_queue.put(final_audio[::3].tobytes())
            except: pass

    def deepgram_engine(self):
        client = DeepgramClient(DEEPGRAM_API_KEY)
        while self.is_running:
            try:
                dg_conn = client.listen.live.v("1")
                def on_msg(s, result, **kwargs):
                    txt = result.channel.alternatives[0].transcript
                    if txt and result.is_final and len(txt.split()) > 2:
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
                print(f"[TRACE] Deepgram Reset: {e}")
                time.sleep(1)

    def get_ai_response(self, text):
        try:
            role = "INTERVIEWER" if self.current_source == "SYSTEM" else "CANDIDATE"
            sys_msg = f"SAP Expert Partner. Role: {self.active_context}. Provide EXACTLY 3 technical bullets. No intro/outro. Use Architect Keywords."
            
            msgs = [{"role": "system", "content": sys_msg}]
            for h in self.conversation_history[-3:]: msgs.append(h)
            msgs.append({"role": "user", "content": f"[{role}]: {text}"})

            res = groq_client.chat.completions.create(model="llama-3.1-8b-instant", messages=msgs)
            ans = res.choices[0].message.content.strip()

            self.conversation_history.append({"role": "user", "content": f"[{role}]: {text}"})
            self.conversation_history.append({"role": "assistant", "content": ans})
            self.root.after(0, lambda: self.update_display(text, ans))
        except: pass

    def update_display(self, topic, response):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, f"\n\n--- {topic[:40]} ---\n", "faded")
        self.text_area.insert(tk.END, response + "\n", "bright")
        self.text_area.tag_config("faded", foreground="#444", font=("Segoe UI", 10, "italic"))
        self.text_area.tag_config("bright", foreground="#00FFCC")
        self.text_area.see(tk.END)
        self.text_area.config(state=tk.DISABLED)

    def start_move(self, event): self._x, self._y = event.x, event.y
    def do_move(self, event):
        x = self.root.winfo_x() + (event.x - self._x)
        y = self.root.winfo_y() + (event.y - self._y)
        self.root.geometry(f"+{x}+{y}")

if __name__ == "__main__":
    TeleprompterCopilot()