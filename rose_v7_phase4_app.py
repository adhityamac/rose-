# rose_v7_phase4_app.py
"""
Rose v7 Phase 4 — Always-on assistant with voice, tray, typing animation,
neon purple HUD, offline-safe fallback, system tray support.
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
# Voice engine
# -----------------------------
engine = pyttsx3.init()
engine.setProperty("rate", 160)

def talk(text):
    engine.say(text)
    engine.runAndWait()

# -----------------------------
# Chat memory
# -----------------------------
CHAT_HISTORY = []
MAX_MEMORY = 10

# -----------------------------
# Local QA fallback
# -----------------------------
EMBED_MODEL = "all-MiniLM-L6-v2"
LOCAL_EMBS = None
LOCAL_TEXTS = None
FAISS_INDEX = None
HAS_FAISS = False
KB_DIR = "kb_docs"
INDEX_SAVE = "kb_index"

def try_load_local_index():
    global LOCAL_EMBS, LOCAL_TEXTS, FAISS_INDEX, HAS_FAISS
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        import faiss
        if os.path.exists(INDEX_SAVE):
            meta_path = os.path.join(INDEX_SAVE, "meta.json")
            emb_path = os.path.join(INDEX_SAVE, "embeddings.npy")
            if os.path.exists(meta_path) and os.path.exists(emb_path):
                with open(meta_path, "r", encoding="utf8") as f:
                    LOCAL_TEXTS = json.load(f)
                LOCAL_EMBS = np.load(emb_path)
                d = LOCAL_EMBS.shape[1]
                index = faiss.IndexFlatL2(d)
                index.add(LOCAL_EMBS)
                FAISS_INDEX = index
                HAS_FAISS = True
                print("Loaded local FAISS index.")
                return True
        return False
    except Exception as e:
        print("Local index load failed:", e)
        return False

def local_qa(query, k=3):
    if LOCAL_EMBS is None:
        return None
    import numpy as np
    q_emb = np.random.rand(1, LOCAL_EMBS.shape[1])  # fallback dummy if model not loaded
    if HAS_FAISS and FAISS_INDEX is not None:
        D, I = FAISS_INDEX.search(q_emb, k)
        return "\n\n".join([LOCAL_TEXTS[i]["text"] for i in I[0]])
    else:
        sims = (LOCAL_EMBS @ q_emb[0]) / ((np.linalg.norm(LOCAL_EMBS, axis=1) * np.linalg.norm(q_emb[0])) + 1e-8)
        idxs = sims.argsort()[::-1][:k]
        return "\n\n".join([LOCAL_TEXTS[i]["text"] for i in idxs])

# -----------------------------
# Process commands
# -----------------------------
def process_command(command):
    command = command.lower()
    global CHAT_HISTORY

    if "open" in command:
        app_name = command.replace("open", "").strip()
        try:
            if "brave" in app_name:
                path = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
                if os.path.exists(path):
                    os.startfile(path)
                else:
                    os.startfile("https://www.google.com")
            elif "chrome" in app_name:
                os.startfile("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
            elif "vscode" in app_name:
                os.startfile(f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe")
            else:
                os.startfile("https://www.google.com")
            resp = f"Opened {app_name}"
        except Exception as e:
            resp = f"Failed to open {app_name}: {e}"
        return resp

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

    # Chat memory
    memory_prompt = ""
    for u, a in CHAT_HISTORY[-MAX_MEMORY:]:
        memory_prompt += f"User: {u}\nAI: {a}\n"
    memory_prompt += f"User: {command}\nAI:"
    CHAT_HISTORY.append((command, f"I heard: {command}"))

    # Local QA fallback
    ans = local_qa(command)
    if ans:
        CHAT_HISTORY.append((command, ans))
        return ans

    return f"I heard: {command}"

# -----------------------------
# GUI + PySide6
# -----------------------------
from PySide6.QtWidgets import (
    QApplication, QWidget, QTextEdit, QVBoxLayout, QPushButton,
    QSystemTrayIcon, QMenu
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QColor, QIcon

engine.setProperty("voice", engine.getProperty('voices')[0].id)
GLOW_COLOR = "#DA00FF"  # neon purple

# -----------------------------
# Listener thread
# -----------------------------
recognizer = sr.Recognizer()
class ListenerThread(QThread):
    heard_signal = Signal(str)

    def run(self):
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
        self.listener = ListenerThread()
        self.listener.heard_signal.connect(self.on_command)
        self.listener.start()

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        screen = app.primaryScreen().geometry()
        width, height = 520, 380
        x = (screen.width() - width)//2
        y = (screen.height() - height)//2
        self.setGeometry(x, y, width, height)
        self.setStyleSheet(f"background-color: rgba(0,0,0,200); color: {GLOW_COLOR}; font-family: Consolas; font-size: 12pt;")
        layout = QVBoxLayout()
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet(f"background: transparent; color: {GLOW_COLOR};")
        layout.addWidget(self.text_area)
        exit_btn = QPushButton("Exit")
        exit_btn.clicked.connect(lambda: sys.exit())
        layout.addWidget(exit_btn)
        self.setLayout(layout)
        self.tray_icon = QSystemTrayIcon(QIcon())
        tray_menu = QMenu()
        tray_menu.addAction("Show/Hide", lambda: self.show() if not self.isVisible() else self.hide())
        tray_menu.addAction("Exit", lambda: sys.exit())
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.append_text("🌹 Rose v7 Phase 4 online — listening continuously...")

    def append_text(self, t):
        self.text_area.append(t)
        self.text_area.repaint()

    def on_command(self, command):
        self.append_text(f"You: {command}")
        threading.Thread(target=self._process_and_show, args=(command,), daemon=True).start()

    def _process_and_show(self, command):
        typing_text = "Rose: thinking..."
        self.append_text(typing_text)
        resp = process_command(command)
        # Typing animation
        display_text = ""
        for c in resp:
            display_text += c
            self.text_area.moveCursor(self.text_area.textCursor().End)
            self.text_area.setText(display_text)
            time.sleep(0.01)
        self.append_text(f"\nRose: {resp}")
        talk(resp)

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    try_load_local_index()
    app = QApplication(sys.argv)
    hud = RoseHUD()
    hud.show()
    sys.exit(app.exec())
