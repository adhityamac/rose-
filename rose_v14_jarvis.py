# rose_v14_jarvis.py
"""
Rose v14 — Hybrid Jarvis
- Always-listening voice assistant (voice-first)
- Hybrid TTS: Edge TTS (online) / pyttsx3 fallback (offline)
- Plugin system: drop .py into plugins/, each plugin must implement register(api)
- Auto-updater: checks a configurable GitHub raw JSON for new version and a zip of plugins
- Profile & adaptation (profile.json)
- Compact HUD with mac-like buttons + animated background
"""

import os
import sys
import time
import json
import threading
import queue
import shutil
import zipfile
import asyncio
import importlib.util
import traceback
from typing import Dict, Callable, Any

# networking & helpers
import requests
import webbrowser
import wikipedia
import pyjokes
import pywhatkit

# GUI
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect, QListWidget
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QColor, QIcon, QPixmap, QPainter

# speech
import speech_recognition as sr

# TTS libs: optional
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except Exception:
    EDGE_TTS_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except Exception:
    PYTTSX3_AVAILABLE = False

# ------------------ CONFIG & PATHS ------------------
APP_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGINS_DIR = os.path.join(APP_DIR, "plugins")
os.makedirs(PLUGINS_DIR, exist_ok=True)

CONFIG_PATH = os.path.join(APP_DIR, "config.json")
PROFILE_PATH = os.path.join(APP_DIR, "profile.json")
LOCAL_VERSION = "0.1.0"  # bump this for updater comparisons

# Default configuration (you can edit config.json)
DEFAULT_CONFIG = {
    "auto_update_url": "",   # raw url to update.json on GitHub (example below)
    "check_update_interval_hours": 6,
    "tts_preference": "edge_then_pyttsx3",  # "pyttsx3_only" | "edge_then_pyttsx3"
    "edge_voice": "en-US-JennyNeural",
    "name": "Adhi",
    "github_token": "",  # optional if private repo
}

# create config/profile if missing
if not os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "w", encoding="utf8") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
with open(CONFIG_PATH, "r", encoding="utf8") as f:
    CONFIG = json.load(f)

if not os.path.exists(PROFILE_PATH):
    profile = {"name": CONFIG.get("name", "Adhi"), "usage_counts": {}, "last_update_check": 0}
    with open(PROFILE_PATH, "w", encoding="utf8") as f:
        json.dump(profile, f, indent=2)
with open(PROFILE_PATH, "r", encoding="utf8") as f:
    PROFILE = json.load(f)

# ------------------ SIGNALS ------------------
class Communicate(QObject):
    status = Signal(str)
    set_listening = Signal(bool)
    plugin_list_updated = Signal(list)

COMM = Communicate()

# ------------------ MIC / TTS LOCKS ------------------
mic_lock = threading.Lock()   # acquired while speaking to prevent self-capture

# ------------------ TTS IMPLEMENTATION (hybrid) ------------------
# Edge-tts async play wrapper
async def _edge_play(text, voice):
    comm = edge_tts.Communicate(text, voice)
    # use stream playback
    await comm.play()

def speak_edge(text: str):
    try:
        # run async in new event loop context
        asyncio.run(_edge_play(text, CONFIG.get("edge_voice", "en-US-JennyNeural")))
        return True
    except Exception as e:
        print("Edge TTS play failed:", e)
        return False

# pyttsx3 speak (blocking)
def speak_pyttsx3(text: str):
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        engine.say(text)
        engine.runAndWait()
        return True
    except Exception as e:
        print("pyttsx3 failed:", e)
        return False

def speak(text: str):
    """
    Main speak wrapper:
    - Acquire mic_lock (stop listening)
    - Try Edge TTS if allowed and available and online
    - Fallback to pyttsx3
    - Release mic_lock
    """
    def _do():
        try:
            mic_lock.acquire()
            COMM.status.emit(f"Rose (speaking): {text[:80]}{'...' if len(text)>80 else ''}")
            pref = CONFIG.get("tts_preference", "edge_then_pyttsx3")
            # detect online
            online = True
            try:
                requests.get("https://google.com", timeout=3)
            except Exception:
                online = False
            used = False
            if pref == "edge_then_pyttsx3" and EDGE_TTS_AVAILABLE and online:
                try:
                    if speak_edge(text):
                        used = True
                except Exception:
                    used = False
            if not used and PYTTSX3_AVAILABLE:
                speak_pyttsx3(text)
            elif not used:
                # last resort: write mp3 via edge_tts.save then play via os default
                if EDGE_TTS_AVAILABLE and online:
                    try:
                        asyncio.run(edge_tts.Communicate(text, CONFIG.get("edge_voice", "en-US-JennyNeural")).save("tmp_rose_tts.mp3"))
                        if sys.platform.startswith("win"):
                            os.startfile("tmp_rose_tts.mp3")
                        else:
                            # try `xdg-open` / `open`
                            opener = "xdg-open" if shutil.which("xdg-open") else "open"
                            os.system(f'{opener} tmp_rose_tts.mp3')
                    except Exception as e:
                        print("Failed to play fallback mp3:", e)
        finally:
            if mic_lock.locked():
                mic_lock.release()
            COMM.status.emit("idle")
    t = threading.Thread(target=_do, daemon=True)
    t.start()

# ------------------ PLUGIN SYSTEM ------------------
# API passed to plugins
class PluginAPI:
    def __init__(self, register_command: Callable[[str, Callable[[str], str]], None], speak_func: Callable[[str], None], config: dict, profile: dict):
        self.register_command = register_command
        self.speak = speak_func
        self.config = config
        self.profile = profile

# command registry: command -> handler(text) -> response str
COMMAND_HANDLERS: Dict[str, Callable[[str], str]] = {}

def register_command(trigger: str, handler: Callable[[str], str]):
    COMMAND_HANDLERS[trigger.lower()] = handler

def load_plugins():
    COMM.status.emit("Loading plugins...")
    loaded = []
    for fn in os.listdir(PLUGINS_DIR):
        if not fn.endswith(".py"):
            continue
        path = os.path.join(PLUGINS_DIR, fn)
        name = os.path.splitext(fn)[0]
        try:
            spec = importlib.util.spec_from_file_location(f"plugin_{name}", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "register") and callable(mod.register):
                api = PluginAPI(register_command, speak, CONFIG, PROFILE)
                mod.register(api)
                loaded.append(name)
            else:
                print(f"Plugin {name} missing register(api) function.")
        except Exception as e:
            print(f"Failed loading plugin {name}: {e}\n{traceback.format_exc()}")
    COMM.plugin_list_updated.emit(loaded)
    COMM.status.emit(f"Loaded plugins: {', '.join(loaded) if loaded else 'none'}")

# ------------------ AUTO-UPDATER (GitHub raw JSON) ------------------
# Expected remote JSON schema:
# { "version": "0.1.1", "plugins_zip": "https://raw.githubusercontent.com/you/repo/main/plugins.zip" }
def check_and_update_from_github():
    url = CONFIG.get("auto_update_url", "").strip()
    if not url:
        return
    try:
        COMM.status.emit("Checking updates...")
        headers = {}
        token = CONFIG.get("github_token", "").strip()
        if token:
            headers["Authorization"] = f"token {token}"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            COMM.status.emit("Update check failed (HTTP)")
            return
        data = r.json()
        remote_ver = data.get("version", "")
        if not remote_ver:
            COMM.status.emit("No version in update manifest")
            return
        if remote_ver <= LOCAL_VERSION:
            COMM.status.emit("No updates found")
            PROFILE["last_update_check"] = int(time.time())
            with open(PROFILE_PATH, "w", encoding="utf8") as f:
                json.dump(PROFILE, f, indent=2)
            return
        # remote version newer -> download plugins_zip
        zip_url = data.get("plugins_zip", "")
        if not zip_url:
            COMM.status.emit("No plugins zip in update manifest")
            return
        COMM.status.emit("Downloading plugin update...")
        zr = requests.get(zip_url, stream=True, timeout=30)
        if zr.status_code != 200:
            COMM.status.emit("Failed to download update zip")
            return
        tmp_zip = os.path.join(APP_DIR, "plugins_update.tmp.zip")
        with open(tmp_zip, "wb") as f:
            for chunk in zr.iter_content(4096):
                f.write(chunk)
        # extract to plugins (overwrite)
        try:
            with zipfile.ZipFile(tmp_zip, "r") as z:
                z.extractall(PLUGINS_DIR)
            COMM.status.emit("Plugins updated, reloading plugins...")
            load_plugins()
            # update profile last check
            PROFILE["last_update_check"] = int(time.time())
            with open(PROFILE_PATH, "w", encoding="utf8") as f:
                json.dump(PROFILE, f, indent=2)
            # optional: restart app to pick core updates (we only update plugins here)
        except Exception as e:
            COMM.status.emit(f"Failed extract: {e}")
        finally:
            try:
                os.remove(tmp_zip)
            except:
                pass
    except Exception as e:
        COMM.status.emit(f"Update error: {e}")

def periodic_update_checker(interval_hours=6):
    while True:
        try:
            check_and_update_from_github()
        except Exception:
            pass
        time.sleep(interval_hours * 3600)

# ------------------ HELPERS: YouTube play (no Selenium) ------------------
import re
def play_youtube_first(song: str) -> str:
    try:
        q = requests.utils.requote_uri(song)
        url = f"https://www.youtube.com/results?search_query={q}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            m = re.search(r"\/watch\?v=([A-Za-z0-9_-]{11})", r.text)
            if m:
                vid = m.group(1)
                webbrowser.open(f"https://www.youtube.com/watch?v={vid}")
                return f"Playing {song} on YouTube"
        # fallback
        pywhatkit.playonyt(song)
        return f"Playing {song} on YouTube (fallback)"
    except Exception as e:
        return f"Failed to play: {e}"

# ------------------ CORE COMMAND PROCESSOR ------------------
def process_command(raw_text: str) -> str:
    text = raw_text.lower().strip()
    # update profile usage
    PROFILE["usage_counts"][text] = PROFILE["usage_counts"].get(text, 0) + 1
    with open(PROFILE_PATH, "w", encoding="utf8") as f:
        json.dump(PROFILE, f, indent=2)

    # plugin handlers first (exact trigger or startswith)
    for trigger, handler in list(COMMAND_HANDLERS.items()):
        if text == trigger or text.startswith(trigger + " "):
            try:
                return handler(raw_text)
            except Exception as e:
                return f"Plugin handler error: {e}"

    # builtin commands
    if text.startswith("open "):
        target = text.replace("open ", "", 1).strip()
        if "youtube" in target:
            webbrowser.open("https://www.youtube.com")
            return "Opened YouTube"
        if "brave" in target:
            path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
            if os.path.exists(path):
                os.startfile(path); return "Opened Brave"
            else:
                webbrowser.open("https://www.google.com"); return "Brave not found, opened Google"
        if "chrome" in target:
            path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            if os.path.exists(path):
                os.startfile(path); return "Opened Chrome"
            else:
                webbrowser.open("https://www.google.com"); return "Chrome not found, opened Google"
        webbrowser.open(f"https://www.google.com/search?q={requests.utils.requote_uri(target)}")
        return f"Searched web for {target}"

    if text.startswith("play "):
        song = text.replace("play ", "", 1).strip()
        return play_youtube_first(song)

    if "weather" in text:
        # quick weather via wttr.in
        try:
            loc = "auto"
            m = re.search(r"weather in (.+)$", text)
            if m:
                loc = requests.utils.requote_uri(m.group(1).strip())
            r = requests.get(f"https://wttr.in/{loc}?format=3", timeout=6)
            if r.status_code == 200:
                return r.text
            else:
                return "Could not fetch weather."
        except Exception as e:
            return f"Weather error: {e}"

    if "news" in text:
        try:
            url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
            r = requests.get(url, timeout=6)
            if r.status_code == 200:
                titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", r.text)
                # first item is "Google News" header, skip
                if len(titles) > 1:
                    top = titles[1:6]
                    return "Top headlines: " + " — ".join(top)
            return "Could not fetch news."
        except Exception as e:
            return f"News error: {e}"

    if "joke" in text:
        return pyjokes.get_joke()

    if any(g in text for g in ("hello","hi","hey")):
        return f"Hello {PROFILE.get('name','Adhi')}, how can I help you?"

    if text in ("bye","goodbye","exit","quit","stop"):
        return "Goodbye"

    # fallback: echo
    return f"I heard: {raw_text}"

# ------------------ LISTENER THREAD (always on) ------------------
class Listener(threading.Thread):
    def __init__(self, comm: Communicate, start_listen=True):
        super().__init__(daemon=True)
        self.comm = comm
        self.running = True
        self.listening = start_listen
        self.recognizer = sr.Recognizer()

    def run(self):
        while self.running:
            if not self.listening:
                time.sleep(0.3)
                continue
            try:
                # ensure mic_lock not held; we acquire it for short time to open mic
                with mic_lock:
                    with sr.Microphone() as source:
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
                        audio = self.recognizer.listen(source, timeout=6, phrase_time_limit=8)
                # recognize outside the mic_lock so speaking can acquire lock later
                try:
                    text = self.recognizer.recognize_google(audio)
                except sr.UnknownValueError:
                    continue
                except Exception as e:
                    print("SR error:", e)
                    continue
                if text and text.strip():
                    self.comm.status.emit(f"You: {text}")
                    # process command in background
                    threading.Thread(target=self.handle_command, args=(text,), daemon=True).start()
            except Exception as e:
                # catch overall listening errors and continue
                continue

    def handle_command(self, text):
        response = process_command(text)
        self.comm.status.emit(f"Rose: {response}")
        if response == "Goodbye":
            speak("Goodbye. Shutting down.")
            time.sleep(0.6)
            os._exit(0)
        else:
            speak(response)

    def stop(self):
        self.running = False

# ------------------ HUD UI ------------------
class HUD(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen.width()-540, 20, 520, 260)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._phase = 0.0

        # layout
        main = QVBoxLayout()
        top = QHBoxLayout()
        # circular buttons (top-left)
        self.btn_close = QPushButton("", self)
        self.btn_close.setFixedSize(16,16)
        self.btn_close.setStyleSheet("background-color:#FF5F57;border-radius:8px;")
        self.btn_close.clicked.connect(self._quit)
        top.addWidget(self.btn_close)
        self.btn_min = QPushButton("", self)
        self.btn_min.setFixedSize(16,16)
        self.btn_min.setStyleSheet("background-color:#FFBD2E;border-radius:8px;")
        self.btn_min.clicked.connect(self._hide)
        top.addWidget(self.btn_min)
        self.btn_mic = QPushButton("", self)
        self.btn_mic.setFixedSize(16,16)
        self.btn_mic.setStyleSheet("background-color:#28C940;border-radius:8px;")
        self.btn_mic.clicked.connect(self._toggle_mic)
        top.addWidget(self.btn_mic)
        top.addStretch()
        main.addLayout(top)

        # status and history
        self.status = QLabel("Rose (v14) — initializing...", self)
        self.status.setStyleSheet("color: #D9B3FF; font-family: Consolas; font-size: 12pt;")
        main.addWidget(self.status)
        self.listwidget = QListWidget(self)
        self.listwidget.setFixedHeight(140)
        main.addWidget(self.listwidget)

        # plugin list
        self.plugins_label = QLabel("Plugins:", self)
        self.plugins_label.setStyleSheet("color: #EDEDED; font-family: Consolas; font-size: 10pt;")
        main.addWidget(self.plugins_label)
        self.plugin_list_widget = QListWidget(self)
        self.plugin_list_widget.setFixedHeight(40)
        main.addWidget(self.plugin_list_widget)

        self.setLayout(main)

        # glow effect
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(28)
        glow.setColor(QColor("#B24BFF"))
        glow.setOffset(0)
        self.setGraphicsEffect(glow)

        # timers
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate)
        self._anim_timer.start(40)

        self._scroll_timer = QTimer(self)
        self._scroll_timer.timeout.connect(self._ensure_bottom)
        self._scroll_timer.start(500)

        # connect signals
        COMM.status.connect(self._append_status)
        COMM.set_listening.connect(self._set_listening_label)
        COMM.plugin_list_updated.connect(self._update_plugins)

        # initial load
        load_plugins()
        COMM.status.emit("Ready")
        # start updater thread if configured
        if CONFIG.get("auto_update_url"):
            t = threading.Thread(target=periodic_update_checker, args=(CONFIG.get("check_update_interval_hours", 6),), daemon=True)
            t.start()

    def _animate(self):
        # animated gradient background
        import math
        self._phase += 0.01
        a = int((math.sin(self._phase) + 1) * 40) + 20
        b = int((math.cos(self._phase * 1.3) + 1) * 30) + 10
        css = f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba({10+a},{5+b},{40+a},230), stop:1 rgba({5+b},{30+a},{20+b},220)); border-radius:12px;"
        self.setStyleSheet(css)

    def _append_status(self, text):
        self.listwidget.addItem(text)
        # keep last 10
        while self.listwidget.count() > 10:
            self.listwidget.takeItem(0)

    def _ensure_bottom(self):
        self.listwidget.scrollToBottom()
        self.plugin_list_widget.scrollToBottom()

    def _set_listening_label(self, flag: bool):
        self.status.setText("Listening: ON" if flag else "Listening: OFF")
        if flag:
            self.btn_mic.setStyleSheet("background-color:#28C940;border-radius:8px;")
        else:
            self.btn_mic.setStyleSheet("background-color:#7a7a7a;border-radius:8px;")

    def _update_plugins(self, plugins):
        self.plugin_list_widget.clear()
        for p in plugins:
            self.plugin_list_widget.addItem(p)

    def _toggle_mic(self):
        # toggle mic listening in listener thread
        # find the running listener and toggle
        # We keep a global reference below
        global LISTENER_THREAD_INSTANCE
        if LISTENER_THREAD_INSTANCE:
            LISTENER_THREAD_INSTANCE.listening = not LISTENER_THREAD_INSTANCE.listening
            COMM.set_listening.emit(LISTENER_THREAD_INSTANCE.listening)

    def _hide(self):
        self.hide()

    def _quit(self):
        speak("Goodbye. Shutting down.")
        time.sleep(0.4)
        try:
            LISTENER_THREAD_INSTANCE.stop()
        except:
            pass
        QApplication.quit()
        sys.exit(0)

# ------------------ INIT & RUN ------------------
LISTENER_THREAD_INSTANCE = None

def main():
    global LISTENER_THREAD_INSTANCE
    app = QApplication(sys.argv)
    hud = HUD()
    hud.show()
    # start listener
    LISTENER_THREAD_INSTANCE = Listener(COMM, start_listen=True)
    LISTENER_THREAD_INSTANCE.start()
    # notify greeting (status already updated)
    COMM.status.emit(f"Hello {PROFILE.get('name','Adhi')} — ready.")
    # speak greeting
    speak(f"Hello {PROFILE.get('name','Adhi')}. I am Rose. I am listening.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
