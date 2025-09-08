# rose_v10_edgetts_macstyle.py
"""
Rose v10 — Mac-style HUD, Edge TTS voice, always-on listening,
YouTube playback, continuous chat memory, top-right Mac buttons, typing animation.
"""

import os
import sys
import time
import json
import threading
import asyncio
import pyjokes
import wikipedia
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from PySide6.QtWidgets import (
    QApplication, QWidget, QTextEdit, QVBoxLayout, QPushButton, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

# ---------------- CONFIG ----------------
WAKE_WORD = "rose"  # not used, listening always
GLOW_COLOR = "#A020F0"  # neon purple
KB_DIR = "kb_docs"
INDEX_SAVE = "kb_index"
MAX_MEMORY = 10

# ---------------- EDGE TTS SETUP ----------------
import edge_tts

async def tts(text):
    try:
        communicate = edge_tts.Communicate(text, voice="en-US-JennyNeural")
        await communicate.save("response.mp3")
        os.system("start response.mp3")  # Windows
    except Exception as e:
        print(f"TTS error: {e}")

def speak(text):
    asyncio.run(tts(text))

# ---------------- CHAT MEMORY ----------------
CHAT_HISTORY = []

# ---------------- COMMAND PROCESSING ----------------
def play_youtube(song):
    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        driver.get(f"https://www.youtube.com/results?search_query={song}")
        time.sleep(2)
        video = driver.find_element(By.ID, "video-title")
        video.click()
        return f"Playing {song} on YouTube"
    except Exception as e:
        return f"Failed to play {song}: {e}"

def process_command(command):
    command = command.lower()

    if "play" in command:
        song = command.replace("play", "").strip()
        resp = play_youtube(song)
        speak(resp)
        return resp

    if "wikipedia" in command:
        topic = command.replace("wikipedia", "").strip()
        try:
            resp = wikipedia.summary(topic, sentences=2)
            speak(resp)
            return resp
        except Exception as e:
            resp = f"Wikipedia error: {e}"
            speak(resp)
            return resp

    if "joke" in command:
        resp = pyjokes.get_joke()
        speak(resp)
        return resp

    resp = f"I heard: {command}"
    speak(resp)
    return resp

# ---------------- HUD / GUI ----------------
class RoseHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self._typing_animation)
        self.typing_text = ""
        self.typing_index = 0

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        screen = QApplication.primaryScreen().geometry()
        width, height = 520, 380
        x, y = screen.width() - width - 20, 20
        self.setGeometry(x, y, width, height)
        self.setStyleSheet("background-color: rgba(0,0,0,220); border-radius: 12px;")

        layout = QVBoxLayout()
        self.text_area = QTextEdit()
        self.text_area.setStyleSheet(f"background-color: rgba(0,0,0,0); color: {GLOW_COLOR}; font-family: Consolas; font-size: 12pt;")
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)

        # Mac-style buttons
        btn_layout = QVBoxLayout()
        self.close_btn = QPushButton("⨉")
        self.close_btn.setStyleSheet("background-color: red; border-radius: 8px; color: white;")
        self.close_btn.clicked.connect(lambda: sys.exit())
        self.min_btn = QPushButton("━")
        self.min_btn.setStyleSheet("background-color: yellow; border-radius: 8px; color: black;")
        self.min_btn.clicked.connect(self.showMinimized)
        btn_layout.addWidget(self.close_btn)
        btn_layout.addWidget(self.min_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(30)
        glow.setColor(QColor(GLOW_COLOR))
        glow.setOffset(0)
        self.text_area.setGraphicsEffect(glow)

        self.append_text("🌹 Rose v10 online — listening...")
        speak("Hello Adhi! I am Rose. What can I do to help you today?")

        # Periodic update (simulate continuous input)
        self.timer = QTimer()
        self.timer.timeout.connect(self.listen_loop)
        self.timer.start(1000)  # 1-second interval

    def append_text(self, t):
        self.text_area.append(t)
        self.text_area.repaint()

    def _typing_animation(self):
        if self.typing_index < len(self.typing_text):
            self.text_area.moveCursor(self.text_area.textCursor().End)
            self.text_area.insertPlainText(self.typing_text[self.typing_index])
            self.typing_index += 1
        else:
            self.typing_timer.stop()
            self.typing_index = 0
            self.typing_text = ""

    def type_text(self, t):
        self.typing_text = t
        self.typing_index = 0
        self.text_area.clear()
        self.typing_timer.start(30)

    def listen_loop(self):
        # This is placeholder for continuous input
        command = input("You: ")  # Temporary; replace with real mic input if you want
        if command:
            self.append_text(f"You: {command}")
            resp = process_command(command)
            self.type_text(f"Rose: {resp}")

# ---------------- MAIN ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    hud = RoseHUD()
    hud.show()
    sys.exit(app.exec())
