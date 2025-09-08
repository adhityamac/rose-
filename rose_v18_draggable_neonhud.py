# rose_v18_draggable_neonhud.py
import sys, asyncio, threading, webbrowser
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton
from PySide6.QtGui import QFont, QPainter, QLinearGradient, QColor, QBrush
import speech_recognition as sr
import edge_tts

# ------------------ GLOBALS ------------------
LISTENING = True
CURRENT_TEXT = ""

# ------------------ TTS ------------------
async def speak_text(text: str):
    """Use Edge-TTS to speak asynchronously (no VLC needed)"""
    communicate = edge_tts.Communicate(text, "en-US-JennyNeural")
    await communicate.save("speech.mp3")
    import subprocess, platform
    if platform.system() == "Windows":
        subprocess.Popen(["powershell", "-c", "Start-Process", "speech.mp3"], shell=True)
    else:
        subprocess.Popen(["afplay", "speech.mp3"])  # macOS

def speak(text):
    threading.Thread(target=lambda: asyncio.run(speak_text(text)), daemon=True).start()

# ------------------ VOICE COMMAND ------------------
def listen_loop():
    global CURRENT_TEXT
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    while LISTENING:
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source)
            command = recognizer.recognize_google(audio)
            CURRENT_TEXT = command.lower()
            handle_command(CURRENT_TEXT)
        except Exception:
            continue

def handle_command(cmd: str):
    """Parse commands and execute"""
    print("Heard:", cmd)
    if "youtube" in cmd or "play" in cmd:
        speak("Opening YouTube")
        webbrowser.open("https://www.youtube.com")
    elif "notepad" in cmd:
        speak("Opening Notepad")
        import os
        os.system("notepad")
    elif "hello" in cmd:
        speak("Hello! How can I help you today?")
    else:
        speak(f"You said: {cmd}")

# ------------------ DRAGGABLE NEON HUD ------------------
class NeonHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(500, 300)

        # ------------------ Neon Text Label ------------------
        self.label = QLabel("Rose Activated!", self)
        self.label.setFont(QFont("Arial", 22, QFont.Bold))
        self.label.setStyleSheet("color: #DA00FF;")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.resize(480, 50)
        self.label.move(10, 120)

        # ------------------ Mac-style buttons ------------------
        self.close_btn = QPushButton(self)
        self.close_btn.setStyleSheet("background-color: red; border-radius: 7px;")
        self.close_btn.setFixedSize(14, 14)
        self.close_btn.move(10, 10)
        self.close_btn.clicked.connect(self.close)

        self.min_btn = QPushButton(self)
        self.min_btn.setStyleSheet("background-color: yellow; border-radius: 7px;")
        self.min_btn.setFixedSize(14, 14)
        self.min_btn.move(30, 10)
        self.min_btn.clicked.connect(self.showMinimized)

        self.max_btn = QPushButton(self)
        self.max_btn.setStyleSheet("background-color: green; border-radius: 7px;")
        self.max_btn.setFixedSize(14, 14)
        self.max_btn.move(50, 10)
        self.max_btn.clicked.connect(lambda: self.showMaximized())

        # ------------------ Background Animation ------------------
        self.gradient_offset = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_bg)
        self.timer.start(50)

        # Draggable
        self.old_pos = self.pos()

        # Greeting
        QTimer.singleShot(1000, lambda: speak("Hello! I am Rose. How can I help you today?"))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPosition().toPoint()

    def animate_bg(self):
        self.gradient_offset += 0.01
        if self.gradient_offset > 1:
            self.gradient_offset = 0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        # Animated gradient background
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt((0 + self.gradient_offset) % 1, QColor(80, 0, 255))
        grad.setColorAt((0.5 + self.gradient_offset) % 1, QColor(150, 0, 255))
        grad.setColorAt((1 + self.gradient_offset) % 1, QColor(80, 0, 255))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 20, 20)

        # Neon glow around text
        for i in range(1, 6):
            color = QColor(218, 0, 255, 50 - i*8)
            painter.setPen(color)
            painter.setFont(QFont("Arial", 22 + i, QFont.Bold))
            painter.drawText(self.label.geometry(), Qt.AlignCenter, self.label.text())

        painter.setPen(QColor(218, 0, 255))
        painter.setFont(QFont("Arial", 22, QFont.Bold))
        painter.drawText(self.label.geometry(), Qt.AlignCenter, self.label.text())

# ------------------ MAIN ------------------
def main():
    global LISTENING
    app = QApplication(sys.argv)
    hud = NeonHUD()
    hud.show()

    # Start background voice listener
    threading.Thread(target=listen_loop, daemon=True).start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
