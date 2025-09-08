# rose_v10_macstyle_stable_v2.py
"""
Rose v10 — Mac-style assistant, tray icon, top-right mac buttons,
typing animation, always listening, voice reply (pyttsx3), black bg, neon purple text.
"""

import sys, os, time, threading
import pyttsx3
import speech_recognition as sr
import pywhatkit
import wikipedia
import pyjokes
from PySide6.QtWidgets import (
    QApplication, QWidget, QTextEdit, QPushButton, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QColor, QIcon

# ---------------- CONFIG ----------------
TEXT_COLOR = "#D700FF"  # neon purple
BG_COLOR = "rgba(0,0,0,200)"
KB_DIR = "kb_docs"
INDEX_SAVE = "kb_index"
MAX_MEMORY = 10

# ---------------- Voice Engine ----------------
engine = pyttsx3.init()
engine.setProperty("rate", 160)
recognizer = sr.Recognizer()

def talk(text):
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print("TTS Error:", e)

# ---------------- Chat memory ----------------
CHAT_HISTORY = []

# ---------------- COMMAND PROCESSING ----------------
def process_command(command):
    command = command.lower()
    global CHAT_HISTORY

    # Open apps
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
            else:
                os.startfile("https://www.google.com")
            resp = f"Opened {app_name}"
        except Exception as e:
            resp = f"Failed to open {app_name}: {e}"
        return resp

    # Play YouTube
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

    if "shutdown" in command:
        talk("Shutting down PC")
        os.system("shutdown /s /t 5")
        return "Shutting down PC"

    if "bye" in command or "stop" in command:
        talk("Goodbye")
        sys.exit()

    CHAT_HISTORY.append((command, f"I heard: {command}"))
    return f"I heard: {command}"

# ---------------- LISTENER THREAD ----------------
class ListenerThread(QThread):
    heard_signal = Signal(str)

    def run(self):
        while True:
            try:
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
                    text = recognizer.recognize_google(audio).lower()
                    if text:
                        self.heard_signal.emit(text)
            except Exception:
                continue

# ---------------- HUD ----------------
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

        # Top-right corner
        screen = QApplication.primaryScreen().geometry()
        width, height = 520, 380
        x, y = screen.width() - width - 20, 50
        self.setGeometry(x, y, width, height)
        self.setStyleSheet(f"background-color: {BG_COLOR}; border-radius:12px;")

        # Text area
        self.text_area = QTextEdit(self)
        self.text_area.setStyleSheet(f"background: transparent; color: {TEXT_COLOR}; font-family: Consolas; font-size:12pt;")
        self.text_area.setReadOnly(True)
        self.text_area.setGeometry(10, 40, width-20, height-50)

        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(25)
        glow.setColor(QColor(TEXT_COLOR))
        glow.setOffset(0)
        self.text_area.setGraphicsEffect(glow)

        # ---------------- Mac-style buttons ----------------
        self.close_btn = QPushButton("", self)
        self.close_btn.setStyleSheet("background-color:red;border-radius:7px;")
        self.close_btn.setGeometry(width-20, 10, 14, 14)
        self.close_btn.clicked.connect(lambda: sys.exit())

        self.min_btn = QPushButton("", self)
        self.min_btn.setStyleSheet("background-color:yellow;border-radius:7px;")
        self.min_btn.setGeometry(width-40, 10, 14, 14)
        self.min_btn.clicked.connect(self.showMinimized)

        self.max_btn = QPushButton("", self)
        self.max_btn.setStyleSheet("background-color:green;border-radius:7px;")
        self.max_btn.setGeometry(width-60, 10, 14, 14)
        self.max_btn.clicked.connect(self.showMaximized)

        # Typing animation
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.type_next_char)
        self.typing_text = ""
        self.typing_index = 0

        self.append_text("Rose v10 online — Listening continuously.")

    def append_text(self, text):
        self.text_area.append(text)
        self.text_area.repaint()

    def type_next_char(self):
        if self.typing_index < len(self.typing_text):
            current = self.text_area.toPlainText()
            self.text_area.setPlainText(current + self.typing_text[self.typing_index])
            self.typing_index += 1
        else:
            self.typing_timer.stop()
            talk(self.typing_text)

    def on_command(self, cmd):
        self.append_text(f"You: {cmd}")
        threading.Thread(target=self._process_and_show, args=(cmd,), daemon=True).start()

    def _process_and_show(self, cmd):
        self.typing_text = process_command(cmd)
        self.typing_index = 0
        self.typing_timer.start(50)

# ---------------- MAIN ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    hud = RoseHUD()
    hud.show()
    sys.exit(app.exec())
