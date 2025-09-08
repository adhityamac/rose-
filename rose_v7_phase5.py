# rose_v7_phase5.py
"""
Rose v7 Phase 5 — Persistent voice assistant with tray, always listening,
human-like TTS, mac-style buttons, typing animation, black HUD, neon purple text.
"""

import os
import sys
import time
import json
import threading
import requests
import pyttsx3
import speech_recognition as sr
import pywhatkit
import wikipedia
import pyjokes
import ctypes
from PySide6.QtWidgets import (
    QApplication, QWidget, QTextEdit, QVBoxLayout, QPushButton, QGraphicsDropShadowEffect,
    QSystemTrayIcon, QMenu, QAction, QHBoxLayout
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QColor, QIcon

# -----------------------------
# Patch pywhatkit to skip internet check
# -----------------------------
try:
    import pywhatkit.core.core as core
    core.check_connection = lambda: True
except Exception as e:
    print(f"[WARNING] Failed to patch pywhatkit: {e}")
try:
    import pywhatkit
except Exception as e:
    print(f"[WARNING] pywhatkit import failed: {e}")
    pywhatkit = None

# -----------------------------
# Internet check
# -----------------------------
def is_online(test_url="https://google.com", timeout=5):
    try:
        requests.get(test_url, timeout=timeout)
        return True
    except:
        return False

# -----------------------------
# TTS
# -----------------------------
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)
engine.setProperty('rate', 160)

def talk(text):
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print("TTS error:", e)

# -----------------------------
# Chat memory
# -----------------------------
CHAT_HISTORY = []
MAX_MEMORY = 10

# -----------------------------
# AI placeholders
# -----------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
KB_DIR = "kb_docs"

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

# -----------------------------
# Local embeddings fallback
# -----------------------------
EMBED_MODEL = "all-MiniLM-L6-v2"
LOCAL_EMBS = None
LOCAL_TEXTS = None
FAISS_INDEX = None
HAS_FAISS = False

def try_load_local_index():
    global LOCAL_EMBS, LOCAL_TEXTS, FAISS_INDEX, HAS_FAISS
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        if os.path.exists("kb_index"):
            meta_path = os.path.join("kb_index", "meta.json")
            emb_path = os.path.join("kb_index", "embeddings.npy")
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
# Command processing
# -----------------------------
def process_command(command):
    command = command.lower()
    global CHAT_HISTORY

    # App opening
    if "open" in command:
        app_name = command.replace("open", "").strip()
        try:
            if "brave" in app_name:
                path = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
                if os.path.exists(path): os.startfile(path)
                else: os.startfile("https://www.google.com")
            elif "chrome" in app_name:
                os.startfile("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
            elif "vscode" in app_name or "code" in app_name:
                os.startfile(f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe")
            else:
                os.startfile("https://www.google.com")
            resp = f"Opened {app_name}"
        except Exception as e:
            resp = f"Failed to open {app_name}: {e}"
        return resp

    # YouTube play
    if "play" in command:
        song = command.replace("play", "").strip()
        pywhatkit.playonyt(song)
        return f"Playing {song} on YouTube"

    # Wikipedia
    if "wikipedia" in command:
        topic = command.replace("wikipedia", "").strip()
        try:
            return wikipedia.summary(topic, sentences=2)
        except Exception as e:
            return f"Wikipedia error: {e}"

    # Joke
    if "joke" in command:
        return pyjokes.get_joke()

    # Shutdown
    if "shutdown" in command:
        talk("Shutting down PC")
        os.system("shutdown /s /t 5")
        return "Shutting down PC"

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
# Listener thread (always listening)
# -----------------------------
class ListenerThread(QThread):
    heard_signal = Signal(str)

    def run(self):
        recognizer = sr.Recognizer()
        while True:
            try:
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
                    text = recognizer.recognize_google(audio).lower()
                    self.heard_signal.emit(text)
            except Exception:
                continue

# -----------------------------
# HUD
# -----------------------------
class RoseHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        screen = app.primaryScreen().geometry()
        width = 520
        height = 380
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.setGeometry(x, y, width, height)
        self.setStyleSheet("background-color: rgba(0,0,0,220); border-radius: 12px;")

        # Mac-style buttons
        btn_layout = QHBoxLayout()
        btn_close = QPushButton()
        btn_close.setFixedSize(15,15)
        btn_close.setStyleSheet("background-color: #FF5F57; border-radius: 7px;")
        btn_close.clicked.connect(lambda: sys.exit())

        btn_min = QPushButton()
        btn_min.setFixedSize(15,15)
        btn_min.setStyleSheet("background-color: #FFBD2E; border-radius: 7px;")
        btn_min.clicked.connect(lambda: self.hide())

        btn_layout.addWidget(btn_close)
        btn_layout.addWidget(btn_min)
        btn_layout.addStretch()

        layout = QVBoxLayout()
        layout.addLayout(btn_layout)

        self.text_area = QTextEdit()
        self.text_area.setStyleSheet(
            "background-color: rgba(0,0,0,0); color: #9b59b6; font-family: Consolas; font-size: 12pt;"
        )
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)
        self.setLayout(layout)

        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(30)
        glow.setColor(QColor("#9b59b6"))
        glow.setOffset(0)
        self.text_area.setGraphicsEffect(glow)

        # Tray icon
        self.tray = QSystemTrayIcon(QIcon())
        menu = QMenu()
        restore_action = QAction("Restore")
        restore_action.triggered.connect(self.show)
        menu.addAction(restore_action)
        quit_action = QAction("Quit")
        quit_action.triggered.connect(lambda: sys.exit())
        menu.addAction(quit_action)
        self.tray.setContextMenu(menu)
        self.tray.show()

        # Start listener
        self.listener = ListenerThread()
        self.listener.heard_signal.connect(self.on_command)
        self.listener.start()

        self.append_text("🌹 Rose v7 Phase 5 online — listening continuously...")
        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_scroll)
        self.timer.start(250)

    def append_text(self, t):
        self.text_area.append(t)
        self.text_area.repaint()

    def on_command(self, command):
        self.append_text(f"You said: {command}")
        threading.Thread(target=self._process_and_show, args=(command,), daemon=True).start()

    def _process_and_show(self, command):
        self.append_text("Rose: thinking...")
        resp = process_command(command)
        for ch in resp:  # typing animation
            self.text_area.insertPlainText(ch)
            QApplication.processEvents()
            time.sleep(0.02)
        self.text_area.append("\n")
        talk(resp)

    def auto_scroll(self):
        sb = self.text_area.verticalScrollBar()
        sb.setValue(sb.maximum())

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    try_load_local_index()
    app = QApplication(sys.argv)
    hud = RoseHUD()
    hud.show()
    sys.exit(app.exec())
