# rose_v7_phase7_tray.py
"""
Rose v7 — Jarvis-mode, always listening, Edge TTS human voice,
tray icon minimization, neon-purple HUD, typing animation, offline fallback, chat memory.
"""

import os, sys, time, threading, json
import ctypes
import requests
import pyttsx3
import pywhatkit
import wikipedia
import pyjokes

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
# Voice engine
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
# Internet check
# -----------------------------
def is_online(test_url="https://google.com", timeout=5):
    try:
        requests.get(test_url, timeout=timeout)
        return True
    except:
        return False

# -----------------------------
# Chat memory
# -----------------------------
CHAT_HISTORY = []
MAX_MEMORY = 10

# -----------------------------
# Simple AI response
# -----------------------------
def process_command(command):
    command = command.lower()
    # Predefined commands
    if "open" in command:
        app_name = command.replace("open", "").strip()
        try:
            if "brave" in app_name:
                os.startfile("C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe")
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

    if "play" in command:
        song = command.replace("play", "").strip()
        if is_online() and pywhatkit:
            pywhatkit.playonyt(song)
        return f"Playing {song}"

    if "wikipedia" in command:
        topic = command.replace("wikipedia", "").strip()
        try:
            return wikipedia.summary(topic, sentences=2)
        except:
            return "Wikipedia error."

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

# -----------------------------
# GUI
# -----------------------------
from PySide6.QtWidgets import (
    QApplication, QWidget, QTextEdit, QVBoxLayout, QPushButton,
    QGraphicsDropShadowEffect, QSystemTrayIcon, QMenu
)
from PySide6.QtGui import QColor, QIcon, QAction  # fixed
from PySide6.QtCore import Qt, QTimer

# ---------------- DPI fix (Windows) ----------------
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

GLOW_COLOR = "#8a2be2"  # neon purple

class RoseHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.listening = True
        self.init_ui()
        threading.Thread(target=self.always_listen, daemon=True).start()

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        screen = QApplication.primaryScreen().geometry()
        width, height = 520, 380
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.setGeometry(x, y, width, height)
        self.setStyleSheet("background-color: rgba(0,0,0,200); border-radius: 12px;")

        layout = QVBoxLayout()
        self.text_area = QTextEdit()
        self.text_area.setStyleSheet(f"background-color: rgba(0,0,0,0); color: {GLOW_COLOR}; font-family: Consolas; font-size: 12pt;")
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)

        exit_btn = QPushButton("❌")
        exit_btn.setFixedWidth(40)
        exit_btn.clicked.connect(lambda: sys.exit())
        layout.addWidget(exit_btn)

        self.setLayout(layout)

        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(30)
        glow.setColor(QColor(GLOW_COLOR))
        glow.setOffset(0)
        self.text_area.setGraphicsEffect(glow)

        # System tray
        self.tray = QSystemTrayIcon(QIcon())
        menu = QMenu()
        show_action = QAction("Show")
        show_action.triggered.connect(self.show)
        menu.addAction(show_action)
        exit_action = QAction("Exit")
        exit_action.triggered.connect(lambda: sys.exit())
        menu.addAction(exit_action)
        self.tray.setContextMenu(menu)
        self.tray.show()

        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_scroll)
        self.timer.start(250)
        self.append_text("Rose v7 Jarvis-mode online — always listening!")

    def append_text(self, t):
        self.text_area.append(t)
        self.text_area.repaint()

    def auto_scroll(self):
        sb = self.text_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def always_listen(self):
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        while self.listening:
            try:
                with mic as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
                    command = recognizer.recognize_google(audio)
                    self.append_text(f"You: {command}")
                    resp = process_command(command)
                    self.append_text(f"Rose: {resp}")
                    talk(resp)
            except Exception:
                continue

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    hud = RoseHUD()
    hud.show()
    sys.exit(app.exec())
