# rose_v21_autoplay_neonhud.py
import sys, asyncio, threading, webbrowser, platform, subprocess, os
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton
from PySide6.QtGui import QFont, QPainter, QLinearGradient, QColor, QBrush
import speech_recognition as sr
import edge_tts
from pytube import Search

# ------------------ GLOBALS ------------------
LISTENING = True
CURRENT_TEXT = ""

# ------------------ TTS ------------------
async def speak_text(text: str):
    communicate = edge_tts.Communicate(text, "en-US-JennyNeural")
    await communicate.save("speech.mp3")
    if platform.system() == "Windows":
        os.system("start wmplayer speech.mp3")  # Uses Windows Media Player
    else:
        subprocess.Popen(["afplay", "speech.mp3"])

def speak(text):
    threading.Thread(target=lambda: asyncio.run(speak_text(text)), daemon=True).start()

# ------------------ VOICE COMMAND LISTENER ------------------
def listen_loop(hud_ref):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    while LISTENING:
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, phrase_time_limit=5)
            command = recognizer.recognize_google(audio)
            command = command.lower().strip()
            if command:
                handle_command(command, hud_ref)
        except Exception:
            continue

# ------------------ PLAY YOUTUBE SONG ------------------
def play_youtube_song(song):
    try:
        search = Search(song)
        first_result = search.results[0]
        video_url = first_result.watch_url
        webbrowser.open(video_url)
    except Exception as e:
        print("YouTube error:", e)

# ------------------ HANDLE COMMANDS ------------------
def handle_command(cmd: str, hud_ref):
    print("Heard:", cmd)
    hud_ref.update_response(f"You said: {cmd}")

    # PLAY SONG ON YOUTUBE
    if "play" in cmd:
        song = cmd.replace("play", "").replace("on youtube", "").strip()
        if song:
            speak(f"Playing {song} on YouTube")
            hud_ref.update_response(f"Playing {song} on YouTube...")
            play_youtube_song(song)
            return

    # VOLUME CONTROL
    if "volume up" in cmd:
        os.system("nircmd setsysvolume 65535")
        speak("Volume increased")
        hud_ref.update_response("Volume increased")
        return
    if "volume down" in cmd:
        os.system("nircmd setsysvolume 10000")
        speak("Volume decreased")
        hud_ref.update_response("Volume decreased")
        return
    if "mute" in cmd:
        os.system("nircmd mutesysvolume 1")
        speak("Volume muted")
        hud_ref.update_response("Volume muted")
        return
    if "unmute" in cmd:
        os.system("nircmd mutesysvolume 0")
        speak("Volume unmuted")
        hud_ref.update_response("Volume unmuted")
        return

    # SYSTEM COMMANDS
    if "notepad" in cmd:
        speak("Opening Notepad")
        hud_ref.update_response("Opening Notepad...")
        os.system("notepad")
        return
    if "calculator" in cmd:
        speak("Opening Calculator")
        hud_ref.update_response("Opening Calculator...")
        os.system("calc")
        return
    if "shutdown" in cmd:
        speak("Shutting down your PC")
        hud_ref.update_response("Shutting down your PC...")
        os.system("shutdown /s /t 1")
        return

    # DEFAULT RESPONSE
    speak(f"You said: {cmd}")
    hud_ref.update_response(f"You said: {cmd}")

# ------------------ NEON HUD ------------------
class NeonHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(500, 300)

        # Neon Text Label
        self.label = QLabel("ROSE", self)
        self.label.setFont(QFont("Arial", 28, QFont.Bold))
        self.label.setStyleSheet("color: white;")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.resize(480, 50)
        self.label.move(10, 40)

        # Response Text
        self.response_label = QLabel("Hi, I’m Rose, your healer...", self)
        self.response_label.setFont(QFont("Arial", 16))
        self.response_label.setStyleSheet("color: white;")
        self.response_label.setAlignment(Qt.AlignCenter)
        self.response_label.resize(480, 100)
        self.response_label.move(10, 120)

        # Mac-style buttons
        self.close_btn = QPushButton(self)
        self.close_btn.setStyleSheet("background-color: red; border-radius: 7px;")
        self.close_btn.setFixedSize(14, 14)
        self.close_btn.move(10, 10)
        self.close_btn.clicked.connect(self.close_app)

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

        # Background Animation
        self.gradient_offset = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_bg)
        self.timer.start(50)

        # Draggable
        self.old_pos = self.pos()

    def close_app(self):
        self.close()

    def update_response(self, text: str):
        self.response_label.setText(text)

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
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt((0 + self.gradient_offset) % 1, QColor(120, 0, 255))
        grad.setColorAt((0.5 + self.gradient_offset) % 1, QColor(200, 0, 255))
        grad.setColorAt((1 + self.gradient_offset) % 1, QColor(120, 0, 255))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 20, 20)

        for i in range(1, 6):
            color = QColor(255, 255, 255, 50 - i*8)
            painter.setPen(color)
            painter.setFont(QFont("Arial", 28 + i, QFont.Bold))
            painter.drawText(self.label.geometry(), Qt.AlignCenter, self.label.text())
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 28, QFont.Bold))
        painter.drawText(self.label.geometry(), Qt.AlignCenter, self.label.text())

# ------------------ MAIN ------------------
def main():
    app = QApplication(sys.argv)
    hud = NeonHUD()
    hud.show()

    threading.Thread(target=listen_loop, args=(hud,), daemon=True).start()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
