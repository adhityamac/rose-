import sys, asyncio, threading, webbrowser, platform, subprocess, os
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton
from PySide6.QtGui import QFont, QPainter, QLinearGradient, QColor, QBrush
import speech_recognition as sr
import edge_tts

# ------------------ GLOBALS ------------------
LISTENING = True
CURRENT_TEXT = ""
vlc_process = None  # Track VLC/other TTS process

# ------------------ TTS ------------------
async def speak_text(text: str):
    """Speak asynchronously using Edge-TTS"""
    global vlc_process
    communicate = edge_tts.Communicate(text, "en-US-JennyNeural")
    await communicate.save("speech.mp3")
    if platform.system() == "Windows":
        vlc_process = subprocess.Popen(["powershell", "-c", "Start-Process", "speech.mp3"], shell=True)
    else:
        vlc_process = subprocess.Popen(["afplay", "speech.mp3"])

def speak(text):
    threading.Thread(target=lambda: asyncio.run(speak_text(text)), daemon=True).start()

# ------------------ YOUTUBE AUTOPLAY ------------------
def play_youtube_song(song: str):
    query = song.replace(" ", "+")
    url = f"https://www.youtube.com/results?search_query={query}"
    webbrowser.open(url)

# ------------------ SYSTEM COMMANDS ------------------
def adjust_volume(action: str):
    if platform.system() == "Windows":
        if action == "up":
            os.system("nircmd changesysvolume 5000")  # increase volume
        elif action == "down":
            os.system("nircmd changesysvolume -5000")  # decrease volume
        elif action == "mute":
            os.system("nircmd mutesysvolume 1")
        elif action == "unmute":
            os.system("nircmd mutesysvolume 0")
    else:
        # macOS/Linux placeholder
        pass

def system_action(action: str):
    if platform.system() == "Windows":
        if action == "shutdown":
            os.system("shutdown /s /t 1")
        elif action == "restart":
            os.system("shutdown /r /t 1")
    else:
        # macOS/Linux placeholder
        pass

# ------------------ VOICE COMMAND ------------------
def listen_loop(hud_ref):
    global CURRENT_TEXT
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    while LISTENING:
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, phrase_time_limit=5)
            command = recognizer.recognize_google(audio)
            CURRENT_TEXT = command.lower()
            handle_command(CURRENT_TEXT, hud_ref)
        except Exception:
            continue

def handle_command(cmd: str, hud_ref):
    """Parse commands and execute"""
    print("Heard:", cmd)
    if cmd.strip() == "":
        return
    hud_ref.update_response(f"You said: {cmd}")

    # ---- Play YouTube Song ----
    if "play" in cmd and "youtube" in cmd:
        song = cmd.replace("play", "").replace("youtube", "").strip()
        if song:
            speak(f"Playing {song} on YouTube")
            hud_ref.update_response(f"Playing {song} on YouTube...")
            play_youtube_song(song)
        else:
            speak("Opening YouTube")
            hud_ref.update_response("Opening YouTube...")
            webbrowser.open("https://www.youtube.com")

    # ---- Volume Control ----
    elif "volume up" in cmd:
        adjust_volume("up")
        speak("Volume increased")
        hud_ref.update_response("Volume increased")
    elif "volume down" in cmd:
        adjust_volume("down")
        speak("Volume decreased")
        hud_ref.update_response("Volume decreased")
    elif "mute" in cmd:
        adjust_volume("mute")
        speak("Volume muted")
        hud_ref.update_response("Volume muted")
    elif "unmute" in cmd:
        adjust_volume("unmute")
        speak("Volume unmuted")
        hud_ref.update_response("Volume unmuted")

    # ---- System Commands ----
    elif "shutdown" in cmd:
        speak("Shutting down system")
        hud_ref.update_response("Shutting down system...")
        system_action("shutdown")
    elif "restart" in cmd:
        speak("Restarting system")
        hud_ref.update_response("Restarting system...")
        system_action("restart")

    # ---- Default Response ----
    else:
        speak(f"You said: {cmd}")
        hud_ref.update_response(f"You said: {cmd}")

# ------------------ DRAGGABLE NEON HUD ------------------
class NeonHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(500, 300)

        # ------------------ Neon Text Label ------------------
        self.label = QLabel("ROSE", self)
        self.label.setFont(QFont("Arial", 28, QFont.Bold))
        self.label.setStyleSheet("color: white;")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.resize(480, 50)
        self.label.move(10, 40)

        # ------------------ Response Text ------------------
        self.response_label = QLabel("", self)
        self.response_label.setFont(QFont("Arial", 16))
        self.response_label.setStyleSheet("color: white;")
        self.response_label.setAlignment(Qt.AlignCenter)
        self.response_label.resize(480, 100)
        self.response_label.move(10, 120)

        # ------------------ Mac-style buttons (LEFT) ------------------
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

        # ------------------ Background Animation ------------------
        self.gradient_offset = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_bg)
        self.timer.start(50)

        # Draggable
        self.old_pos = self.pos()

    def close_app(self):
        global vlc_process
        if vlc_process:
            vlc_process.kill()
        self.close()

    # ------------------ Update Response ------------------
    def update_response(self, text: str):
        self.response_label.setText(text)

    # ------------------ Dragging ------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPosition().toPoint()

    # ------------------ Background Animation ------------------
    def animate_bg(self):
        self.gradient_offset += 0.01
        if self.gradient_offset > 1:
            self.gradient_offset = 0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        # Animated gradient background
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt((0 + self.gradient_offset) % 1, QColor(120, 0, 255))
        grad.setColorAt((0.5 + self.gradient_offset) % 1, QColor(200, 0, 255))
        grad.setColorAt((1 + self.gradient_offset) % 1, QColor(120, 0, 255))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 20, 20)

        # Neon glow for ROSE
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
    global LISTENING
    app = QApplication(sys.argv)
    hud = NeonHUD()
    hud.show()

    # Start background voice listener
    threading.Thread(target=listen_loop, args=(hud,), daemon=True).start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
