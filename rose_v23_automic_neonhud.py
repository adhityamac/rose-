import sys, asyncio, threading, webbrowser, platform, subprocess, os, random
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton
from PySide6.QtGui import QFont, QPainter, QLinearGradient, QColor, QBrush, QIcon, QPixmap
import speech_recognition as sr
import edge_tts

# ------------------ GLOBALS ------------------
LISTENING = True
CURRENT_TEXT = ""
USE_VLC = False  # Switch to True for VLC voice output, False for Edge-TTS
vlc_process = None

# ------------------ TTS ------------------
async def speak_text(text: str):
    global vlc_process
    if USE_VLC:
        # VLC Option
        with open("tts.txt", "w") as f:
            f.write(text)
        if platform.system() == "Windows":
            vlc_process = subprocess.Popen(["powershell", "-c", f'Start-Process vlc --play-and-exit --qt-start-minimized "tts.txt"'], shell=True)
        else:
            vlc_process = subprocess.Popen(["vlc", "--play-and-exit", "tts.txt"])
    else:
        # Edge-TTS Option
        communicate = edge_tts.Communicate(text, "en-US-JennyNeural")
        await communicate.save("speech.mp3")
        if platform.system() == "Windows":
            subprocess.Popen(["powershell", "-c", "Start-Process", "speech.mp3"], shell=True)
        else:
            subprocess.Popen(["afplay", "speech.mp3"])

def speak(text):
    threading.Thread(target=lambda: asyncio.run(speak_text(text)), daemon=True).start()

# ------------------ YouTube Auto-Play ------------------
def play_youtube_song(song):
    try:
        search_query = song.replace(" ", "+")
        url = f"https://www.youtube.com/results?search_query={search_query}"
        webbrowser.open(url)
    except:
        pass

# ------------------ Voice Command ------------------
def listen_loop(hud_ref):
    global CURRENT_TEXT
    recognizer = sr.Recognizer()
    mic = None

    # Auto-detect mic
    try:
        mic = sr.Microphone()
        print("Using default microphone:", sr.Microphone.list_microphone_names()[0])
    except:
        print("No microphone detected!")
        return

    while LISTENING:
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, phrase_time_limit=5)
            command = recognizer.recognize_google(audio)
            CURRENT_TEXT = command.lower()
            handle_command(CURRENT_TEXT, hud_ref)
        except Exception as e:
            print("Microphone/listen error:", e)
            continue

# ------------------ Command Handler ------------------
def handle_command(cmd: str, hud_ref):
    if cmd.strip() == "":
        return
    print("Heard:", cmd)
    hud_ref.update_response(f"You said: {cmd}")

    # Song playback
    if "play" in cmd or "youtube" in cmd:
        song = cmd.replace("play", "").replace("youtube", "").strip()
        if song:
            hud_ref.update_response(f"Playing {song} on YouTube...")
            speak(f"Playing {song} on YouTube")
            play_youtube_song(song)
        else:
            hud_ref.update_response("Opening YouTube...")
            speak("Opening YouTube")
            webbrowser.open("https://www.youtube.com")

    # System commands
    elif "shutdown" in cmd:
        hud_ref.update_response("Shutting down system...")
        speak("Shutting down system")
        if platform.system() == "Windows":
            os.system("shutdown /s /t 1")
    elif "restart" in cmd:
        hud_ref.update_response("Restarting system...")
        speak("Restarting system")
        if platform.system() == "Windows":
            os.system("shutdown /r /t 1")
    elif "volume up" in cmd:
        hud_ref.update_response("Volume up")
        speak("Volume increased")
        os.system("nircmd.exe changesysvolume 2000")
    elif "volume down" in cmd:
        hud_ref.update_response("Volume down")
        speak("Volume decreased")
        os.system("nircmd.exe changesysvolume -2000")

    # Greetings
    elif "hello" in cmd or "hi" in cmd:
        hud_ref.update_response("Hello! How can I help you?")
        speak("Hello! How can I help you?")

    else:
        speak(f"You said: {cmd}")

# ------------------ Neon HUD ------------------
class NeonHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(500, 300)
        self.setWindowTitle("Rose - Your Healer")

        # Set rose icon
        self.setWindowIcon(QIcon("rose_icon.png"))  # Place peach rose image as rose_icon.png

        # Neon Title
        self.label = QLabel("ROSE", self)
        self.label.setFont(QFont("Arial", 32, QFont.Bold))
        self.label.setStyleSheet("color: white;")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.resize(480, 50)
        self.label.move(10, 40)

        # Response Text
        self.response_label = QLabel("Hi, I'm Rose, your healer...", self)
        self.response_label.setFont(QFont("Arial", 16))
        self.response_label.setStyleSheet("color: white;")
        self.response_label.setAlignment(Qt.AlignCenter)
        self.response_label.resize(480, 100)
        self.response_label.move(10, 120)

        # Mac-style Buttons (Top Left)
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
        self.max_btn.clicked.connect(self.showMaximized)

        # Background Animation
        self.gradient_offset = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_bg)
        self.timer.start(40)

        # Waveform Animation Timer
        self.wave_timer = QTimer()
        self.wave_timer.timeout.connect(self.animate_waveform)
        self.wave_timer.start(100)
        self.wave_height = [random.randint(5, 15) for _ in range(10)]

        # Drag
        self.old_pos = self.pos()

        # Initial Greeting
        speak("Hi, I'm Rose, your healer...")

    def close_app(self):
        global vlc_process
        if vlc_process:
            vlc_process.kill()
        self.close()

    def update_response(self, text: str):
        self.response_label.setText(text)

    # Dragging
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPosition().toPoint()

    # Background Animation
    def animate_bg(self):
        self.gradient_offset += 0.01
        if self.gradient_offset > 1:
            self.gradient_offset = 0
        self.update()

    # Waveform Animation
    def animate_waveform(self):
        self.wave_height = [random.randint(5, 15) for _ in range(10)]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        # Gradient Background
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt((0 + self.gradient_offset) % 1, QColor(120, 0, 255))
        grad.setColorAt((0.5 + self.gradient_offset) % 1, QColor(200, 0, 255))
        grad.setColorAt((1 + self.gradient_offset) % 1, QColor(120, 0, 255))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 20, 20)

        # Neon Glow Text
        for i in range(1, 6):
            color = QColor(255, 255, 255, 50 - i*8)
            painter.setPen(color)
            painter.setFont(QFont("Arial", 32 + i, QFont.Bold))
            painter.drawText(self.label.geometry(), Qt.AlignCenter, self.label.text())
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 32, QFont.Bold))
        painter.drawText(self.label.geometry(), Qt.AlignCenter, self.label.text())

        # Waveform
        painter.setPen(QColor(255, 255, 255))
        x_start = 150
        for i, h in enumerate(self.wave_height):
            painter.drawLine(x_start + i * 12, 260, x_start + i * 12, 260 - h)

# ------------------ MAIN ------------------
def main():
    global LISTENING
    app = QApplication(sys.argv)
    hud = NeonHUD()
    hud.show()
    threading.Thread(target=listen_loop, args=(hud,), daemon=True).start()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
