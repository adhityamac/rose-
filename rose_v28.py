# rose_v28.py
# Rose v28 — fixes: ROSE title fades reliably after 5s; removed top hint text.
# Keep gradient HTML background (if QtWebEngine available), rose icon beside buttons,
# stacked menu, snap-to-edge docking, always-listening SR, TTS, youtube, spotify, reminders.

import sys
import os
import math
import time
import asyncio
import threading
import webbrowser
import platform
import subprocess
import json
from typing import Optional

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QRect
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QMenu, QScrollArea, QTextEdit,
    QGraphicsOpacityEffect
)
from PySide6.QtGui import QFont, QPixmap, QCloseEvent

# optional WebEngine
USE_WEBENGINE = True
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except Exception:
    USE_WEBENGINE = False
    print("[WARN] PySide6.QtWebEngineWidgets import failed. HTML background disabled. Install PySide6-QtWebEngine to enable it.")

# optional libs
try:
    import speech_recognition as sr
except Exception:
    sr = None
    print("[WARN] speech_recognition not installed; voice input disabled.")
try:
    import edge_tts
except Exception:
    edge_tts = None
    print("[WARN] edge-tts not installed; TTS will be fallback print-only.")
try:
    from pytube import Search
except Exception:
    Search = None
    print("[WARN] pytube not installed; YouTube will open search page.")

import requests

# ---------------- CONFIG ----------------
HTML_FILE = "gradient_circle_design.html"
ROSE_ICON_FILE = "rose_logo.png"
HISTORY_FILE = "rose_history.json"
REMINDERS_FILE = "rose_reminders.json"

GEMINI_API_KEY = ""         # optional
OPENWEATHER_API_KEY = ""
NEWSAPI_API_KEY = ""

LISTENING = True
TTS_PLAYING = False
TTS_LOCK = threading.Lock()
BG_LISTENER_STOP = None
CONVERSATION_HISTORY = []
REMINDERS = []

# ---------------- persistence ----------------
def load_persistent():
    global CONVERSATION_HISTORY, REMINDERS
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf8") as f:
                CONVERSATION_HISTORY = json.load(f)
    except Exception:
        CONVERSATION_HISTORY = []
    try:
        if os.path.exists(REMINDERS_FILE):
            with open(REMINDERS_FILE, "r", encoding="utf8") as f:
                REMINDERS = json.load(f)
    except Exception:
        REMINDERS = []

def save_persistent():
    try:
        with open(HISTORY_FILE, "w", encoding="utf8") as f:
            json.dump(CONVERSATION_HISTORY, f, ensure_ascii=False, indent=2)
        with open(REMINDERS_FILE, "w", encoding="utf8") as f:
            json.dump(REMINDERS, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Save error:", e)

# ---------------- TTS ----------------
def _estimate_tts_duration_seconds(text: str) -> float:
    words = len(text.split())
    return max(0.6, words / 2.8)

def _play_file_default(path: str):
    try:
        if platform.system() == "Windows":
            subprocess.Popen(["start", path], shell=True)
        elif platform.system() == "Darwin":
            subprocess.Popen(["afplay", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        print("Playback error:", e)

async def _gen_tts_save(text: str, filename: str = "speech.mp3"):
    if not edge_tts:
        raise RuntimeError("edge-tts not installed")
    comm = edge_tts.Communicate(text, "en-US-JennyNeural")
    await comm.save(filename)

def speak(text: str):
    """Generate and play TTS in background; sets TTS_PLAYING flag while estimated playback duration."""
    def _runner():
        global TTS_PLAYING
        with TTS_LOCK:
            TTS_PLAYING = True
        try:
            if edge_tts:
                asyncio.run(_gen_tts_save(text, "speech.mp3"))
                _play_file_default("speech.mp3")
            else:
                # fallback
                print("[TTS fallback] " + text)
        except Exception as e:
            print("TTS error:", e)
        finally:
            time.sleep(_estimate_tts_duration_seconds(text) + 0.35)
            with TTS_LOCK:
                TTS_PLAYING = False
    threading.Thread(target=_runner, daemon=True).start()

# ---------------- YouTube ----------------
def play_youtube_song(song: str):
    song = (song or "").strip()
    if not song:
        webbrowser.open("https://www.youtube.com")
        return
    try:
        if Search:
            s = Search(song)
            if getattr(s, "results", None):
                first = s.results[0]
                url = getattr(first, "watch_url", None) or f"https://www.youtube.com/watch?v={first.video_id}"
                webbrowser.open(url)
                return
    except Exception as e:
        print("pytube search error:", e)
    webbrowser.open(f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}")

# ---------------- Spotify local controls ----------------
def _send_media_key_windows(vk_code: int):
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        INPUT_KEYBOARD = 1
        KEYEVENTF_EXTENDEDKEY = 0x0001
        KEYEVENTF_KEYUP = 0x0002
        class KEYBDINPUT(ctypes.Structure):
            _fields_ = (("wVk", wintypes.WORD),("wScan", wintypes.WORD),
                        ("dwFlags", wintypes.DWORD),("time", wintypes.DWORD),
                        ("dwExtraInfo", wintypes.ULONG_PTR))
        class INPUT(ctypes.Structure):
            _fields_ = (("type", wintypes.DWORD),("ki", KEYBDINPUT))
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
        print("Spotify control error:", e)

def spotify_next():
    try:
        if platform.system() == "Windows":
            _send_media_key_windows(0xB0)
        elif platform.system() == "Darwin":
            subprocess.Popen(["osascript","-e",'tell application "Spotify" to next track'])
        else:
            os.system("playerctl next")
    except Exception as e:
        print("Spotify next failed:", e)

def spotify_prev():
    try:
        if platform.system() == "Windows":
            _send_media_key_windows(0xB1)
        elif platform.system() == "Darwin":
            subprocess.Popen(["osascript","-e",'tell application "Spotify" to previous track'])
        else:
            os.system("playerctl previous")
    except Exception as e:
        print("Spotify prev failed:", e)

# ---------------- system helpers ----------------
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
        print("Volume error:", e)

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

# ---------------- utilities: weather/news/reminders ----------------
def get_weather(city: str):
    if not OPENWEATHER_API_KEY:
        return "Weather API key not configured."
    try:
        resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric", timeout=6).json()
        if resp.get("cod") != 200:
            return "Couldn't fetch weather."
        return f"The weather in {city} is {resp['weather'][0]['description']} and {resp['main']['temp']}°C."
    except Exception as e:
        print("Weather error:", e)
        return "Weather fetch error."

def get_news():
    if not NEWSAPI_API_KEY:
        return "News API key not configured."
    try:
        r = requests.get(f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWSAPI_API_KEY}", timeout=6).json()
        if r.get("status") != "ok":
            return "Couldn't fetch news."
        titles = [a["title"] for a in r.get("articles",[])[:3]]
        return "Top headlines: " + " / ".join(titles)
    except Exception as e:
        print("News error:", e)
        return "News fetch error."

def handle_reminder(cmd_norm: str):
    global REMINDERS
    if "remind me to" in cmd_norm:
        task = cmd_norm.split("remind me to",1)[1].strip()
        if task:
            REMINDERS.append(task)
            save_persistent()
            return f"Reminder added: {task}"
    if "what are my reminders" in cmd_norm or "list reminders" in cmd_norm:
        if not REMINDERS:
            return "No reminders."
        return "Reminders: " + " ; ".join(REMINDERS)
    return None

# ---------------- command processing ----------------
def handle_command(cmd: str, hud_ref: Optional["RoseHUD"] = None):
    if not cmd:
        return
    cmd_norm = cmd.lower().strip()
    print("Heard:", cmd_norm)
    if hud_ref:
        hud_ref.append_response(f"> {cmd_norm}")

    # youtube / browser
    if "open youtube" in cmd_norm or (cmd_norm.startswith("play ") and ("youtube" in cmd_norm or "on youtube" in cmd_norm)):
        if cmd_norm.startswith("play "):
            song = cmd_norm[5:].replace("on youtube","").replace("youtube","").strip()
        else:
            song = ""
        hud_ref and hud_ref.append_response("Opening YouTube...")
        speak("Opening YouTube")
        play_youtube_song(song)
        return

    if "open brave" in cmd_norm or "open chrome" in cmd_norm or "open browser" in cmd_norm:
        hud_ref and hud_ref.append_response("Opening browser...")
        speak("Opening browser")
        if platform.system() == "Windows":
            brave = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
            chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            if "brave" in cmd_norm and os.path.exists(brave):
                subprocess.Popen([brave]); return
            if "chrome" in cmd_norm and os.path.exists(chrome):
                subprocess.Popen([chrome]); return
            webbrowser.open("https://www.google.com")
        else:
            webbrowser.open("https://www.google.com")
        return

    # spotify
    if "spotify" in cmd_norm:
        if any(k in cmd_norm for k in ("play","pause","play/pause","toggle")):
            spotify_play_pause(); speak("Toggling Spotify"); hud_ref and hud_ref.append_response("Toggling Spotify"); return
        if "next" in cmd_norm or "skip" in cmd_norm:
            spotify_next(); speak("Next track"); hud_ref and hud_ref.append_response("Next track"); return
        if "previous" in cmd_norm or "prev" in cmd_norm:
            spotify_prev(); speak("Previous track"); hud_ref and hud_ref.append_response("Previous track"); return

    # volume
    if any(x in cmd_norm for x in ("volume up","increase volume","turn it up")):
        adjust_volume("up"); speak("Volume increased"); hud_ref and hud_ref.append_response("Volume increased"); return
    if any(x in cmd_norm for x in ("volume down","decrease volume","turn it down")):
        adjust_volume("down"); speak("Volume decreased"); hud_ref and hud_ref.append_response("Volume decreased"); return
    if "mute" in cmd_norm and "unmute" not in cmd_norm:
        adjust_volume("mute"); speak("Muted"); hud_ref and hud_ref.append_response("Muted"); return
    if "unmute" in cmd_norm:
        adjust_volume("unmute"); speak("Unmuted"); hud_ref and hud_ref.append_response("Unmuted"); return

    # reminders / weather / news
    r = handle_reminder(cmd_norm)
    if r:
        speak(r); hud_ref and hud_ref.append_response(r); return
    if "weather" in cmd_norm:
        city = cmd_norm.split("in")[-1].strip() if "in" in cmd_norm else "London"
        reply = get_weather(city); speak(reply); hud_ref and hud_ref.append_response(reply); return
    if "news" in cmd_norm or "headlines" in cmd_norm:
        reply = get_news(); speak(reply); hud_ref and hud_ref.append_response(reply); return

    # greetings
    if any(g in cmd_norm for g in ("hello","hi","hey")):
        speak("Hello. I'm Rose, your healer."); hud_ref and hud_ref.append_response("Hello. I'm Rose, your healer."); return

    # fallback to Gemini or echo
    CONVERSATION_HISTORY.append({"role":"user","parts":[{"text":cmd_norm}]})
    if GEMINI_API_KEY:
        try:
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": CONVERSATION_HISTORY,
                "systemInstruction": {"parts":[{"text":"You are Rose, a healer assistant. Answer helpfully."}]},
                "generationConfig": {"maxOutputTokens": 200}
            }
            headers = {"Content-Type":"application/json"}
            resp = requests.post(api_url, json=payload, headers=headers, timeout=8)
            jr = resp.json()
            ai_reply = jr["candidates"][0]["content"]["parts"][0]["text"].strip()
            CONVERSATION_HISTORY.append({"role":"model","parts":[{"text":ai_reply}]})
            save_persistent()
            speak(ai_reply); hud_ref and hud_ref.append_response(ai_reply)
            return
        except Exception as e:
            print("Gemini call error:", e)
            CONVERSATION_HISTORY.pop()
    # fallback echo
    speak(f"I heard: {cmd_norm}")
    hud_ref and hud_ref.append_response(f"I heard: {cmd_norm}")

# ---------------- HUD ----------------
class RoseHUD(QWidget):
    SNAP_MARGIN = 30
    SNAP_ANIM_MS = 240

    def __init__(self):
        super().__init__()
        load_persistent()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(880, 600)
        self._drag_offset = None
        self._is_max = False

        # HTML background or fallback
        if USE_WEBENGINE and os.path.exists(HTML_FILE):
            self.web = QWebEngineView(self)
            html_text = open(HTML_FILE, "r", encoding="utf8").read()
            # hide in-html top-controls so UI won't duplicate
            html_text = html_text.replace('<div class="top-controls">', '<div class="top-controls" style="display:none">')
            self.web.setHtml(html_text)
            self.web.setGeometry(0, 0, self.width(), self.height())
            self.web.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        else:
            self.web = None
            self.setStyleSheet("background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #110022, stop:1 #440077);")

        # mac buttons
        self.close_btn = QPushButton(self)
        self.close_btn.setGeometry(12, 12, 16, 16)
        self.close_btn.setStyleSheet("background:#FF5C5C;border-radius:8px;border:none;")
        self.close_btn.clicked.connect(self.close_animated)

        self.min_btn = QPushButton(self)
        self.min_btn.setGeometry(36, 12, 16, 16)
        self.min_btn.setStyleSheet("background:#FFBD44;border-radius:8px;border:none;")
        self.min_btn.clicked.connect(self.minimize_animated)

        self.max_btn = QPushButton(self)
        self.max_btn.setGeometry(60, 12, 16, 16)
        self.max_btn.setStyleSheet("background:#28C840;border-radius:8px;border:none;")
        self.max_btn.clicked.connect(self.toggle_max_restore)

        # rose icon beside buttons
        self.rose_icon = QLabel(self)
        if os.path.exists(ROSE_ICON_FILE):
            pix = QPixmap(ROSE_ICON_FILE).scaled(28,28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.rose_icon.setPixmap(pix)
        else:
            self.rose_icon.setText("🌹")
            self.rose_icon.setFont(QFont("Segoe UI Emoji", 14))
        self.rose_icon.setGeometry(92, 8, 28, 28)

        # title label (center) with opacity effect
        self.title_label = QLabel("ROSE", self)
        self.title_label.setFont(QFont("Segoe UI", 48, QFont.Bold))
        self.title_label.setStyleSheet("color: white;")
        self.title_label.setGeometry(0, self.height()//2 - 60, self.width(), 120)
        self.title_label.setAlignment(Qt.AlignCenter)
        # opacity effect (reliable animation)
        self._title_op = QGraphicsOpacityEffect(self.title_label)
        self.title_label.setGraphicsEffect(self._title_op)
        self._title_op.setOpacity(1.0)
        self._title_anim = None

        # response area
        self.response_area = QScrollArea(self)
        self.response_area.setGeometry(40, self.height()-220, self.width()-80, 160)
        self.response_area.setStyleSheet("background: rgba(0,0,0,0.55); border-radius:10px;")
        self.response_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.response_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.response_area.setWidgetResizable(True)
        self.response_content = QTextEdit()
        self.response_content.setReadOnly(True)
        self.response_content.setStyleSheet("background: transparent; color: white; border: none; padding: 8px;")
        self.response_content.setFont(QFont("Segoe UI", 12))
        self.response_area.setWidget(self.response_content)

        # stacked menu top-right
        self.menu_btn = QPushButton("⋯", self)
        self.menu_btn.setGeometry(self.width()-62, 10, 50, 30)
        self.menu_btn.setStyleSheet("background: rgba(255,255,255,0.12); color: white; border-radius:8px;")
        self.menu = QMenu(self)
        self.menu.addAction("Toggle Flow", lambda: self._run_js("toggleAnimation()"))
        self.menu.addAction("Change Speed", lambda: self._run_js("changeSpeed()"))
        self.menu.addAction("Toggle Glow", lambda: self._run_js("toggleGlow()"))
        self.menu_btn.setMenu(self.menu)

        # no hint label (removed per request)

        # fade title after 5s (use QTimer.singleShot)
        QTimer.singleShot(5000, self.fade_title)

        # geometry refresh timer
        self._update_geom_timer = QTimer(self)
        self._update_geom_timer.timeout.connect(self._on_geometry_refresh)
        self._update_geom_timer.start(120)

        # start background recognition
        self._start_background_listener()

        # optional "ready" speak (commented out)
        # speak("Ready")

    def _on_geometry_refresh(self):
        if self.web:
            self.web.setGeometry(0, 0, self.width(), self.height())
        self.title_label.setGeometry(0, self.height()//2 - 60, self.width(), 120)
        self.response_area.setGeometry(40, self.height()-220, self.width()-80, 160)
        self.menu_btn.setGeometry(self.width()-62, 10, 50, 30)

    def _run_js(self, js_code: str):
        if self.web:
            try:
                self.web.page().runJavaScript(js_code)
            except Exception as e:
                print("runJS error:", e)

    def append_response(self, text: str):
        cur = self.response_content
        cur.append(text)
        cur.verticalScrollBar().setValue(cur.verticalScrollBar().maximum())

    def fade_title(self):
        # animate opacity effect on title; hide when finished
        if self._title_anim and getattr(self._title_anim, "state", None):
            try:
                self._title_anim.stop()
            except Exception:
                pass
        anim = QPropertyAnimation(self._title_op, b"opacity")
        anim.setDuration(1200)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        anim.finished.connect(self.title_label.hide)
        anim.start()
        self._title_anim = anim

    def close_animated(self):
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(300)
        anim.setStartValue(self.windowOpacity())
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        anim.finished.connect(self._do_close)
        anim.start()
        self._fade_anim = anim

    def _do_close(self):
        global LISTENING, BG_LISTENER_STOP
        LISTENING = False
        if BG_LISTENER_STOP:
            try:
                BG_LISTENER_STOP(wait_for_stop=False)
            except Exception:
                pass
        save_persistent()
        self.close()

    def minimize_animated(self):
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(240)
        anim.setStartValue(self.windowOpacity())
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        def do_min(): self.showMinimized(); self.setWindowOpacity(0.0)
        anim.finished.connect(do_min)
        anim.start()
        self._fade_anim = anim

    def toggle_max_restore(self):
        if self.isMaximized():
            self.showNormal()
            self._is_max = False
        else:
            self.showMaximized()
            self._is_max = True

    # dragging + snap
    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self._drag_offset = ev.globalPosition().toPoint() - self.frameGeometry().topLeft()
            ev.accept()

    def mouseMoveEvent(self, ev):
        if self._drag_offset is not None and (ev.buttons() & Qt.LeftButton):
            self.move(ev.globalPosition().toPoint() - self._drag_offset)
            ev.accept()

    def mouseReleaseEvent(self, ev):
        if self._drag_offset is not None:
            self._snap_to_edge()
        self._drag_offset = None
        ev.accept()

    def _snap_to_edge(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x, y = self.x(), self.y()
        w, h = self.width(), self.height()
        target_x, target_y = x, y
        if x <= screen.left() + self.SNAP_MARGIN:
            target_x = screen.left() + 8
        if x + w >= screen.right() - self.SNAP_MARGIN:
            target_x = screen.right() - w - 8
        if y <= screen.top() + self.SNAP_MARGIN:
            target_y = screen.top() + 8
        if y + h >= screen.bottom() - self.SNAP_MARGIN:
            target_y = screen.bottom() - h - 8
        if (target_x, target_y) != (x, y):
            anim = QPropertyAnimation(self, b"geometry")
            anim.setDuration(self.SNAP_ANIM_MS)
            anim.setStartValue(self.geometry())
            anim.setEndValue(QRect(target_x, target_y, w, h))
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.start()
            self._snap_anim = anim

    # ---------------- voice listener ----------------
    def _start_background_listener(self):
        global BG_LISTENER_STOP
        if not sr:
            print("[WARN] speech_recognition not installed.")
            return
        recognizer_test = sr.Recognizer()
        names = sr.Microphone.list_microphone_names()
        mic_index = None
        bad = ("Sound Mapper", "Microsoft Sound Mapper", "Primary Sound Driver", "Stereo Mix")
        for i, name in enumerate(names):
            if any(bk in name for bk in bad):
                continue
            try:
                with sr.Microphone(device_index=i) as src:
                    recognizer_test.adjust_for_ambient_noise(src, duration=0.6)
                mic_index = i
                print("Using mic:", name)
                break
            except Exception:
                continue
        if mic_index is None and names:
            mic_index = 0
            print("Falling back to mic:", names[0])
        if mic_index is None:
            print("No microphone found.")
            self.append_response("[No microphone available]")
            return

        mic = sr.Microphone(device_index=mic_index)
        def callback(recognizer, audio):
            with TTS_LOCK:
                if TTS_PLAYING:
                    return
            try:
                text = recognizer.recognize_google(audio)
                if text and text.strip():
                    threading.Thread(target=handle_command, args=(text, self), daemon=True).start()
            except sr.UnknownValueError:
                return
            except Exception as e:
                print("Recognition callback error:", e)
                return
        try:
            rec = sr.Recognizer()
            BG_LISTENER_STOP = rec.listen_in_background(mic, callback, phrase_time_limit=4)
        except Exception as e:
            print("Background listen failed, fallback loop:", e)
            threading.Thread(target=self._fallback_listen, args=(mic,), daemon=True).start()

    def _fallback_listen(self, mic):
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
                except Exception as e:
                    print("SR error:", e)
                    time.sleep(0.5)
                    continue
            except Exception as e:
                print("Fallback mic error:", e)
                time.sleep(0.5)
                continue

    def closeEvent(self, ev: QCloseEvent):
        global LISTENING, BG_LISTENER_STOP
        LISTENING = False
        if BG_LISTENER_STOP:
            try:
                BG_LISTENER_STOP(wait_for_stop=False)
            except Exception:
                pass
        save_persistent()
        ev.accept()

# ---------------- run ----------------
def main():
    app = QApplication(sys.argv)
    hud = RoseHUD()
    hud.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
