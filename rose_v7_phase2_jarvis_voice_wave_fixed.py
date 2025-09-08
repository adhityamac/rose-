# rose_v7_phase2_jarvis_voice_wave_fixed.py
import os, sys, time, json, threading, requests, pyttsx3, speech_recognition as sr
import wikipedia, pyjokes, ctypes

# -----------------------------
# Patch pywhatkit
# -----------------------------
try:
    import pywhatkit.core.core as core
    core.check_connection = lambda: True
except:
    pass

try:
    import pywhatkit
except:
    pywhatkit = None

# -----------------------------
# Internet check
# -----------------------------
def is_online(url="https://google.com", timeout=5):
    try:
        requests.get(url, timeout=timeout)
        return True
    except:
        return False

# -----------------------------
# TTS with interrupt support
# -----------------------------
engine = pyttsx3.init()
engine.setProperty("rate", 160)
mic_lock = threading.Lock()
speaking = False

def talk(text):
    global speaking
    with mic_lock:    # prevent listening while talking
        speaking = True
        engine.say(text)
        engine.runAndWait()
        speaking = False

# -----------------------------
# Chat memory
# -----------------------------
CHAT_HISTORY = []
MAX_MEMORY = 10

# -----------------------------
# Command processing
# -----------------------------
def process_command(command):
    command = command.lower()
    global CHAT_HISTORY
    if "open" in command:
        try:
            if "brave" in command:
                path = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
                os.startfile(path if os.path.exists(path) else "https://www.google.com")
            elif "chrome" in command:
                os.startfile("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
            elif "vscode" in command:
                os.startfile(f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe")
            else:
                os.startfile("https://www.google.com")
            return "Opened app"
        except Exception as e:
            return f"Failed to open: {e}"

    if "play" in command:
        song = command.replace("play", "").strip()
        if pywhatkit:
            pywhatkit.playonyt(song)
            return f"Playing {song} on YouTube"
        return f"Cannot play {song}, pywhatkit unavailable."

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

    if "bye" in command or "stop" in command:
        talk("Goodbye")
        sys.exit()

    CHAT_HISTORY.append((command, f"I heard: {command}"))
    return f"I heard: {command}"

# -----------------------------
# GUI
# -----------------------------
from PySide6.QtWidgets import QApplication, QWidget, QTextEdit, QVBoxLayout, QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QBrush

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

class RoseHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(400,200,520,380)
        self.setStyleSheet("background-color: rgba(0,0,0,200); border-radius: 12px;")

        layout = QVBoxLayout()
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("background-color: rgba(0,0,0,0); color: #BF00FF; font-family: Consolas; font-size: 12pt;")
        layout.addWidget(self.text_area)

        exit_btn = QPushButton("Exit")
        exit_btn.setStyleSheet("background-color: rgba(255,0,0,160); color: white; font-weight: bold;")
        exit_btn.clicked.connect(lambda: sys.exit())
        layout.addWidget(exit_btn)

        self.setLayout(layout)

        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(30)
        glow.setColor(QColor("#BF00FF"))
        glow.setOffset(0)
        self.text_area.setGraphicsEffect(glow)

        # Pulsing indicator variables
        self.listening_indicator = False
        self.pulse_value = 0
        self.pulse_direction = 1

        # Speaking bars
        self.num_bars = 3
        self.bar_heights = [10]*self.num_bars

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_visuals)
        self.timer.start(50)

        self.append_text("🌹 Rose v7 online — say 'rose' then your command.")

    def append_text(self, text):
        self.text_area.append(text)
        self.text_area.repaint()

    def update_visuals(self):
        global speaking
        if self.listening_indicator:
            self.pulse_value += self.pulse_direction * 0.05
            if self.pulse_value >= 1: self.pulse_value = 1; self.pulse_direction = -1
            elif self.pulse_value <= 0.2: self.pulse_value = 0.2; self.pulse_direction = 1
        else:
            self.pulse_value = 0; self.pulse_direction = 1

        if speaking:
            import random
            self.bar_heights = [random.randint(10,50) for _ in range(self.num_bars)]
        else:
            self.bar_heights = [10]*self.num_bars

        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.listening_indicator:
            color = QColor(0,255,255)
            color.setAlphaF(self.pulse_value)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(self.width()-30,10,15,15)

        bar_width = 10
        spacing = 8
        base_x = 20
        base_y = self.height() - 30
        for i,h in enumerate(self.bar_heights):
            painter.setBrush(QBrush(QColor(191,0,255)))
            painter.drawRect(base_x + i*(bar_width+spacing), base_y - h, bar_width, h)

# -----------------------------
# Voice Assistant
# -----------------------------
class VoiceAssistant:
    def __init__(self, hud):
        self.hud = hud
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.listening = True
        self.command_thread = None
        threading.Thread(target=self.listen_loop, daemon=True).start()

    def listen_loop(self):
        while self.listening:
            try:
                self.hud.listening_indicator = True
                with mic_lock:   # single mic context
                    with self.microphone as source:
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                text = self.recognizer.recognize_google(audio).lower()
                if "rose" in text:
                    command = text.replace("rose","").strip()
                    if command:
                        if self.command_thread and self.command_thread.is_alive():
                            engine.stop()
                        self.command_thread = threading.Thread(target=self.handle_command, args=(command,), daemon=True)
                        self.command_thread.start()
            except:
                continue
            finally:
                self.hud.listening_indicator = False

    def handle_command(self, command):
        self.hud.append_text(f"You said: {command}")
        self.hud.append_text("Rose: thinking...")
        resp = process_command(command)
        self.hud.append_text(f"Rose: {resp}")
        talk(resp)

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    hud = RoseHUD()
    hud.show()

    assistant = VoiceAssistant(hud)
    talk("Hello Adhi, I am Rose. Ready to assist you!")

    sys.exit(app.exec())
