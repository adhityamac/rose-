# rose_v26_5_ui_plus.py
# Rose v26.5+ — UI + settings + mic reselect + optional Spotify Web API (fallback: media keys)
# Requirements:
#   pip install PySide6 speechrecognition edge-tts pytube
# Optional:
#   pip install spotipy

import sys
import os
import math
import time
import asyncio
import threading
import webbrowser
import platform
import subprocess
import random
from typing import Optional, List

from PySide6.QtCore import Qt, QTimer, QRect, QEasingCurve, QPropertyAnimation, QPoint
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QGraphicsDropShadowEffect,
    QDialog, QVBoxLayout, QHBoxLayout, QSlider, QComboBox, QFormLayout, QLineEdit, QMessageBox, QCheckBox
)
from PySide6.QtGui import QFont, QPainter, QLinearGradient, QColor, QBrush, QPixmap, QPainterPath, QPaintEvent

import speech_recognition as sr
import edge_tts
from pytube import Search

# Try optional spotify web api
SPOTIFY_AVAILABLE = False
try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    SPOTIFY_AVAILABLE = True
except Exception:
    SPOTIFY_AVAILABLE = False

# --------------- Globals ---------------
LISTENING = True
TTS_PLAYING = False
TTS_LOCK = threading.Lock()
BG_LISTENER_STOP = None
HUD_REF: Optional["NeonHUD"] = None

# HUD sizing/docking
DEFAULT_WIDTH = 540
DEFAULT_HEIGHT = 320
MIN_WIDTH = 380
MIN_HEIGHT = 220
DOCK_THRESHOLD = 36

# ---------------- Helpers ----------------
def estimate_tts_duration(text: str) -> float:
    words = len(text.split())
    return max(0.5, words / 2.8)

def _play_file_nonblocking(path: str):
    try:
        if platform.system() == "Windows":
            subprocess.Popen(["start", path], shell=True)
        elif platform.system() == "Darwin":
            subprocess.Popen(["afplay", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        print("Playback error:", e)

# ---------------- TTS ----------------
async def _edge_save(text: str, filename: str = "speech.mp3"):
    comm = edge_tts.Communicate(text, "en-US-JennyNeural")
    await comm.save(filename)

def speak(text: str):
    """Generate TTS and play it. Triggers HUD visual effects if HUD_REF is set."""
    def runner():
        global TTS_PLAYING, HUD_REF
        # ask HUD to spawn petals right before voice
        try:
            if HUD_REF:
                QTimer.singleShot(0, lambda: HUD_REF._trigger_speaking_effects(text))
        except Exception:
            pass

        with TTS_LOCK:
            TTS_PLAYING = True
        try:
            asyncio.run(_edge_save(text, "speech.mp3"))
            _play_file_nonblocking("speech.mp3")
            time.sleep(estimate_tts_duration(text) + 0.35)
        except Exception as e:
            print("TTS error:", e)
        finally:
            with TTS_LOCK:
                TTS_PLAYING = False
    threading.Thread(target=runner, daemon=True).start()

# ---------------- YouTube ----------------
def play_youtube_song(song: str):
    try:
        q = song.strip()
        if not q:
            webbrowser.open("https://www.youtube.com")
            return
        s = Search(q)
        if not getattr(s, "results", None):
            webbrowser.open(f"https://www.youtube.com/results?search_query={q.replace(' ','+')}")
            return
        first = s.results[0]
        url = getattr(first, "watch_url", None) or f"https://www.youtube.com/watch?v={first.video_id}"
        webbrowser.open(url)
    except Exception as e:
        print("YT error", e)
        webbrowser.open(f"https://www.youtube.com/results?search_query={song.replace(' ','+')}")

# ---------------- Spotify control (two modes) ----------------
def _send_media_key_windows(vk_code: int):
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        INPUT_KEYBOARD = 1
        KEYEVENTF_EXTENDEDKEY = 0x0001
        KEYEVENTF_KEYUP = 0x0002

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = (("wVk", wintypes.WORD),
                        ("wScan", wintypes.WORD),
                        ("dwFlags", wintypes.DWORD),
                        ("time", wintypes.DWORD),
                        ("dwExtraInfo", wintypes.ULONG_PTR))

        class INPUT(ctypes.Structure):
            _fields_ = (("type", wintypes.DWORD),
                        ("ki", KEYBDINPUT))

        ki = KEYBDINPUT(wVk=vk_code, wScan=0, dwFlags=KEYEVENTF_EXTENDEDKEY, time=0, dwExtraInfo=0)
        x = INPUT(type=INPUT_KEYBOARD, ki=ki)
        user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

        ki_up = KEYBDINPUT(wVk=vk_code, wScan=0, dwFlags=KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, time=0, dwExtraInfo=0)
        x_up = INPUT(type=INPUT_KEYBOARD, ki=ki_up)
        user32.SendInput(1, ctypes.byref(x_up), ctypes.sizeof(x_up))
    except Exception as e:
        print("Media key send failed:", e)

def spotify_media_play_pause():
    try:
        if platform.system() == "Windows":
            _send_media_key_windows(0xB3)
        elif platform.system() == "Darwin":
            subprocess.Popen(["osascript", "-e", 'tell application "Spotify" to playpause'])
        else:
            os.system("playerctl play-pause")
    except Exception as e:
        print("Spotify local play/pause error:", e)

def spotify_media_next():
    try:
        if platform.system() == "Windows":
            _send_media_key_windows(0xB0)
        elif platform.system() == "Darwin":
            subprocess.Popen(["osascript", "-e", 'tell application "Spotify" to next track'])
        else:
            os.system("playerctl next")
    except Exception as e:
        print("Spotify next error:", e)

def spotify_media_prev():
    try:
        if platform.system() == "Windows":
            _send_media_key_windows(0xB1)
        elif platform.system() == "Darwin":
            subprocess.Popen(["osascript", "-e", 'tell application "Spotify" to previous track'])
        else:
            os.system("playerctl previous")
    except Exception as e:
        print("Spotify prev error:", e)

# Optional Spotify Web API wrapper (if spotipy present and env vars set)
SPOTIFY_OAUTH = None
SP_CLIENT = None
if SPOTIFY_AVAILABLE:
    try:
        client_id = os.getenv("SPOTIPY_CLIENT_ID", "")
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET", "")
        redirect = os.getenv("SPOTIPY_REDIRECT_URI", "http://localhost:8888/callback")
        if client_id and client_secret:
            SPOTIFY_OAUTH = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect, scope="user-modify-playback-state,user-read-playback-state,user-read-currently-playing")
            SP_CLIENT = spotipy.Spotify(auth_manager=SPOTIFY_OAUTH)
            print("Spotify Web API initialized.")
        else:
            SPOTIFY_AVAILABLE = False
    except Exception as e:
        print("Spotify Web init error:", e)
        SPOTIFY_AVAILABLE = False

def spotify_web_play_search_and_play(query: str):
    """Search using Spotify Web API and play on active device if possible."""
    if not SPOTIFY_AVAILABLE or SP_CLIENT is None:
        print("Spotify Web API not configured.")
        return False
    try:
        result = SP_CLIENT.search(q=query, type="track", limit=1)
        items = result.get("tracks", {}).get("items", [])
        if not items:
            return False
        uri = items[0]["uri"]
        # try to start playback on user's active device
        SP_CLIENT.start_playback(uris=[uri])
        return True
    except Exception as e:
        print("Spotify Web play error:", e)
        return False

# --------------- Volume & system ---------------
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

# ---------------- Command processor ----------------
def handle_command(cmd: str, hud_ref: Optional["NeonHUD"] = None):
    if not cmd:
        return
    cmd_norm = cmd.lower().strip()
    if hud_ref:
        hud_ref.update_response(f"You said: {cmd_norm}")

    # Spotify voice commands (prefer web API if available & configured)
    if "spotify" in cmd_norm:
        # play/pause
        if any(x in cmd_norm for x in ("play", "pause", "toggle", "play/pause")):
            # try web API if configured
            if SPOTIFY_AVAILABLE and SP_CLIENT:
                # try searching for specific play request: "play <song> on spotify"
                # if song specified, search then play; else toggle
                if cmd_norm.startswith("play ") and "spotify" in cmd_norm:
                    q = cmd_norm.replace("play", "").replace("spotify", "").strip()
                    if q:
                        ok = spotify_web_play_search_and_play(q)
                        if ok:
                            speak(f"Playing {q} on Spotify")
                            return
                # fallback to toggle
            spotify_media_play_pause()
            speak("Toggling Spotify")
            return
        if any(x in cmd_norm for x in ("next", "skip")):
            spotify_media_next(); speak("Next track"); return
        if any(x in cmd_norm for x in ("previous", "prev", "back")):
            spotify_media_prev(); speak("Previous track"); return

    # Play on YouTube (default for "play <song>")
    if cmd_norm.startswith("play "):
        if "spotify" in cmd_norm:
            # handled above
            pass
        else:
            song = cmd_norm.replace("play", "", 1).replace("on youtube", "").replace("youtube", "").strip()
            if song:
                if hud_ref: hud_ref.update_response(f"Playing {song} on YouTube...")
                speak(f"Playing {song} on YouTube")
                play_youtube_song(song)
                return

    # Volume
    if any(x in cmd_norm for x in ("volume up", "increase volume", "higher volume")):
        adjust_volume("up"); speak("Volume increased")
        if hud_ref: hud_ref.update_response("Volume increased"); return
    if any(x in cmd_norm for x in ("volume down", "decrease volume", "lower volume")):
        adjust_volume("down"); speak("Volume decreased")
        if hud_ref: hud_ref.update_response("Volume decreased"); return
    if "mute" in cmd_norm and "unmute" not in cmd_norm:
        adjust_volume("mute"); speak("Muted")
        if hud_ref: hud_ref.update_response("Muted"); return
    if "unmute" in cmd_norm:
        adjust_volume("unmute"); speak("Unmuted")
        if hud_ref: hud_ref.update_response("Unmuted"); return

    # System
    if "shutdown" in cmd_norm:
        if hud_ref: hud_ref.update_response("Shutting down...")
        speak("Shutting down the system"); system_action("shutdown"); return
    if "restart" in cmd_norm:
        if hud_ref: hud_ref.update_response("Restarting...")
        speak("Restarting the system"); system_action("restart"); return

    # Open apps
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
        code_path = rf"C:\Users\{os.getlogin()}\AppData\Local\Programs\Microsoft VS Code\Code.exe"
        if platform.system() == "Windows" and os.path.exists(code_path):
            subprocess.Popen([code_path])
        else:
            webbrowser.open("https://code.visualstudio.com")
        return

    # Greetings
    if any(g in cmd_norm for g in ("hello", "hi", "hey")):
        speak("Hello. I'm Rose, your healer.")
        if hud_ref: hud_ref.update_response("Hello. I'm Rose, your healer.")
        return

    # Fallback
    speak(f"I heard: {cmd_norm}")
    if hud_ref: hud_ref.update_response(f"I heard: {cmd_norm}")

# ---------------- Settings dialog ----------------
class SettingsDialog(QDialog):
    def __init__(self, parent: "NeonHUD"):
        super().__init__(parent)
        self.setWindowTitle("Rose Settings")
        self.setModal(True)
        self.parent = parent
        self.setMinimumWidth(420)
        layout = QVBoxLayout()

        form = QFormLayout()

        # theme intensity slider (0..100)
        self.theme_slider = QSlider(Qt.Horizontal)
        self.theme_slider.setRange(0, 100)
        self.theme_slider.setValue(int(parent.theme_intensity * 100))
        form.addRow("Theme intensity", self.theme_slider)

        # waveform sensitivity
        self.wave_slider = QSlider(Qt.Horizontal)
        self.wave_slider.setRange(1, 200)
        self.wave_slider.setValue(int(parent.waveform_sensitivity * 100))
        form.addRow("Waveform sensitivity", self.wave_slider)

        # mic device selector
        self.mic_combo = QComboBox()
        mics = sr.Microphone.list_microphone_names()
        self.mic_combo.addItem("Auto-detect")
        for m in mics:
            self.mic_combo.addItem(m)
        # select current
        if parent.forced_mic_index is None:
            self.mic_combo.setCurrentIndex(0)
        else:
            idx = parent.forced_mic_index + 1
            if idx < self.mic_combo.count():
                self.mic_combo.setCurrentIndex(idx)
        form.addRow("Microphone override", self.mic_combo)

        # spotify web toggle
        self.spotify_checkbox = QCheckBox("Enable Spotify Web API (requires env vars)")
        self.spotify_checkbox.setChecked(bool(SPOTIFY_AVAILABLE and SP_CLIENT))
        form.addRow(self.spotify_checkbox)

        layout.addLayout(form)

        btns = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        save_btn.clicked.connect(self.on_save)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)
        self.setLayout(layout)

    def on_save(self):
        # theme intensity
        val = self.theme_slider.value()
        self.parent.theme_intensity = val / 100.0
        self.parent.waveform_sensitivity = self.wave_slider.value() / 100.0
        # mic override
        idx = self.mic_combo.currentIndex()
        if idx == 0:
            self.parent.forced_mic_index = None
        else:
            self.parent.forced_mic_index = idx - 1
        # spotify web toggle - user must have env vars
        # just notify user; actual SP_CLIENT config is global
        if self.spotify_checkbox.isChecked() and not SPOTIFY_AVAILABLE:
            QMessageBox.information(self, "Spotify", "Spotify Web API not configured or spotipy not installed.")
        self.accept()

# ---------------- NeonHUD ----------------
class NeonHUD(QWidget):
    def __init__(self):
        super().__init__()
        global HUD_REF
        HUD_REF = self

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)

        # visual params
        self.theme_intensity = 0.9   # 0..1
        self.waveform_sensitivity = 1.0
        self.forced_mic_index: Optional[int] = None

        # title & response
        self.title_label = QLabel("ROSE", self)
        self.title_label.setFont(QFont("Montserrat", 30, QFont.Bold))
        self.title_label.setStyleSheet("color: white;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setGeometry(0, 40, self.width(), 54)

        self.response_label = QLabel("", self)
        self.response_label.setFont(QFont("Montserrat", 14))
        self.response_label.setStyleSheet("color: white;")
        self.response_label.setAlignment(Qt.AlignCenter)
        self.response_label.setWordWrap(True)
        self.response_label.setGeometry(20, 140, self.width() - 40, 100)

        # top-left mac buttons
        self.close_btn = QPushButton(self)
        self.close_btn.setGeometry(10, 10, 16, 16)
        self.close_btn.setStyleSheet(self._btn_style("#FF5C5C"))
        self.close_btn.clicked.connect(self._animate_close)

        self.min_btn = QPushButton(self)
        self.min_btn.setGeometry(36, 10, 16, 16)
        self.min_btn.setStyleSheet(self._btn_style("#FFBD44"))
        self.min_btn.clicked.connect(self._animate_minimize)

        self.max_btn = QPushButton(self)
        self.max_btn.setGeometry(62, 10, 16, 16)
        self.max_btn.setStyleSheet(self._btn_style("#28C840"))
        self.max_btn.clicked.connect(self.toggle_max_restore)

        # settings button (tiny) top-right
        self.settings_btn = QPushButton("⚙", self)
        self.settings_btn.setGeometry(self.width() - 40, 8, 32, 20)
        self.settings_btn.setStyleSheet("""
            color: white;
            background: rgba(255,255,255,8);
            border-radius:6px;
        """)
        self.settings_btn.clicked.connect(self.open_settings)

        # mic reselect button
        self.mic_btn = QPushButton("Mic", self)
        self.mic_btn.setGeometry(self.width() - 84, 8, 36, 20)
        self.mic_btn.setStyleSheet("""
            color: white;
            background: rgba(255,255,255,6);
            border-radius:6px;
        """)
        self.mic_btn.clicked.connect(self.reselect_mic_dialog)

        # peach rose icon top-left but not overlapping buttons
        self.icon_pix = self._build_peach_rose_icon(36)
        self.icon_x = 96
        self.icon_y = 6
        self.icon_angle = 0.0
        self._icon_timer = QTimer(self)
        self._icon_timer.timeout.connect(self._icon_tick)
        self._icon_timer.start(80)

        # petals
        self.petal_list: List[dict] = []

        # animation states
        self._grad_phase = 0.0
        self._wave_phase = 0.0
        self._fade_anim = None

        # timers
        self._grad_timer = QTimer(self)
        self._grad_timer.timeout.connect(self._on_grad_tick)
        self._grad_timer.start(36)

        self._wave_timer = QTimer(self)
        self._wave_timer.timeout.connect(self._on_wave_tick)
        self._wave_timer.start(30)

        # dragging/docking
        self._drag_pos = None

        # start mic listener (with optional forced index)
        self._start_background_listener(self.forced_mic_index)

        # greeting after show (animated)
        QTimer.singleShot(700, self._greet)

        # fade-in
        self.setWindowOpacity(0.0)
        self._animate_show()

        # drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(shadow)

    # UI helpers
    def _btn_style(self, color_hex: str) -> str:
        return f"""
            background-color: {color_hex};
            border-radius: 7px;
            border: 1px solid rgba(255,255,255,0.06);
        """

    def _build_peach_rose_icon(self, size_px: int) -> QPixmap:
        pix = QPixmap(size_px, size_px)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        center = size_px / 2
        petal_color = QColor(255, 179, 153)
        stroke = QColor(210, 120, 100)
        p.setBrush(petal_color)
        p.setPen(stroke)
        for i in range(5):
            angle = i * (360 / 5)
            rad = math.radians(angle)
            x = center + math.cos(rad) * (size_px * 0.12)
            y = center + math.sin(rad) * (size_px * 0.12)
            rect = QRect(int(x - size_px * 0.22), int(y - size_px * 0.22),
                         int(size_px * 0.44), int(size_px * 0.44))
            p.drawEllipse(rect)
        p.setBrush(QColor(255, 140, 120))
        p.drawEllipse(int(center - size_px * 0.12), int(center - size_px * 0.12),
                      int(size_px * 0.24), int(size_px * 0.24))
        p.end()
        return pix

    # Greeting
    def _greet(self):
        greeting = "Hi, I'm Rose, your healer. How can I assist you?"
        self._type_animate_response(greeting)
        # spawn petals + speak (pre-warm)
        self._trigger_speaking_effects(greeting)
        speak(greeting)

    def _type_animate_response(self, text: str, interval_ms: int = 28):
        # simple typewriter effect on response_label
        self.response_label.setText("")
        def worker():
            cur = ""
            for ch in text:
                cur += ch
                QTimer.singleShot(0, lambda c=cur: self.response_label.setText(c))
                time.sleep(interval_ms / 1000.0)
        threading.Thread(target=worker, daemon=True).start()

    def update_response(self, text: str):
        # immediate update (no typing)
        self.response_label.setText(text)

    # Animations
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
        anim.setDuration(340)
        anim.setStartValue(self.windowOpacity())
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        def do_close():
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
            self.showMinimized()
            self.setWindowOpacity(0.0)
        anim.finished.connect(do_min)
        anim.start()
        self._fade_anim = anim

    def toggle_max_restore(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _on_grad_tick(self):
        self._grad_phase += 0.007 * (0.5 + 0.5 * self.theme_intensity)
        if self._grad_phase > math.tau:
            self._grad_phase -= math.tau
        self.update()

    def _on_wave_tick(self):
        self._wave_phase += 0.16 * (0.8 + 0.4 * self.waveform_sensitivity)
        if self._wave_phase > math.tau:
            self._wave_phase -= math.tau
        self.update(QRect(20, self.height() - 110, self.width() - 40, 100))

    def _icon_tick(self):
        self.icon_angle = (self.icon_angle + 0.7) % 360
        self.update(QRect(self.icon_x, self.icon_y, 48, 48))

    def paintEvent(self, ev: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        # matte black base
        base = QColor(8, 8, 10, 220)
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, 20, 20)
        painter.fillPath(path, base)

        # frosted glass overlay simulation
        painter.fillPath(path, QColor(255, 255, 255, int(6 * (0.6 + 0.4 * self.theme_intensity))))

        # animated neon border (purple->pink->blue)
        phase = self._grad_phase
        c1 = QColor.fromHsv(int((270 + math.sin(phase) * 12) % 360), int(180*self.theme_intensity), 200)
        c2 = QColor.fromHsv(int((320 + math.cos(phase*1.2) * 12) % 360), int(200*self.theme_intensity), 210)
        border_grad = QLinearGradient(0, 0, w, 0)
        border_grad.setColorAt(0.0, c1)
        border_grad.setColorAt(0.5, c2)
        border_grad.setColorAt(1.0, c1)
        pen = painter.pen()
        pen.setWidth(2)
        pen.setBrush(border_grad)
        painter.setPen(pen)
        painter.drawRoundedRect(1, 1, w - 2, h - 2, 20, 20)

        # inner subtle glow
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 8))
        painter.drawRoundedRect(10, 10, w - 20, h - 20, 16, 16)

        # neon corner accents
        accent_size = 12
        corner_grad = QLinearGradient(0, 0, accent_size, accent_size)
        corner_grad.setColorAt(0.0, c1)
        corner_grad.setColorAt(1.0, c2)
        painter.setBrush(corner_grad)
        painter.drawEllipse(6, 6, 8, 8)  # top-left tiny

        # draw rotating peach icon
        painter.save()
        painter.translate(self.icon_x + self.icon_pix.width()/2, self.icon_y + self.icon_pix.height()/2)
        painter.rotate(self.icon_angle)
        painter.translate(- (self.icon_x + self.icon_pix.width()/2), - (self.icon_y + self.icon_pix.height()/2))
        painter.drawPixmap(self.icon_x, self.icon_y, self.icon_pix)
        painter.restore()

        # title glow and color (speaking changes color)
        with TTS_LOCK:
            speaking = TTS_PLAYING
        base_col = QColor(255, 190, 180) if speaking else QColor(190, 0, 255)

        title_rect = self.title_label.geometry()
        for i in range(4, 0, -1):
            alpha = max(6, 36 // i)
            col = QColor(base_col.red(), base_col.green(), base_col.blue(), alpha)
            painter.setPen(col)
            painter.setFont(QFont("Montserrat", 30 + i, QFont.Bold))
            painter.drawText(title_rect, Qt.AlignCenter, self.title_label.text())
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Montserrat", 30, QFont.Bold))
        painter.drawText(title_rect, Qt.AlignCenter, self.title_label.text())

        # waveform draw
        self._draw_waveform(painter, speaking)

        # petals
        self._draw_petals(painter)

    def _draw_waveform(self, painter: QPainter, active: bool):
        bar_count = max(8, int(self.width() / 26))
        rect_w = self.width() - 60
        rect_h = 68 if active else 36
        x0 = 30
        y0 = self.height() - 120 if active else self.height() - 90
        spacing = rect_w / bar_count
        for i in range(bar_count):
            phase = self._wave_phase + (i * 0.28)
            if active:
                amp = 0.25 + 0.75 * (0.5 + 0.5 * math.sin(phase * 1.6))
                amp *= (0.8 + 0.6 * self.waveform_sensitivity)
            else:
                amp = 0.45 + 0.12 * math.sin(phase * 0.9)
            bar_h = rect_h * amp
            bx = int(x0 + i * spacing + spacing * 0.12)
            bw = int(spacing * 0.72)
            by = int(y0 + (rect_h - bar_h) / 2)
            alpha = int(110 + 80 * amp) if active else int(60 + 40 * amp)
            hue = 300 + 30 * math.sin(phase + self._grad_phase)
            col = QColor.fromHsv(int(hue) % 360, int(180*self.theme_intensity), 230, alpha)
            painter.setBrush(col)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(bx, by, bw, int(bar_h), 6, 6)

    def _draw_petals(self, painter: QPainter):
        now = time.time()
        self.petal_list = [p for p in self.petal_list if now < p['end']]
        for p in self.petal_list:
            progress = (now - p['start']) / (p['end'] - p['start'])
            x = p['x'] + p['dx'] * progress
            y = p['y'] + p['dy'] * progress + (progress**1.5) * 30
            alpha = int(255 * (1 - progress))
            col = QColor(255, 190, 170, alpha)
            painter.setBrush(col)
            painter.setPen(Qt.NoPen)
            size = max(4, int(6 * (1 - progress) + 3))
            painter.drawEllipse(int(x), int(y), size, size)

    def _trigger_speaking_effects(self, text: str):
        now = time.time()
        cnt = min(12, max(6, len(text.split()) // 3))
        for i in range(cnt):
            self.petal_list.append({
                'x': self.icon_x + random.randint(-6, 18),
                'y': self.icon_y + random.randint(6, 18),
                'dx': random.uniform(-26, 26),
                'dy': random.uniform(40, 96),
                'start': now + random.uniform(0.0, 0.06 * i),
                'end': now + 0.9 + (i * 0.05)
            })

    # --------------- Microphone management ---------------
    def _start_background_listener(self, forced_index: Optional[int] = None):
        recognizer_test = sr.Recognizer()
        available = sr.Microphone.list_microphone_names()
        mic_index = None

        if forced_index is not None and 0 <= forced_index < len(available):
            mic_index = forced_index
            print("Forced mic index selected:", mic_index, available[mic_index])
        else:
            # prefer non-virtual devices
            bad_keywords = ("Sound Mapper", "Microsoft Sound Mapper", "Primary Sound Driver", "Stereo Mix")
            for i, name in enumerate(available):
                if any(bk in name for bk in bad_keywords):
                    continue
                try:
                    with sr.Microphone(device_index=i) as src:
                        recognizer_test.adjust_for_ambient_noise(src, duration=0.6)
                    mic_index = i
                    print("Auto-selected mic:", name)
                    break
                except Exception:
                    continue
            if mic_index is None and available:
                mic_index = 0
                print("Falling back to mic:", available[0])

        if mic_index is None:
            print("No microphone found")
            self.update_response("No microphone found")
            return

        mic = sr.Microphone(device_index=mic_index)
        self.current_mic_index = mic_index

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
            print("Started background listener on index", mic_index)
        except Exception as e:
            print("listen_in_background failed:", e)
            # fallback to blocking in thread
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
            except Exception as e:
                print("Mic capture error:", e)
                time.sleep(0.2)
                continue
            try:
                text = r.recognize_google(audio)
                if text and text.strip():
                    threading.Thread(target=handle_command, args=(text, self), daemon=True).start()
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                print("SR request error:", e)
                time.sleep(0.5)
                continue
            except Exception as e:
                print("Fallback recognition error:", e)
                time.sleep(0.5)
                continue

    def reselect_mic_dialog(self):
        # show mic list and let user pick
        dlg = QDialog(self)
        dlg.setWindowTitle("Select Microphone")
        layout = QVBoxLayout()
        combo = QComboBox()
        mics = sr.Microphone.list_microphone_names()
        combo.addItem("Auto-detect")
        for m in mics:
            combo.addItem(m)
        layout.addWidget(combo)
        btns = QHBoxLayout()
        ok = QPushButton("OK")
        cancel = QPushButton("Cancel")
        btns.addWidget(ok); btns.addWidget(cancel)
        layout.addLayout(btns)
        dlg.setLayout(layout)
        def do_ok():
            idx = combo.currentIndex()
            if idx == 0:
                self.forced_mic_index = None
            else:
                self.forced_mic_index = idx - 1
            # restart listener
            self._restart_listener()
            dlg.accept()
        ok.clicked.connect(do_ok)
        cancel.clicked.connect(dlg.reject)
        dlg.exec()

    def _restart_listener(self):
        global BG_LISTENER_STOP
        try:
            if BG_LISTENER_STOP:
                BG_LISTENER_STOP(wait_for_stop=False)
        except Exception:
            pass
        time.sleep(0.12)
        self._start_background_listener(self.forced_mic_index)

    # ---------------- Docking/snapping & input events ----------------
    def _snap_to_edge_if_close(self):
        screen = QApplication.primaryScreen().availableGeometry()
        px, py = self.pos().x(), self.pos().y()
        w, h = self.width(), self.height()
        if abs(px - screen.x()) < DOCK_THRESHOLD:
            self.move(screen.x(), py)
        if abs((px + w) - (screen.x() + screen.width())) < DOCK_THRESHOLD:
            self.move(screen.x() + screen.width() - w, py)
        if abs(py - screen.y()) < DOCK_THRESHOLD:
            self.move(self.pos().x(), screen.y())
        if abs((py + h) - (screen.y() + screen.height())) < DOCK_THRESHOLD:
            self.move(self.pos().x(), screen.y() + screen.height() - h)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self._drag_pos = ev.globalPosition().toPoint() - self.frameGeometry().topLeft()
            ev.accept()

    def mouseMoveEvent(self, ev):
        if self._drag_pos is not None and ev.buttons() & Qt.LeftButton:
            self.move(ev.globalPosition().toPoint() - self._drag_pos)
            ev.accept()

    def mouseReleaseEvent(self, ev):
        self._snap_to_edge_if_close()
        self._drag_pos = None
        ev.accept()

    def resizeEvent(self, ev):
        self.title_label.setGeometry(0, 40, self.width(), 54)
        self.response_label.setGeometry(20, 140, self.width() - 40, 100)
        self.settings_btn.setGeometry(self.width() - 40, 8, 32, 20)
        self.mic_btn.setGeometry(self.width() - 84, 8, 36, 20)
        QWidget.resizeEvent(self, ev)

    def closeEvent(self, ev):
        global LISTENING, BG_LISTENER_STOP
        LISTENING = False
        if BG_LISTENER_STOP:
            try:
                BG_LISTENER_STOP(wait_for_stop=False)
            except Exception:
                pass
        time.sleep(0.12)
        ev.accept()

    # ---------------- Settings UI ----------------
    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            # user saved - apply settings (already done in dialog)
            self.update_response("Settings saved")
            # restart mic if forced changed
            self._restart_listener()

# ---------------- Main ----------------
def main():
    app = QApplication(sys.argv)
    hud = NeonHUD()
    hud.show()

    # pre-warm TTS quietly so first speak is snappy (optional)
    QTimer.singleShot(1000, lambda: speak("Ready"))

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
