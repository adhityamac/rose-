# rose_v13_voice_jarvis.py
"""
Rose v13 — Voice-first, always-listening assistant with Mac-style UI.
- Always listens in background (pauses while speaking)
- Instant offline TTS via pyttsx3
- Mac-style circular buttons (top-left) with glow animation
- Animated gradient background
- HUD shows short history/status (no typing)
"""

import sys
import os
import time
import threading
import queue
import webbrowser
import requests
import wikipedia
import pyjokes
import pywhatkit

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QColor

import speech_recognition as sr
import pyttsx3

# ---------- Config ----------
HUD_WIDTH = 480
HUD_HEIGHT = 220
GLOW_COLOR = "#B24BFF"   # neon purple-ish
BG_BASE = (12, 12, 15)   # base RGB for animated gradient
LISTEN_ON_START = True
MIC_ADJUST_SECONDS = 0.6

# ---------- Global locks & queue ----------
mic_lock = threading.Lock()      # held while TTS plays to prevent listening
cmd_queue = queue.Queue()        # not strictly necessary, but useful for sequencing

# ---------- Signals ----------
class Communicate(QObject):
    add_status = Signal(str)       # add a short line to HUD
    set_listening = Signal(bool)   # update mic status indicator
comm = Communicate()

# ---------- TTS (pyttsx3) ----------
tts_engine = pyttsx3.init()
tts_engine.setProperty("rate", 150)

def speak(text: str):
    """Speak text in background, and ensure mic is paused while speaking."""
    def _run():
        try:
            # Acquire mic lock so listener won't capture our voice
            mic_lock.acquire()
            # speak (blocking)
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception as e:
            print("TTS error:", e)
        finally:
            # release mic lock so listener resumes
            if mic_lock.locked():
                mic_lock.release()
    t = threading.Thread(target=_run, daemon=True)
    t.start()

# ---------- Command processing ----------
def play_youtube_first(song: str) -> str:
    """Search YouTube, open first result (no Selenium)."""
    try:
        q = requests.utils.requote_uri(song)
        url = f"https://www.youtube.com/results?search_query={q}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            import re
            m = re.search(r"\/watch\?v=([A-Za-z0-9_-]{11})", r.text)
            if m:
                vid = m.group(1)
                webbrowser.open(f"https://www.youtube.com/watch?v={vid}")
                return f"Playing {song} on YouTube"
        # fallback: pywhatkit or open search page
        try:
            pywhatkit.playonyt(song)
            return f"Playing {song} on YouTube (fallback)"
        except Exception:
            webbrowser.open(url)
            return f"Opened YouTube search for {song}"
    except Exception as e:
        return f"Failed to play {song}: {e}"

def process_command(cmd: str) -> str:
    c = cmd.lower().strip()
    # simple conversational cases
    if any(w in c for w in ("hello", "hi", "hey")):
        return "Hey Adhi. How can I help?"
    if "time" in c and "what" in c or c.strip() == "time" or "what time" in c:
        return time.strftime("It's %I:%M %p right now.")
    if c.startswith("open "):
        target = c.replace("open ", "", 1).strip()
        if "youtube" in target:
            webbrowser.open("https://www.youtube.com")
            return "Opened YouTube."
        if "brave" in target:
            path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
            if os.path.exists(path):
                os.startfile(path); return "Opened Brave."
            else:
                webbrowser.open("https://www.google.com"); return "Brave not found, opened Google."
        if "chrome" in target:
            path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            if os.path.exists(path):
                os.startfile(path); return "Opened Chrome."
            else:
                webbrowser.open("https://www.google.com"); return "Chrome not found, opened Google."
        # default search
        webbrowser.open(f"https://www.google.com/search?q={requests.utils.requote_uri(target)}")
        return f"Searched the web for {target}."
    if c.startswith("play "):
        song = c.replace("play ", "", 1).strip()
        if song:
            return play_youtube_first(song)
        return "Tell me what you want me to play."
    if "wikipedia" in c:
        topic = c.replace("wikipedia", "").strip()
        try:
            summary = wikipedia.summary(topic, sentences=2)
            return summary
        except Exception as e:
            return f"Wikipedia error: {e}"
    if "joke" in c:
        return pyjokes.get_joke()
    if c in ("bye", "goodbye", "exit", "quit", "stop"):
        # goodbye spoken elsewhere, return text to show
        return "Goodbye"
    # default echo
    return f"I heard: {cmd}"

# ---------- Microphone listener (always-on) ----------
class ListenerThread(threading.Thread):
    def __init__(self, comm_obj: Communicate, start_listen=True):
        super().__init__(daemon=True)
        self.comm = comm_obj
        self.running = True
        self.listening = start_listen
        self.r = sr.Recognizer()

    def run(self):
        while self.running:
            if not self.listening:
                time.sleep(0.25)
                continue
            try:
                # Wait for mic_lock to be free, then use microphone
                with mic_lock:
                    with sr.Microphone() as source:
                        self.r.adjust_for_ambient_noise(source, duration=MIC_ADJUST_SECONDS)
                        audio = self.r.listen(source, timeout=6, phrase_time_limit=8)
                # recognize outside mic_lock so lock is brief
                try:
                    text = self.r.recognize_google(audio)
                except sr.UnknownValueError:
                    continue
                except Exception as e:
                    print("Recognition error:", e)
                    continue
                if text and text.strip():
                    self.comm.add_status.emit(f"You: {text}")
                    # process in worker so listener loop can continue
                    threading.Thread(target=self._handle, args=(text,), daemon=True).start()
            except Exception:
                # keep loop alive on errors (timeouts, OS errors)
                continue

    def _handle(self, text):
        # called in background thread
        resp = process_command(text)
        # show response on HUD immediately
        self.comm.add_status.emit(f"Rose: {resp}")
        # speak response (this will acquire mic_lock internally)
        if resp == "Goodbye":
            speak("Goodbye. Shutting down.")
            time.sleep(0.5)
            os._exit(0)
        else:
            speak(resp)

    def stop(self):
        self.running = False

# ---------- HUD (Qt) ----------
class RoseHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rose")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen.width() - HUD_WIDTH - 20, 20, HUD_WIDTH, HUD_HEIGHT)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._bg_phase = 0.0

        # Visual layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)

        # top bar with mac-like circular buttons (top-left)
        topbar = QHBoxLayout()
        topbar.setSpacing(8)
        # red close
        self.btn_close = QPushButton("", self)
        self.btn_close.setFixedSize(16, 16)
        self.btn_close.setStyleSheet("background-color:#FF5F57; border-radius:8px; border: 1px rgba(0,0,0,0.15);")
        self.btn_close.clicked.connect(self._close)
        topbar.addWidget(self.btn_close)
        # yellow minimize/hide
        self.btn_min = QPushButton("", self)
        self.btn_min.setFixedSize(16, 16)
        self.btn_min.setStyleSheet("background-color:#FFBD2E; border-radius:8px; border: 1px rgba(0,0,0,0.12);")
        self.btn_min.clicked.connect(self._hide)
        topbar.addWidget(self.btn_min)
        # green mic toggle
        self.btn_mic = QPushButton("", self)
        self.btn_mic.setFixedSize(16, 16)
        self.btn_mic.setStyleSheet("background-color:#28C940; border-radius:8px; border: 1px rgba(0,0,0,0.10);")
        self.btn_mic.clicked.connect(self._toggle_mic)
        topbar.addWidget(self.btn_mic)
        topbar.addStretch()
        main_layout.addLayout(topbar)

        # status label (one-line)
        self.status_label = QLabel("Rose — voice-only assistant", self)
        self.status_label.setStyleSheet(f"color: {GLOW_COLOR}; font-family: Consolas; font-size: 12pt;")
        main_layout.addWidget(self.status_label)

        # small history area
        self.history = QLabel("", self)
        self.history.setWordWrap(True)
        self.history.setStyleSheet("color: #E6E6E6; font-family: Consolas; font-size: 10pt;")
        self.history.setFixedHeight(120)
        main_layout.addWidget(self.history)

        # mic indicator
        self.mic_ind = QLabel("", self)
        self.mic_ind.setStyleSheet("color: #9ef; font-family: Consolas; font-size: 10pt;")
        main_layout.addWidget(self.mic_ind)

        self.setLayout(main_layout)

        # glow effect on entire widget (visual only)
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(28)
        glow.setColor(QColor(GLOW_COLOR))
        glow.setOffset(0)
        self.setGraphicsEffect(glow)

        # animation timers
        self._bg_timer = QTimer(self)
        self._bg_timer.timeout.connect(self._animate_background)
        self._bg_timer.start(40)  # ~25 FPS style smoothness

        # short history buffer
        self._history_lines = []

        # connect signals
        comm.add_status.connect(self._on_status)
        comm.set_listening.connect(self._on_listening)

        # start listener thread
        self.listener = ListenerThread(comm, start_listen=LISTEN_ON_START)
        self.listener.start()
        comm.set_listening.emit(LISTEN_ON_START)

        # greet
        self._add_history("Rose: Booting... ")
        # speak greeting
        speak("Hello Adhi. I am Rose. I am listening. What can I do for you?")

    # ---------- UI actions ----------
    def _add_history_line(self, s: str):
        # keep last 6 lines
        self._history_lines.append(s)
        if len(self._history_lines) > 6:
            self._history_lines = self._history_lines[-6:]
        self.history.setText("\n".join(self._history_lines))

    def _on_status(self, text: str):
        # signal callback — append a short status line
        self._add_history_line(text)

    def _on_listening(self, flag: bool):
        # update mic indicator
        self.mic_ind.setText("Listening: ON" if flag else "Listening: OFF")

    def _toggle_mic(self):
        new = not self.listener.listening
        self.listener.listening = new
        comm.set_listening.emit(new)
        # change mic button color for visual feedback
        if new:
            self.btn_mic.setStyleSheet("background-color:#28C940; border-radius:8px;")
        else:
            self.btn_mic.setStyleSheet("background-color:#7a7a7a; border-radius:8px;")

    def _hide(self):
        self.hide()

    def _close(self):
        # speak farewell then exit
        speak("Goodbye Adhi. Shutting down.")
        time.sleep(0.45)
        try:
            self.listener.stop()
        except:
            pass
        QApplication.quit()
        sys.exit(0)

    # ---------- background animation ----------
    def _animate_background(self):
        # increment phase
        self._bg_phase += 0.008
        # compute two hues and blend into CSS gradient
        import math
        h1 = (math.sin(self._bg_phase) + 1) / 2  # 0..1
        h2 = (math.cos(self._bg_phase * 1.3) + 1) / 2
        # map to color stops (simple interpolation between two RGBs)
        def lerp(a,b,t): return tuple(int(a[i] + (b[i]-a[i])*t) for i in range(3))
        c1 = lerp(BG_BASE, (30, 5, 45), h1)   # dark purple-ish
        c2 = lerp(BG_BASE, (5, 35, 60), h2)   # blue-ish
        css = f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba({c1[0]},{c1[1]},{c1[2]},220), stop:1 rgba({c2[0]},{c2[1]},{c2[2]},220)); border-radius:12px;"
        self.setStyleSheet(css)

    def _add_history(self, text: str):
        self._add_history_line(text)

# ---------- Run ----------
def main():
    app = QApplication(sys.argv)
    hud = RoseHUD()
    hud.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
