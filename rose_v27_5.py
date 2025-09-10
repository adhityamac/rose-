# rose_v28.py
# Complete Rose AI Assistant with Enhanced HUD
# Features: Enhanced 2D Rose Animation, Mood-based colors, Smooth UI, Voice control, AI integration

import sys
import os
import math
import time
import asyncio
import threading
import webbrowser
import platform
import subprocess
from typing import Optional
import json

from PySide6.QtCore import Qt, QTimer, QRect, QEasingCurve, QPropertyAnimation, QPoint
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton
from PySide6.QtGui import QFont, QPainter, QLinearGradient, QRadialGradient, QColor, QBrush, QPixmap, QPen, QPolygonF

import speech_recognition as sr
import edge_tts
from pytube import Search
import requests

# ------------------------ Globals ------------------------
LISTENING = True
TTS_PLAYING = False
TTS_LOCK = threading.Lock()
BG_LISTENER_STOP = None
CONVERSATION_HISTORY = []
REMINDERS = []

# File paths for persistence
HISTORY_FILE = "rose_history.json"
REMINDERS_FILE = "rose_reminders.json"

# Your API keys
GEMINI_API_KEY = "AIzaSyB3hpqh17aPpqeaQSe5eW8yxpcw1rlkydk"
OPENWEATHER_API_KEY = "9938e50ae1b4436a854205957250909"
NEWSAPI_API_KEY = "379d79c81dee44a1b3bdbfdde53ea2bf"

# Color Palettes based on mood
COLOR_PALETTES = {
    "calm": {
        "primary": QColor(242, 230, 238),  # Light pink
        "secondary": QColor(183, 198, 234),  # Light blue
        "accent": QColor(151, 112, 255),  # Purple
        "deep": QColor(0, 51, 255)  # Deep blue
    },
    "energetic": {
        "primary": QColor(255, 179, 153),  # Peach
        "secondary": QColor(255, 140, 120),  # Orange
        "accent": QColor(255, 87, 51),  # Bright orange
        "deep": QColor(230, 57, 70)  # Red
    },
    "focused": {
        "primary": QColor(151, 112, 255),  # Purple
        "secondary": QColor(121, 134, 203),  # Blue purple
        "accent": QColor(0, 51, 255),  # Blue
        "deep": QColor(6, 0, 74)  # Dark blue
    },
    "relaxed": {
        "primary": QColor(255, 230, 204),  # Warm beige
        "secondary": QColor(255, 204, 153),  # Light orange
        "accent": QColor(255, 153, 102),  # Orange
        "deep": QColor(255, 102, 51)  # Deep orange
    }
}

# ------------------------ Load/Save Persistent Data ------------------------
def load_persistent_data():
    global CONVERSATION_HISTORY, REMINDERS
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            CONVERSATION_HISTORY = json.load(f)
    if os.path.exists(REMINDERS_FILE):
        with open(REMINDERS_FILE, 'r') as f:
            REMINDERS = json.load(f)

def save_persistent_data():
    with open(HISTORY_FILE, 'w') as f:
        json.dump(CONVERSATION_HISTORY, f)
    with open(REMINDERS_FILE, 'w') as f:
        json.dump(REMINDERS, f)

# ------------------------ TTS helpers ------------------------
def _estimate_tts_duration_seconds(text: str) -> float:
    words = len(text.split())
    return max(0.6, words / 2.8)

def _play_audio_file(path: str):
    try:
        if platform.system() == "Windows":
            subprocess.Popen(["start", path], shell=True)
        elif platform.system() == "Darwin":
            subprocess.Popen(["afplay", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        print("Playback error:", e)

async def _gen_tts_save(text: str, filename: str = "speech.mp3", rate: str = "+0%", pitch: str = "+0Hz"):
    comm = edge_tts.Communicate(text, "en-US-JennyNeural", rate=rate, pitch=pitch)
    await comm.save(filename)

def speak(text: str):
    """Generate TTS with emotional parameters"""
    rate = "+0%"
    pitch = "+0Hz"
    lower_text = text.lower()
    if any(word in lower_text for word in ["joke", "fun", "excited", "great", "awesome"]):
        rate = "+20%"
        pitch = "+50Hz"
    elif any(word in lower_text for word in ["sad", "sorry", "bad", "error"]):
        rate = "-10%"
        pitch = "-50Hz"
    elif any(word in lower_text for word in ["weather", "news", "info", "fact"]):
        rate = "-5%"
        pitch = "+0Hz"

    def runner():
        global TTS_PLAYING
        with TTS_LOCK:
            TTS_PLAYING = True
        try:
            asyncio.run(_gen_tts_save(text, "speech.mp3", rate, pitch))
            _play_audio_file("speech.mp3")
            time.sleep(_estimate_tts_duration_seconds(text) + 0.35)
        except Exception as e:
            print("TTS error:", e)
        finally:
            with TTS_LOCK:
                TTS_PLAYING = False
    threading.Thread(target=runner, daemon=True).start()

# ------------------------ Media & System Control ------------------------
def play_youtube_song(song: str):
    try:
        query = song.strip()
        if not query:
            webbrowser.open("https://www.youtube.com")
            return
        s = Search(query)
        if not getattr(s, "results", None):
            webbrowser.open(f"https://www.youtube.com/results?search_query={query.replace(' ','+')}")
            return
        first = s.results[0]
        url = getattr(first, "watch_url", None) or f"https://www.youtube.com/watch?v={first.video_id}"
        webbrowser.open(url)
    except Exception as e:
        print("YouTube error:", e)
        webbrowser.open(f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}")

def _send_media_key_windows(vk_code: int):
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        INPUT_KEYBOARD = 1
        KEYEVENTF_EXTENDEDKEY = 0x0001
        KEYEVENTF_KEYUP = 0x0002

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = (("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                        ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                        ("dwExtraInfo", wintypes.ULONG_PTR))

        class INPUT(ctypes.Structure):
            _fields_ = (("type", wintypes.DWORD), ("ki", KEYBDINPUT))

        ki = KEYBDINPUT(wVk=vk_code, wScan=0, dwFlags=KEYEVENTF_EXTENDEDKEY, time=0, dwExtraInfo=0)
        x = INPUT(type=INPUT_KEYBOARD, ki=ki)
        user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

        ki_up = KEYBDINPUT(wVk=vk_code, wScan=0, dwFlags=KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, time=0, dwExtraInfo=0)
        x_up = INPUT(type=INPUT_KEYBOARD, ki=ki_up)
        user32.SendInput(1, ctypes.byref(x_up), ctypes.sizeof(x_up))
    except Exception as e:
        print("Windows media key send failed:", e)

def spotify_play_pause():
    try:
        if platform.system() == "Windows":
            _send_media_key_windows(0xB3)
        elif platform.system() == "Darwin":
            subprocess.Popen(["osascript", "-e", 'tell application "Spotify" to playpause'])
        else:
            os.system("playerctl play-pause")
    except Exception as e:
        print("Spotify play/pause error:", e)

def spotify_next():
    try:
        if platform.system() == "Windows":
            _send_media_key_windows(0xB0)
        elif platform.system() == "Darwin":
            subprocess.Popen(["osascript", "-e", 'tell application "Spotify" to next track'])
        else:
            os.system("playerctl next")
    except Exception as e:
        print("Spotify next error:", e)

def spotify_prev():
    try:
        if platform.system() == "Windows":
            _send_media_key_windows(0xB1)
        elif platform.system() == "Darwin":
            subprocess.Popen(["osascript", "-e", 'tell application "Spotify" to previous track'])
        else:
            os.system("playerctl previous")
    except Exception as e:
        print("Spotify previous error:", e)

def adjust_volume(cmd: str):
    try:
        if platform.system() == "Windows":
            if "up" in cmd: os.system("nircmd.exe changesysvolume 5000")
            elif "down" in cmd: os.system("nircmd.exe changesysvolume -5000")
            elif "mute" in cmd: os.system("nircmd.exe mutesysvolume 1")
            elif "unmute" in cmd: os.system("nircmd.exe mutesysvolume 0")
        elif platform.system() == "Darwin":
            if "up" in cmd: os.system("osascript -e 'set volume output volume (output volume of (get volume settings) + 10)'")
            elif "down" in cmd: os.system("osascript -e 'set volume output volume (output volume of (get volume settings) - 10)'")
        else:
            if "up" in cmd: os.system("amixer -D pulse sset Master 5%+")
            elif "down" in cmd: os.system("amixer -D pulse sset Master 5%-")
    except Exception as e:
        print("Volume control error:", e)

def system_action(cmd: str):
    try:
        if "shutdown" in cmd:
            if platform.system() == "Windows": os.system("shutdown /s /t 1")
            else: os.system("shutdown now")
        elif "restart" in cmd:
            if platform.system() == "Windows": os.system("shutdown /r /t 1")
            else: os.system("reboot")
    except Exception as e:
        print("System action error:", e)

# ------------------------ Integrations ------------------------
def get_weather(city: str):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url).json()
        if response.get("cod") != 200:
            return "Sorry, couldn't fetch weather data."
        temp = response['main']['temp']
        desc = response['weather'][0]['description']
        return f"The weather in {city} is {desc} with a temperature of {temp}°C."
    except Exception as e:
        print("Weather API error:", e)
        return "Sorry, there was an error fetching the weather."

def get_news():
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWSAPI_API_KEY}"
    try:
        response = requests.get(url).json()
        if response.get("status") != "ok":
            return "Sorry, couldn't fetch news data."
        articles = response['articles'][:3]
        news_str = "Top headlines: "
        for art in articles:
            news_str += f"{art['title']} from {art['source']['name']}. "
        return news_str.strip()
    except Exception as e:
        print("News API error:", e)
        return "Sorry, there was an error fetching the news."

def handle_reminder(cmd_norm: str):
    global REMINDERS
    if "remind me to" in cmd_norm:
        task = cmd_norm.split("remind me to")[-1].strip()
        REMINDERS.append(task)
        save_persistent_data()
        return f"Reminder added: {task}"
    elif "what are my reminders" in cmd_norm:
        if not REMINDERS:
            return "You have no reminders."
        return "Your reminders: " + "; ".join(REMINDERS)
    return None

# ------------------------ 2D Rose Widget ------------------------
class Rose2D(QWidget):
    """2D animated rose using Qt painting"""
    def __init__(self):
        super().__init__()
        self.rotation_angle = 0.0
        self.bloom_factor = 1.0
        self.is_blooming = False
        
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(16)
        
    def animate(self):
        self.rotation_angle += 1.0
        if self.rotation_angle >= 360:
            self.rotation_angle = 0
            
        if self.is_blooming:
            self.bloom_factor = min(1.5, self.bloom_factor + 0.02)
            if self.bloom_factor >= 1.5:
                self.is_blooming = False
        else:
            self.bloom_factor = max(1.0, self.bloom_factor - 0.01)
            
        self.update()
        
    def start_bloom(self):
        self.is_blooming = True
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        center_x, center_y = w / 2, h / 2
        
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.rotation_angle)
        
        self.draw_rose_petals(painter)
        painter.restore()
        
    def draw_rose_petals(self, painter):
        base_size = 25 * self.bloom_factor
        
        # Outer petals
        for i in range(8):
            angle = i * 45
            painter.save()
            painter.rotate(angle)
            
            alpha = 200 if self.is_blooming else 150
            petal_color = QColor(255, 160, 160, alpha)
            painter.setBrush(QBrush(petal_color))
            painter.setPen(QPen(QColor(255, 100, 100, 100), 1))
            
            petal = QPolygonF()
            petal.append(QPoint(0, 0))
            petal.append(QPoint(int(base_size * 0.8), int(-base_size * 0.3)))
            petal.append(QPoint(int(base_size), int(-base_size * 0.1)))
            petal.append(QPoint(int(base_size * 0.8), int(base_size * 0.3)))
            petal.append(QPoint(0, 0))
            
            painter.drawPolygon(petal)
            painter.restore()
            
        # Inner petals
        for i in range(6):
            angle = i * 60 + 30
            painter.save()
            painter.rotate(angle)
            
            alpha = 220 if self.is_blooming else 170
            inner_color = QColor(255, 120, 120, alpha)
            painter.setBrush(QBrush(inner_color))
            painter.setPen(QPen(QColor(255, 80, 80, 120), 1))
            
            inner_petal = QPolygonF()
            inner_size = base_size * 0.6
            inner_petal.append(QPoint(0, 0))
            inner_petal.append(QPoint(int(inner_size * 0.7), int(-inner_size * 0.2)))
            inner_petal.append(QPoint(int(inner_size * 0.8), 0))
            inner_petal.append(QPoint(int(inner_size * 0.7), int(inner_size * 0.2)))
            inner_petal.append(QPoint(0, 0))
            
            painter.drawPolygon(inner_petal)
            painter.restore()
            
        # Center
        center_size = int(base_size * 0.4)
        center_color = QColor(255, 80, 80, 250)
        painter.setBrush(QBrush(center_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(-center_size//2, -center_size//2, center_size, center_size)

# ------------------------ Enhanced HUD ------------------------
class EnhancedHUD(QWidget):
    def __init__(self):
        super().__init__()
        load_persistent_data()
        self.current_mood = "calm"
        self.title_visible = True
        self.setup_ui()
        self.setup_animations()
        
    def setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(600, 400)
        self.setMinimumSize(400, 300)
        
        # 2D Rose widget
        self.rose_2d = Rose2D()
        self.rose_2d.setParent(self)
        self.rose_2d.setGeometry(250, 150, 100, 100)
        
        # Title label
        self.title_label = QLabel("ROSE", self)
        self.title_label.setFont(QFont("Segoe UI", 36, QFont.Bold))
        self.title_label.setStyleSheet("color: white;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setGeometry(0, 60, self.width(), 60)
        
        # Response label
        self.response_label = QLabel("Hello, I'm Rose, your healer.", self)
        self.response_label.setFont(QFont("Segoe UI", 14))
        self.response_label.setStyleSheet("color: white;")
        self.response_label.setAlignment(Qt.AlignCenter)
        self.response_label.setWordWrap(True)
        self.response_label.setGeometry(40, 280, self.width() - 80, 80)
        
        self.setup_buttons()
        
        self.circle_pulse = 0.0
        self.bg_shift = 0.0
        
    def setup_buttons(self):
        # Mac-style buttons
        self.close_btn = QPushButton(self)
        self.close_btn.setStyleSheet("background-color: #FF5C5C; border-radius:8px; border: none;")
        self.close_btn.setGeometry(15, 15, 18, 18)
        self.close_btn.clicked.connect(self._animate_close)
        
        self.min_btn = QPushButton(self)
        self.min_btn.setStyleSheet("background-color: #FFBD44; border-radius:8px; border: none;")
        self.min_btn.setGeometry(40, 15, 18, 18)
        self.min_btn.clicked.connect(self._animate_minimize)
        
        # Mood selector buttons
        moods = ["calm", "energetic", "focused", "relaxed"]
        for i, mood in enumerate(moods):
            btn = QPushButton(mood.title(), self)
            btn.setGeometry(450 + i * 35, 15, 30, 20)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.2);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 10px;
                    color: white;
                    font-size: 8px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.3);
                }
            """)
            btn.clicked.connect(lambda checked, m=mood: self.set_mood(m))
        
    def setup_animations(self):
        self.bg_timer = QTimer()
        self.bg_timer.timeout.connect(self.animate_background)
        self.bg_timer.start(32)
        
        self.title_timer = QTimer()
        self.title_timer.timeout.connect(self.fade_title)
        self.title_timer.setSingleShot(True)
        self.title_timer.start(20000)  # 20 seconds
        
        self._start_background_listener()
        QTimer.singleShot(900, self._greet)
        
        self.setWindowOpacity(0.0)
        self._animate_show()
        
    def _greet(self):
        global CONVERSATION_HISTORY
        greeting = "Hi, I'm Rose, your healer. How can I assist you?"
        self.update_response(greeting)
        speak(greeting)
        CONVERSATION_HISTORY.append({"role": "model", "parts": [{"text": greeting}]})
        save_persistent_data()
        
    def set_mood(self, mood):
        self.current_mood = mood
        self.rose_2d.start_bloom()
        self.update()
        
    def get_mood_from_text(self, text):
        text_lower = text.lower()
        if any(word in text_lower for word in ["excited", "great", "awesome", "amazing", "fantastic", "fun", "party", "dance", "music"]):
            return "energetic"
        elif any(word in text_lower for word in ["work", "focus", "task", "study", "code", "programming", "important", "serious"]):
            return "focused"
        elif any(word in text_lower for word in ["calm", "relax", "peaceful", "quiet", "rest", "sleep", "meditate", "breathe"]):
            return "relaxed"
        else:
            return "calm"
            
    def update_response(self, text):
        detected_mood = self.get_mood_from_text(text)
        if detected_mood != self.current_mood:
            self.set_mood(detected_mood)
        self.response_label.setText(text)
        
    def fade_title(self):
        self.title_anim = QPropertyAnimation(self.title_label, b"windowOpacity")
        self.title_anim.setDuration(2000)
        self.title_anim.setStartValue(1.0)
        self.title_anim.setEndValue(0.0)
        self.title_anim.setEasingCurve(QEasingCurve.InOutCubic)
        self.title_anim.finished.connect(lambda: self.title_label.hide())
        self.title_anim.start()
        
    def animate_background(self):
        self.circle_pulse += 0.05
        self.bg_shift += 0.02
        if self.circle_pulse > math.pi * 2:
            self.circle_pulse = 0
        if self.bg_shift > math.pi * 2:
            self.bg_shift = 0
        self.update()
        
    def _animate_show(self):
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(420)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        anim.start()
        self._fade_anim = anim

    def _animate_close(self):
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(350)
        anim.setStartValue(self.windowOpacity())
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InOutCubic)

        def do_close():
            save_persistent_data()
            global BG_LISTENER_STOP
            if BG_LISTENER_STOP:
                try:
                    BG_LISTENER_STOP(wait_for_stop=False)
                except Exception:
                    pass
            self.close()

        anim.finished.connect(do_close)
        anim.start()
        self._fade_anim = anim

    def _animate_minimize(self):
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(300)
        anim.setStartValue(self.windowOpacity())
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InOutCubic)

        def do_min():
            save_persistent_data()
            self.showMinimized()
            self.setWindowOpacity(0.0)

        anim.finished.connect(do_min)
        anim.start()
        self._fade_anim = anim
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        palette = COLOR_PALETTES[self.current_mood]
        
        # Smooth gradient background
        gradient = QRadialGradient(w/2, h/2, max(w, h)/2)
        gradient.setColorAt(0.0, palette["primary"])
        gradient.setColorAt(0.4, palette["secondary"])
        gradient.setColorAt(0.8, palette["accent"])
        gradient.setColorAt(1.0, palette["deep"])
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, 25, 25)
        
        # Central pulsing circle
        self.draw_central_circle(painter, w/2, h/2)
        
        # Overlay patterns
        self.draw_overlay_patterns(painter)
        
    def draw_central_circle(self, painter, center_x, center_y):
        palette = COLOR_PALETTES[self.current_mood]
        pulse = math.sin(self.circle_pulse) * 0.1 + 1.0
        
        base_radius = 80
        for i in range(6):
            radius = base_radius - (i * 12)
            alpha = int(255 * (0.8 - i * 0.12) * pulse)
            
            if i < 2:
                color = QColor(palette["primary"])
            elif i < 4:
                color = QColor(palette["secondary"])
            else:
                color = QColor(palette["accent"])
                
            color.setAlpha(alpha)
            
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(center_x - radius), int(center_y - radius), 
                              int(radius * 2), int(radius * 2))
                              
    def draw_overlay_patterns(self, painter):
        w, h = self.width(), self.height()
        
        for i in range(12):
            x = (w * 0.1) + (i * w * 0.08) + math.sin(self.bg_shift + i * 0.5) * 20
            y = (h * 0.2) + math.cos(self.bg_shift + i * 0.3) * 30
            
            size = 3 + math.sin(self.bg_shift + i) * 2
            alpha = int(100 + math.cos(self.bg_shift + i * 0.7) * 50)
            
            color = QColor(255, 255, 255, alpha)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(x), int(y), int(size), int(size))
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            
    def mouseMoveEvent(self, event):
        if hasattr(self, 'drag_pos') and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)

    # ------------------------ Voice Recognition & Background Listener ------------------------
    def _start_background_listener(self):
        recognizer_test = sr.Recognizer()
        mics = sr.Microphone.list_microphone_names()
        mic_index = None

        bad_keywords = ("Sound Mapper", "Microsoft Sound Mapper", "Primary Sound Driver", "Stereo Mix")
        for i, name in enumerate(mics):
            if any(bk in name for bk in bad_keywords):
                continue
            try:
                with sr.Microphone(device_index=i) as source:
                    recognizer_test.adjust_for_ambient_noise(source, duration=0.8)
                mic_index = i
                print("Using mic:", name)
                break
            except Exception:
                continue

        if mic_index is None and mics:
            mic_index = 0
            print("Falling back to mic:", mics[0])

        if mic_index is None:
            print("No microphone devices available.")
            self.update_response("No microphone available")
            return

        mic = sr.Microphone(device_index=mic_index)

        def callback(recognizer_obj, audio):
            with TTS_LOCK:
                if TTS_PLAYING:
                    return
            try:
                text = recognizer_obj.recognize_google(audio)
                if text and text.strip():
                    threading.Thread(target=handle_command, args=(text, self), daemon=True).start()
            except sr.UnknownValueError:
                return
            except sr.RequestError as e:
                print("Speech recognition request error:", e)
                return
            except Exception as e:
                print("Recognition callback error:", e)
                return

        global BG_LISTENER_STOP
        try:
            rec = sr.Recognizer()
            BG_LISTENER_STOP = rec.listen_in_background(mic, callback, phrase_time_limit=4)
        except Exception as e:
            print("Background listener failed, falling back to blocking loop:", e)
            threading.Thread(target=self._fallback_listen_loop, args=(mic,), daemon=True).start()

    def _fallback_listen_loop(self, mic):
        r = sr.Recognizer()
        r.dynamic_energy_threshold = True
        r.pause_threshold = 0.35
        while LISTENING:
            try:
                with mic as source:
                    r.adjust_for_ambient_noise(source, duration=0.6)
                    audio = r.listen(source, phrase_time_limit=5)
                try:
                    text = r.recognize_google(audio)
                    if text and text.strip():
                        handle_command(text, self)
                except sr.UnknownValueError:
                    continue
                except sr.RequestError as e:
                    print("SR request error:", e)
                    time.sleep(0.5)
                    continue
            except Exception as e:
                print("Fallback mic error:", e)
                time.sleep(0.5)
                continue

    def closeEvent(self, ev):
        global LISTENING, BG_LISTENER_STOP
        LISTENING = False
        save_persistent_data()
        if BG_LISTENER_STOP:
            try:
                BG_LISTENER_STOP(wait_for_stop=False)
            except Exception:
                pass
        time.sleep(0.2)
        ev.accept()

# ------------------------ Command Handling ------------------------
def handle_command(cmd: str, hud_ref: Optional[QWidget] = None):
    if not cmd:
        return
    cmd_norm = cmd.lower().strip()
    if hud_ref:
        hud_ref.update_response(f"You said: {cmd_norm}")

    # Handle reminders
    reminder_reply = handle_reminder(cmd_norm)
    if reminder_reply:
        speak(reminder_reply)
        if hud_ref: hud_ref.update_response(reminder_reply)
        return

    # Weather integration
    if "weather" in cmd_norm:
        city = cmd_norm.split("in")[-1].strip() if "in" in cmd_norm else "London"
        reply = get_weather(city)
        speak(reply)
        if hud_ref: hud_ref.update_response(reply)
        return

    # News integration
    if "news" in cmd_norm or "headlines" in cmd_norm:
        reply = get_news()
        speak(reply)
        if hud_ref: hud_ref.update_response(reply)
        return

    # Spotify voice commands
    if "spotify" in cmd_norm:
        if any(k in cmd_norm for k in ("play", "pause", "play pause", "play/pause")):
            spotify_play_pause(); speak("Toggling Spotify play pause"); return
        if "next" in cmd_norm or "skip" in cmd_norm:
            spotify_next(); speak("Skipping to next track"); return
        if "previous" in cmd_norm or "prev" in cmd_norm or "back" in cmd_norm:
            spotify_prev(); speak("Going to previous track"); return

    # Play on YouTube
    if cmd_norm.startswith("play "):
        if "on youtube" in cmd_norm or "youtube" in cmd_norm:
            song = cmd_norm.replace("play", "").replace("on youtube", "").replace("youtube", "").strip()
            if hud_ref: hud_ref.update_response(f"Playing {song} on YouTube...")
            speak(f"Playing {song} on YouTube")
            play_youtube_song(song)
            return
        else:
            song = cmd_norm[5:].strip()
            if song:
                if hud_ref: hud_ref.update_response(f"Playing {song} on YouTube...")
                speak(f"Playing {song} on YouTube")
                play_youtube_song(song)
                return

    # Volume control
    if any(x in cmd_norm for x in ("volume up", "increase volume", "volume higher")):
        adjust_volume("up"); speak("Volume increased"); 
        if hud_ref: hud_ref.update_response("Volume increased"); return
    if any(x in cmd_norm for x in ("volume down", "decrease volume", "volume lower")):
        adjust_volume("down"); speak("Volume decreased"); 
        if hud_ref: hud_ref.update_response("Volume decreased"); return
    if "mute" in cmd_norm and "unmute" not in cmd_norm:
        adjust_volume("mute"); speak("Muted"); 
        if hud_ref: hud_ref.update_response("Muted"); return
    if "unmute" in cmd_norm:
        adjust_volume("unmute"); speak("Unmuted"); 
        if hud_ref: hud_ref.update_response("Unmuted"); return

    # System commands
    if "shutdown" in cmd_norm:
        if hud_ref: hud_ref.update_response("Shutting down...")
        speak("Shutting down the system")
        system_action("shutdown")
        return
    if "restart" in cmd_norm:
        if hud_ref: hud_ref.update_response("Restarting...")
        speak("Restarting the system")
        system_action("restart")
        return

    # Open applications
    if "open chrome" in cmd_norm or "open brave" in cmd_norm or "open browser" in cmd_norm:
        speak("Opening browser")
        if platform.system() == "Windows":
            brave = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
            chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            if os.path.exists(brave): subprocess.Popen([brave])
            elif os.path.exists(chrome): subprocess.Popen([chrome])
            else: webbrowser.open("https://www.google.com")
        else:
            webbrowser.open("https://www.google.com")
        return
    if "open vscode" in cmd_norm or "open code" in cmd_norm:
        speak("Opening Visual Studio Code")
        if platform.system() == "Windows":
            code_path = rf"C:\Users\{os.getlogin()}\AppData\Local\Programs\Microsoft VS Code\Code.exe"
            if os.path.exists(code_path): subprocess.Popen([code_path]); return
        webbrowser.open("https://code.visualstudio.com")
        return

    # Greetings
    if any(g in cmd_norm for g in ("hello", "hi", "hey")):
        speak("Hello. I'm Rose, your healer.")
        if hud_ref: hud_ref.update_response("Hello. I'm Rose, your healer.")
        return

    # Default: Use Gemini API for conversational response
    global CONVERSATION_HISTORY
    CONVERSATION_HISTORY.append({"role": "user", "parts": [{"text": cmd_norm}]})
    try:
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": CONVERSATION_HISTORY,
            "systemInstruction": {
                "parts": [{"text": "You are Rose, a healer AI assistant. Respond helpfully and conversationally."}]
            },
            "generationConfig": {
                "maxOutputTokens": 150
            }
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(api_url, json=payload, headers=headers)
        if not response.ok:
            print("HTTP Error:", response.status_code, response.text)
            raise ValueError("API request failed")
        json_response = response.json()
        if 'error' in json_response:
            print("API Error:", json_response['error'])
            raise ValueError("API returned error")
        if 'candidates' not in json_response:
            print("No candidates in response:", json_response)
            prompt_feedback = json_response.get("promptFeedback", {})
            block_reason = prompt_feedback.get("blockReason", "Unknown")
            speak(f"Sorry, the response was blocked due to {block_reason}.")
            if hud_ref:
                hud_ref.update_response(f"Blocked: {block_reason}")
            CONVERSATION_HISTORY.pop()
            return
        ai_candidate = json_response["candidates"][0]
        if "content" not in ai_candidate:
            finish_reason = ai_candidate.get("finishReason", "Unknown")
            speak(f"Sorry, the response was blocked due to {finish_reason}.")
            if hud_ref:
                hud_ref.update_response(f"Blocked: {finish_reason}")
            CONVERSATION_HISTORY.pop()
            return
        ai_reply = ai_candidate["content"]["parts"][0]["text"].strip()
        CONVERSATION_HISTORY.append({"role": "model", "parts": [{"text": ai_reply}]})
        save_persistent_data()
        speak(ai_reply)
        if hud_ref:
            hud_ref.update_response(ai_reply)
    except Exception as e:
        print("Gemini API error:", e)
        speak(f"I heard: {cmd_norm}. Sorry, I couldn't process that with AI.")
        if hud_ref: hud_ref.update_response(f"I heard: {cmd_norm}")
        CONVERSATION_HISTORY.pop()

# ------------------------ Main Application ------------------------
def main():
    app = QApplication(sys.argv)
    hud = EnhancedHUD()
    hud.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()