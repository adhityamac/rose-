# rose_v7_phase2_safe_v2.py
"""
Rose v7 Phase 2 — Safe offline & online features, TTS, persistent chat memory,
transparent HUD, neon purple text, wake-word voice recognition, and thread-safe GUI.
"""

import os
import sys
import time
import json
import threading
import requests
import pyttsx3
import speech_recognition as sr
import wikipedia
import pyjokes
import ctypes

# -----------------------------
# 1️⃣ Patch pywhatkit to skip internet check on import
# -----------------------------
try:
    import pywhatkit.core.core as core
    core.check_connection = lambda: True
except Exception as e:
    print(f"[WARNING] Failed to patch pywhatkit: {e}")

# -----------------------------
# 2️⃣ Import pywhatkit safely
# -----------------------------
try:
    import pywhatkit
except Exception as e:
    print(f"[WARNING] pywhatkit import failed: {e}")
    pywhatkit = None

# -----------------------------
# 3️⃣ Internet check
# -----------------------------
def is_online(test_url="https://google.com", timeout=5):
    try:
        requests.get(test_url, timeout=timeout)
        return True
    except:
        return False

# -----------------------------
# 4️⃣ Text-to-Speech
# -----------------------------
engine = pyttsx3.init()
engine.setProperty("rate", 160)

def talk(text):
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print("TTS error:", e)

# -----------------------------
# 5️⃣ Safe pywhatkit wrapper
# -----------------------------
def safe_pywhatkit_send(to_number, message, hour, minute):
    if not pywhatkit:
        talk("pywhatkit not available.")
        return
    if not is_online():
        talk("Internet not available. Cannot send message.")
        return
    try:
        pywhatkit.sendwhatmsg(to_number, message, hour, minute)
        talk("Message sent successfully!")
    except Exception as e:
        talk("Failed to send message.")

# -----------------------------
# 6️⃣ Chat memory, Gemini, local embeddings
# -----------------------------
CHAT_HISTORY = []
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MAX_MEMORY = 10
KB_DIR = "kb_docs"
INDEX_SAVE = "kb_index"
EMBED_MODEL = "all-MiniLM-L6-v2"
LOCAL_EMBS = None
LOCAL_TEXTS = None
FAISS_INDEX = None
HAS_FAISS = False

def ask_gemini(prompt):
    try:
        import google.generativeai as genai
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
        resp = genai.generate_text(model="gemini-1.5-flash-latest", input=prompt)
        if resp and getattr(resp, "text", None):
            return resp.text
        if isinstance(resp, dict) and "candidates" in resp:
            return resp["candidates"][0].get("content", "")
    except Exception:
        return None

def try_load_local_index():
    global LOCAL_EMBS, LOCAL_TEXTS, FAISS_INDEX, HAS_FAISS
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        if os.path.exists(INDEX_SAVE):
            meta_path = os.path.join(INDEX_SAVE, "meta.json")
            emb_path = os.path.join(INDEX_SAVE, "embeddings.npy")
            if os.path.exists(meta_path) and os.path.exists(emb_path):
                with open(meta_path, "r", encoding="utf8") as f:
                    LOCAL_TEXTS = json.load(f)
                LOCAL_EMBS = np.load(emb_path)
                try:
                    import faiss
                    d = LOCAL_EMBS.shape[1]
                    index = faiss.IndexFlatL2(d)
                    index.add(LOCAL_EMBS)
                    FAISS_INDEX = index
                    HAS_FAISS = True
                    print("Loaded local FAISS index.")
                except Exception:
                    HAS_FAISS = False
                    print("Loaded embeddings but FAISS not available.")
                return True
        return False
    except Exception as e:
        print("Local index load failed:", e)
        return False

def local_qa(query, k=3):
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        model = SentenceTransformer(EMBED_MODEL)
    except Exception:
        return None
    q_emb = model.encode([query], convert_to_numpy=True)
    if HAS_FAISS and FAISS_INDEX is not None:
        D, I = FAISS_INDEX.search(q_emb, k)
        return "\n\n".join([LOCAL_TEXTS[i]["text"] for i in I[0]])
    else:
        sims = (LOCAL_EMBS @ q_emb[0]) / ((np.linalg.norm(LOCAL_EMBS, axis=1) * np.linalg.norm(q_emb[0])) + 1e-8)
        idxs = sims.argsort()[::-1][:k]
        return "\n\n".join([LOCAL_TEXTS[i]["text"] for i in idxs])

# -----------------------------
# 7️⃣ Command processing
# -----------------------------
def process_command(command):
    command = command.lower()
    global CHAT_HISTORY

    if "open" in command:
        try:
            if "brave" in command:
                path = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
                os.startfile(path if os.path.exists(path) else "https://www.google.com")
            elif "chrome" in command:
                os.startfile("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
            elif "vscode" in command:
                os.startfile(f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe")
            else:
                os.startfile("https://www.google.com")
            return f"Opened app"
        except Exception as e:
            return f"Failed to open: {e}"

    if "play" in command:
        song = command.replace("play", "").strip()
        pywhatkit.playonyt(song)
        return f"Playing {song} on YouTube"

    if "wikipedia" in command:
        topic = command.replace("wikipedia", "").strip()
        try:
            return wikipedia.summary(topic, sentences=2)
        except Exception as e:
            return f"Wikipedia error: {e}"

    if "joke" in command:
        return pyjokes.get_joke()

    if "shutdown" in command:
        talk("Shutting down PC")
        os.system("shutdown /s /t 5")
        return "Shutting down PC"

    if "bye" in command or "stop" in command:
        talk("Goodbye")
        sys.exit()

    # Chat memory
    memory_prompt = ""
    for u, a in CHAT_HISTORY[-MAX_MEMORY:]:
        memory_prompt += f"User: {u}\nAI: {a}\n"
    memory_prompt += f"User: {command}\nAI:"

    gem = ask_gemini(memory_prompt) if GEMINI_API_KEY else None
    if gem:
        CHAT_HISTORY.append((command, gem))
        return gem

    if LOCAL_EMBS is not None:
        ans = local_qa(command)
        if ans:
            CHAT_HISTORY.append((command, ans))
            return ans

    CHAT_HISTORY.append((command, f"I heard: {command}"))
    return f"I heard: {command}"

# -----------------------------
# 8️⃣ GUI & listener thread
# -----------------------------
from PySide6.QtWidgets import QApplication, QWidget, QTextEdit, QVBoxLayout, QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QColor

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

recognizer = sr.Recognizer()
HUD = None
GLOW_COLOR = "#BF00FF"  # neon purple

class ListenerThread(QThread):
    heard_signal = Signal(str)
    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        while self.running:
            try:
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
                    text = recognizer.recognize_google(audio).lower()
                    if "rose" in text:
                        cmd = text.replace("rose", "").strip()
                        if cmd:
                            self.heard_signal.emit(cmd)
            except Exception:
                continue

    def stop(self):
        self.running = False
        self.quit()
        self.wait()

class RoseHUD(QWidget):
    append_signal = Signal(str)

    def __init__(self):
        super().__init__()
        global HUD
        HUD = self
        self.append_signal.connect(self.append_text)
        self.init_ui()

    def init_ui(self):
        screen = app.primaryScreen().geometry()
        width = 520; height = 380
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.setGeometry(x, y, width, height)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(0,0,0,200); border-radius: 12px;")

        layout = QVBoxLayout()
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet(f"background-color: rgba(0,0,0,0); color: {GLOW_COLOR}; font-family: Consolas; font-size: 12pt;")
        layout.addWidget(self.text_area)

        exit_btn = QPushButton("Exit")
        exit_btn.setStyleSheet("background-color: rgba(255,0,0,160); color: white; font-weight: bold;")
        exit_btn.clicked.connect(lambda: sys.exit())
        layout.addWidget(exit_btn)

        self.setLayout(layout)

        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(30)
        glow.setColor(QColor(GLOW_COLOR))
        glow.setOffset(0)
        self.text_area.setGraphicsEffect(glow)

        self.listener = ListenerThread()
        self.listener.heard_signal.connect(self.on_command)
        self.listener.start()

        self.append_text("Rose v7 online — say 'rose' then your command.")
        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_scroll)
        self.timer.start(250)

    def append_text(self, text):
        self.text_area.append(text)
        self.text_area.repaint()

    def on_command(self, command):
        self.append_signal.emit(f"You said: {command}")
        threading.Thread(target=self._process_and_show, args=(command,), daemon=True).start()

    def _process_and_show(self, command):
        self.append_signal.emit("Rose: thinking...")
        resp = process_command(command)
        self.append_signal.emit(f"Rose: {resp}")
        talk(resp)

    def auto_scroll(self):
        sb = self.text_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def closeEvent(self, event):
        self.listener.stop()
        event.accept()

# -----------------------------
# 9️⃣ Main
# -----------------------------
if __name__ == "__main__":
    try_load_local_index()
    # Uncomment to build embeddings first run
    # build_local_index_from_folder(KB_DIR)

    app = QApplication(sys.argv)
    hud = RoseHUD()
    hud.show()
    sys.exit(app.exec())
