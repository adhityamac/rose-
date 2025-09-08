# rose_v8_jarvis.py
"""
Rose v8 — Top-right HUD, tray integration, Apple-style animations,
Edge TTS voice, continuous voice input, always-on listening, offline fallback.
"""

import os
import sys
import time
import json
import threading
import asyncio
import pyttsx3
import speech_recognition as sr
import pyjokes
import wikipedia
import webbrowser

from PySide6.QtWidgets import (
    QApplication, QWidget, QTextEdit, QVBoxLayout, QPushButton, QGraphicsDropShadowEffect,
    QSystemTrayIcon, QMenu
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QPropertyAnimation
from PySide6.QtGui import QColor, QIcon

# ---------------- Config ----------------
EDGE_TTS_ENABLED = True  # use Edge TTS for human-like voice
WAKE_WORD = None  # always listening
HUD_WIDTH = 520
HUD_HEIGHT = 380
HUD_COLOR = "rgba(0,0,0,200)"
TEXT_COLOR = "#DA70D6"  # neon purple

# ---------------- Voice ----------------
recognizer = sr.Recognizer()

if not EDGE_TTS_ENABLED:
    engine = pyttsx3.init()
    engine.setProperty("rate", 160)

async def speak_edge(text):
    import edge_tts
    communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
    await communicate.play()

def talk(text):
    if EDGE_TTS_ENABLED:
        asyncio.run(speak_edge(text))
    else:
        engine.say(text)
        engine.runAndWait()

# ---------------- Command processing ----------------
def process_command(command):
    command = command.lower()
    resp = ""

    if "open youtube" in command:
        webbrowser.open("https://www.youtube.com")
        resp = "Opening YouTube"
    elif "open brave" in command:
        path = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
        if os.path.exists(path):
            os.startfile(path)
            resp = "Opening Brave Browser"
        else:
            webbrowser.open("https://www.google.com")
            resp = "Brave not found, opened Google"
    elif "open chrome" in command:
        path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        if os.path.exists(path):
            os.startfile(path)
            resp = "Opening Chrome"
        else:
            webbrowser.open("https://www.google.com")
            resp = "Chrome not found, opened Google"
    elif "play" in command:
        song = command.replace("play", "").strip()
        webbrowser.open(f"https://www.youtube.com/results?search_query={song}")
        resp = f"Playing {song} on YouTube"
    elif "wikipedia" in command:
        topic = command.replace("wikipedia", "").strip()
        try:
            resp = wikipedia.summary(topic, sentences=2)
        except Exception as e:
            resp = f"Wikipedia error: {e}"
    elif "joke" in command:
        resp = pyjokes.get_joke()
    elif "shutdown" in command:
        talk("Shutting down PC")
        os.system("shutdown /s /t 5")
        resp = "Shutting down PC"
    elif "bye" in command or "stop" in command:
        talk("Goodbye")
        sys.exit()
    else:
        resp = f"I heard: {command}"

    threading.Thread(target=talk, args=(resp,), daemon=True).start()
    return resp

# ---------------- Listener Thread ----------------
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

# ---------------- HUD ----------------
class RoseHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.tray = None
        self.init_ui()
        self.listener = ListenerThread()
        self.listener.heard_signal.connect(self.on_command)
        self.listener.start()

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        screen = QApplication.primaryScreen().geometry()
        x = screen.width() - HUD_WIDTH - 20
        y = 20
        self.setGeometry(x, y, HUD_WIDTH, HUD_HEIGHT)

        layout = QVBoxLayout()
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet(f"background-color: {HUD_COLOR}; color: {TEXT_COLOR}; font-family: Consolas; font-size: 12pt;")
        layout.addWidget(self.text_area)

        btn_layout = QVBoxLayout()
        self.min_btn = QPushButton("—")
        self.min_btn.setFixedWidth(40)
        self.min_btn.clicked.connect(self.minimize_to_tray)
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedWidth(40)
        self.close_btn.clicked.connect(lambda: sys.exit())
        btn_layout.addWidget(self.min_btn)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(30)
        glow.setColor(QColor(TEXT_COLOR))
        glow.setOffset(0)
        self.text_area.setGraphicsEffect(glow)

        self.append_text("Rose v8 online — always listening...")

        # Smooth fade-in
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(800)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()

        self.create_tray_icon()

        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_scroll)
        self.timer.start(250)

    def append_text(self, t):
        self.text_area.append(t)
        self.text_area.repaint()

    def on_command(self, command):
        self.append_text(f"You said: {command}")
        resp = process_command(command)
        self.append_text(f"Rose: {resp}")

    def auto_scroll(self):
        sb = self.text_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def create_tray_icon(self):
        self.tray = QSystemTrayIcon(QIcon())
        menu = QMenu()
        show_action = menu.addAction("Show Rose")
        show_action.triggered.connect(self.show)
        quit_action = menu.addAction("Quit Rose")
        quit_action.triggered.connect(lambda: sys.exit())
        self.tray.setContextMenu(menu)
        self.tray.setToolTip("Rose Assistant")
        self.tray.show()

    def minimize_to_tray(self):
        self.hide()
        self.tray.showMessage("Rose", "Rose minimized to tray!", QSystemTrayIcon.Information, 2000)

# ---------------- Main ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    hud = RoseHUD()
    hud.show()
    sys.exit(app.exec())
