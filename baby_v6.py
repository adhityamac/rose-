import sys
import os
import time
import requests
import pyttsx3
import speech_recognition as sr
import pywhatkit
import wikipedia
import pyjokes
import ctypes
from PySide6.QtWidgets import QApplication, QWidget, QTextEdit, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QColor , QFont
from PySide6.QtWidgets import QGraphicsDropShadowEffect


# ---------------- CONFIG ----------------
ZAI_API_KEY = "YOUR_ZAI_API_KEY"  # Replace if you have ZAI key
WAKE_WORD = "rose"  # Your wake word
GLOW_COLOR = "#00ffff"  # cyan glow

# ---------------- DPI FIX ----------------
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

# ---------------- VOICE SETUP ----------------
engine = pyttsx3.init()
listener = sr.Recognizer()

def talk(text):
    engine.say(text)
    engine.runAndWait()

# ---------------- AI FUNCTION (ZAI + Free Fallback) ----------------
def ask_ai(question):
    try:
        if ZAI_API_KEY and ZAI_API_KEY != "YOUR_ZAI_API_KEY":
            url = "https://z.ai/api/chat"
            headers = {
                "Authorization": f"Bearer {ZAI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {"messages": [{"role": "user", "content": question}]}
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
        # Free fallback
        return free_ai_response(question)
    except:
        return free_ai_response(question)

def free_ai_response(query):
    # Simple rule-based fallback
    if "who are you" in query:
        return "I am Rose, your AI assistant."
    elif "how are you" in query:
        return "I'm always good when you're around."
    elif "your name" in query:
        return "My name is Rose, just like you named me."
    else:
        return f"I heard you say: {query}"

# ---------------- COMMAND PROCESSING ----------------
def process_command(command):
    command = command.lower()
    response = ""
    if "play" in command:
        song = command.replace("play", "").strip()
        talk(f"Playing {song}")
        pywhatkit.playonyt(song)
        response = f"Playing {song} on YouTube"
    elif "wikipedia" in command:
        topic = command.replace("wikipedia", "").strip()
        info = wikipedia.summary(topic, sentences=2)
        talk(info)
        response = info
    elif "joke" in command:
        joke = pyjokes.get_joke()
        talk(joke)
        response = joke
    elif "open" in command:
        app_name = command.replace("open", "").strip()
        if "chrome" in app_name:
            os.startfile("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
            response = "Opening Chrome"
        elif "vscode" in app_name:
            os.startfile("C:\\Users\\Adhi\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe")
            response = "Opening VSCode"
        elif "calculator" in app_name:
            os.system("calc")
            response = "Opening Calculator"
        else:
            response = "App not found"
            talk("App not found")
    elif "shutdown" in command:
        talk("Shutting down PC")
        os.system("shutdown /s /t 5")
        response = "Shutting down PC"
    elif "bye" in command or "stop" in command:
        talk("Goodbye! Exiting now.")
        sys.exit()
    else:
        response = ask_ai(command)
        talk(response)
    return response

# ---------------- LISTENER THREAD ----------------
class ListenerThread(QThread):
    heard_signal = Signal(str)

    def run(self):
        while True:
            try:
                with sr.Microphone() as source:
                    listener.adjust_for_ambient_noise(source)
                    audio = listener.listen(source, timeout=5, phrase_time_limit=7)
                    command = listener.recognize_google(audio).lower()
                    if WAKE_WORD in command:
                        command = command.replace(WAKE_WORD, "").strip()
                        self.heard_signal.emit(command)
            except:
                continue

# ---------------- HUD ----------------
class BabyHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Center HUD on screen
        screen = app.primaryScreen().geometry()
        width = 500
        height = 350
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.setGeometry(x, y, width, height)
        self.setStyleSheet("background-color: rgba(0,0,0,120); border-radius: 15px;")

        layout = QVBoxLayout()

        # Text area for logs
        self.text_area = QTextEdit()
        self.text_area.setStyleSheet(f"background-color: rgba(0,0,0,0); color: {GLOW_COLOR}; font-family: Consolas; font-size: 12pt;")
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)

        # Exit button
        exit_btn = QPushButton("Exit")
        exit_btn.setStyleSheet("background-color: rgba(255,0,0,180); color: white; font-weight: bold;")
        exit_btn.clicked.connect(lambda: sys.exit())
        layout.addWidget(exit_btn)

        self.setLayout(layout)

        # Start listener thread
        self.listener_thread = ListenerThread()
        self.listener_thread.heard_signal.connect(self.handle_command)
        self.listener_thread.start()

        talk("Rose v6 online. Waiting for wake word...")
        self.text_area.append("Rose v6 online. Waiting for wake word...\n")

        # Timer for scrolling effect
        self.timer = QTimer()
        self.timer.timeout.connect(self.scroll_text)
        self.timer.start(200)

    def handle_command(self, command):
        self.text_area.append(f"You said: {command}")
        response = process_command(command)
        if response:
            self.text_area.append(f"Rose: {response}")

    def scroll_text(self):
        self.text_area.verticalScrollBar().setValue(self.text_area.verticalScrollBar().maximum())

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    hud = BabyHUD()
    hud.show()
    sys.exit(app.exec())
