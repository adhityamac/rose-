# rose_v26_5_spotify.py
# v26.5 — v26 HUD + instant talkback + Spotify local control + aesthetics upgrades
# Requirements: PySide6, speechrecognition, edge-tts, pytube, requests

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

from PySide6.QtCore import Qt, QTimer, QRect, QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton
from PySide6.QtGui import QFont, QPainter, QLinearGradient, QColor, QBrush, QPixmap

import speech_recognition as sr
import edge_tts
from pytube import Search
import requests  # For Gemini API integration

# ------------------------ Globals ------------------------
LISTENING = True
TTS_PLAYING = False
TTS_LOCK = threading.Lock()
BG_LISTENER_STOP = None
CONVERSATION_HISTORY = []  # For maintaining conversational context with Gemini

# Your Gemini API key (get from https://aistudio.google.com/app/apikey)
GEMINI_API_KEY = "AIzaSyB3hpqh17aPpqeaQSe5eW8yxpcw1rlkydk"  # Replace with your actual key

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

async def _gen_tts_save(text: str, filename: str = "speech.mp3"):
    comm = edge_tts.Communicate(text, "en-US-JennyNeural")
    await comm.save(filename)

def speak(text: str):
    """Generate TTS (edge-tts) and play it; sets TTS_PLAYING while playback is expected."""
    def runner():
        global TTS_PLAYING
        with TTS_LOCK:
            TTS_PLAYING = True
        try:
            asyncio.run(_gen_tts_save(text, "speech.mp3"))
            _play_audio_file("speech.mp3")
            time.sleep(_estimate_tts_duration_seconds(text) + 0.35)
        except Exception as e:
            print("TTS error:", e)
        finally:
            with TTS_LOCK:
                TTS_PLAYING = False
    threading.Thread(target=runner, daemon=True).start()

# ------------------------ YouTube helper ------------------------
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

# ------------------------ Spotify local control ------------------------
# We use media key simulation for Windows; on mac use AppleScript to control Spotify app.
def _send_media_key_windows(vk_code: int):
    """Send a media key using SendInput on Windows (works without extra libs)."""
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL('user32', use_last_error=True)
        # INPUT structure constants
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

        # key down
        ki = KEYBDINPUT(wVk=vk_code, wScan=0, dwFlags=KEYEVENTF_EXTENDEDKEY, time=0, dwExtraInfo=0)
        x = INPUT(type=INPUT_KEYBOARD, ki=ki)
        user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

        # key up
        ki_up = KEYBDINPUT(wVk=vk_code, wScan=0, dwFlags=KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, time=0, dwExtraInfo=0)
        x_up = INPUT(type=INPUT_KEYBOARD, ki=ki_up)
        user32.SendInput(1, ctypes.byref(x_up), ctypes.sizeof(x_up))
    except Exception as e:
        print("Windows media key send failed:", e)

def spotify_play_pause():
    try:
        if platform.system() == "Windows":
            VK_MEDIA_PLAY_PAUSE = 0xB3
            _send_media_key_windows(VK_MEDIA_PLAY_PAUSE)
        elif platform.system() == "Darwin":
            apple = 'tell application "Spotify" to playpause'
            subprocess.Popen(["osascript", "-e", apple])
        else:
            # Linux fallback: try playerctl
            os.system("playerctl play-pause")
    except Exception as e:
        print("Spotify play/pause error:", e)

def spotify_next():
    try:
        if platform.system() == "Windows":
            VK_MEDIA_NEXT_TRACK = 0xB0
            _send_media_key_windows(VK_MEDIA_NEXT_TRACK)
        elif platform.system() == "Darwin":
            apple = 'tell application "Spotify" to next track'
            subprocess.Popen(["osascript", "-e", apple])
        else:
            os.system("playerctl next")
    except Exception as e:
        print("Spotify next error:", e)

def spotify_prev():
    try:
        if platform.system() == "Windows":
            VK_MEDIA_PREV_TRACK = 0xB1
            _send_media_key_windows(VK_MEDIA_PREV_TRACK)
        elif platform.system() == "Darwin":
            apple = 'tell application "Spotify" to previous track'
            subprocess.Popen(["osascript", "-e", apple])
        else:
            os.system("playerctl previous")
    except Exception as e:
        print("Spotify previous error:", e)

# ------------------------ Volume & system helpers ------------------------
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

# ------------------------ Command handling ------------------------
def handle_command(cmd: str, hud_ref: Optional[QWidget] = None):
    if not cmd:
        return
    cmd_norm = cmd.lower().strip()
    if hud_ref:
        hud_ref.update_response(f"You said: {cmd_norm}")

    # Spotify voice-only commands
    if "spotify" in cmd_norm:
        if any(k in cmd_norm for k in ("play", "pause", "play pause", "play/pause")):
            spotify_play_pause(); speak("Toggling Spotify play pause"); return
        if "next" in cmd_norm or "skip" in cmd_norm:
            spotify_next(); speak("Skipping to next track"); return
        if "previous" in cmd_norm or "prev" in cmd_norm or "back" in cmd_norm:
            spotify_prev(); speak("Going to previous track"); return

    # Play on YouTube: "play arz kiya h" or "play X on youtube"
    if cmd_norm.startswith("play "):
        # if user says "play X on youtube" or "play X"
        # prioritize youtube unless they said 'spotify'
        if "on youtube" in cmd_norm or "youtube" in cmd_norm:
            song = cmd_norm.replace("play", "").replace("on youtube", "").replace("youtube", "").strip()
            if hud_ref: hud_ref.update_response(f"Playing {song} on YouTube...")
            speak(f"Playing {song} on YouTube")
            play_youtube_song(song)
            return
        else:
            # If no mention of spotify, treat as youtube by default
            song = cmd_norm[5:].strip()
            if song:
                if hud_ref: hud_ref.update_response(f"Playing {song} on YouTube...")
                speak(f"Playing {song} on YouTube")
                play_youtube_song(song)
                return

    # Volume
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

    # System
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

    # Open apps
    if "open chrome" in cmd_norm or "open brave" in cmd_norm or "open browser" in cmd_norm:
        speak("Opening browser")
        if platform.system() == "Windows":
            # try Brave, then Chrome
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
        # fallback: open file explorer
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
            CONVERSATION_HISTORY.pop()  # Remove failed user message
            return
        ai_candidate = json_response["candidates"][0]
        if "content" not in ai_candidate:
            finish_reason = ai_candidate.get("finishReason", "Unknown")
            speak(f"Sorry, the response was blocked due to {finish_reason}.")
            if hud_ref:
                hud_ref.update_response(f"Blocked: {finish_reason}")
            CONVERSATION_HISTORY.pop()  # Remove failed user message
            return
        ai_reply = ai_candidate["content"]["parts"][0]["text"].strip()
        CONVERSATION_HISTORY.append({"role": "model", "parts": [{"text": ai_reply}]})
        speak(ai_reply)
        if hud_ref:
            hud_ref.update_response(ai_reply)
    except Exception as e:
        print("Gemini API error:", e)
        speak(f"I heard: {cmd_norm}. Sorry, I couldn't process that with AI.")
        if hud_ref: hud_ref.update_response(f"I heard: {cmd_norm}")
        # Remove the failed user message from history if error
        CONVERSATION_HISTORY.pop()

# ------------------------ HUD ------------------------
class NeonHUD(QWidget):
    def __init__(self):
        super().__init__()
        # flags & look
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(540, 320)
        self.setMinimumSize(360, 220)

        # icon (moved right of mac buttons)
        self.icon_pix = self._build_peach_rose_icon(28)
        self._icon_x = 90
        self._icon_y = 6

        # Title
        self.title_label = QLabel("ROSE", self)
        self.title_label.setFont(QFont("Segoe UI", 30, QFont.Bold))
        self.title_label.setStyleSheet("color: white;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setGeometry(0, 40, self.width(), 54)

        # Response text
        self.response_label = QLabel("", self)
        self.response_label.setFont(QFont("Segoe UI", 14))
        self.response_label.setStyleSheet("color: white;")
        self.response_label.setAlignment(Qt.AlignCenter)
        self.response_label.setWordWrap(True)
        self.response_label.setGeometry(20, 140, self.width() - 40, 100)

        # mac-like buttons (top-left)
        self.close_btn = QPushButton(self)
        self.close_btn.setStyleSheet("background-color: #FF5C5C; border-radius:7px;")
        self.close_btn.setGeometry(10, 10, 16, 16)
        self.close_btn.clicked.connect(self._animate_close)

        self.min_btn = QPushButton(self)
        self.min_btn.setStyleSheet("background-color: #FFBD44; border-radius:7px;")
        self.min_btn.setGeometry(34, 10, 16, 16)
        self.min_btn.clicked.connect(self._animate_minimize)

        self.max_btn = QPushButton(self)
        self.max_btn.setStyleSheet("background-color: #28C840; border-radius:7px;")
        self.max_btn.setGeometry(58, 10, 16, 16)
        self.max_btn.clicked.connect(self.toggle_max_restore)

        # animation state
        self._grad_phase = 0.0
        self._wave_phase = 0.0
        self._fade_anim = None

        # timers
        self._grad_timer = QTimer(self)
        self._grad_timer.timeout.connect(self._on_grad_tick)
        self._grad_timer.start(36)  # ~28fps

        self._wave_timer = QTimer(self)
        self._wave_timer.timeout.connect(self._on_wave_tick)
        self._wave_timer.start(32)

        # dragging
        self._drag_pos = None

        # start background listener (robust)
        self._start_background_listener()

        # greeting
        QTimer.singleShot(900, self._greet)

        # show fade-in
        self.setWindowOpacity(0.0)
        self._animate_show()

    # ----- build icon -----
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
            rect = QRect(int(x - size_px * 0.22), int(y - size_px * 0.22), int(size_px * 0.44), int(size_px * 0.44))
            p.drawEllipse(rect)
        p.setBrush(QColor(255, 140, 120))
        p.drawEllipse(int(center - size_px * 0.12), int(center - size_px * 0.12), int(size_px * 0.24), int(size_px * 0.24))
        p.end()
        return pix

    # ----- greeting -----
    def _greet(self):
        global CONVERSATION_HISTORY
        greeting = "Hi, I'm Rose, your healer. How can I assist you?"
        self.update_response(greeting)
        speak(greeting)
        CONVERSATION_HISTORY.append({"role": "model", "parts": [{"text": greeting}]})

    # ----- response helper -----
    def update_response(self, text: str):
        self.response_label.setText(text)

    # ----- animations -----
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

    # ----- gradient & waveform ticks -----
    def _on_grad_tick(self):
        self._grad_phase += 0.007
        if self._grad_phase > math.tau:
            self._grad_phase -= math.tau
        self.update()

    def _on_wave_tick(self):
        self._wave_phase += 0.14
        if self._wave_phase > math.tau:
            self._wave_phase -= math.tau
        # update waveform area region only for efficiency
        self.update(QRect(20, self.height() - 80, self.width() - 40, 68))

    # ----- paint -----
    def paintEvent(self, ev):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        phase = self._grad_phase
        c1_h = (270 + (math.sin(phase) * 18)) % 360
        c2_h = (300 + (math.cos(phase * 1.2) * 16)) % 360
        c1 = QColor.fromHsv(int(c1_h), 200, 170)
        c2 = QColor.fromHsv(int(c2_h), 200, 180)

        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0.0, c1)
        grad.setColorAt(1.0, c2)
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, 20, 20)

        # inner subtle glow
        painter.setBrush(QColor(255, 255, 255, 10))
        painter.drawRoundedRect(10, 10, w - 20, h - 20, 18, 18)

        # draw mac buttons area
        # (buttons are actual widgets; icon is drawn to avoid overlap)
        painter.drawPixmap(self._icon_x, self._icon_y, self.icon_pix)

        # speaking state influences glow color and icon scale
        with TTS_LOCK:
            speaking = TTS_PLAYING

        # title glow and color changes
        if speaking:
            # peach/pink when speaking
            base_col = QColor(255, 180, 170)
        else:
            # neon purple when idle
            base_col = QColor(190, 0, 255)

        title_rect = self.title_label.geometry()
        for i in range(5, 0, -1):
            alpha = max(6, 36 // i)
            col = QColor(base_col.red(), base_col.green(), base_col.blue(), alpha)
            painter.setPen(col)
            painter.setFont(QFont("Segoe UI", 30 + i, QFont.Bold))
            painter.drawText(title_rect, Qt.AlignCenter, self.title_label.text())

        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI", 30, QFont.Bold))
        painter.drawText(title_rect, Qt.AlignCenter, self.title_label.text())

        # waveform
        if speaking:
            self._draw_waveform(painter)
        else:
            # draw subtle idle microbars
            self._draw_idle_wave(painter)

    def _draw_waveform(self, painter: QPainter):
        bar_count = max(10, int(self.width() / 30))
        rect_w = self.width() - 60
        rect_h = 60
        x0 = 30
        y0 = self.height() - 90
        spacing = rect_w / bar_count
        for i in range(bar_count):
            phase = self._wave_phase + (i * 0.28)
            h_ratio = 0.25 + 0.75 * (0.5 + 0.5 * math.sin(phase))
            bar_h = rect_h * h_ratio
            bx = int(x0 + i * spacing + spacing * 0.12)
            bw = int(spacing * 0.76)
            by = int(y0 + (rect_h - bar_h) / 2)
            alpha = int(140 + 80 * h_ratio)
            col = QColor(255, 220, 210, alpha)
            painter.setBrush(col)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(bx, by, bw, int(bar_h), 6, 6)

    def _draw_idle_wave(self, painter: QPainter):
        # subtle floating bars
        bar_count = max(8, int(self.width() / 40))
        rect_w = self.width() - 60
        rect_h = 30
        x0 = 30
        y0 = self.height() - 70
        spacing = rect_w / bar_count
        for i in range(bar_count):
            phase = (self._grad_phase * 0.6) + (i * 0.18)
            h_ratio = 0.45 + 0.15 * math.sin(phase)
            bar_h = rect_h * h_ratio
            bx = int(x0 + i * spacing + spacing * 0.2)
            bw = int(spacing * 0.6)
            by = int(y0 + (rect_h - bar_h) / 2)
            alpha = int(70 + 40 * h_ratio)
            col = QColor(255, 255, 255, alpha)
            painter.setBrush(col)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(bx, by, bw, int(bar_h), 5, 5)

    # ----- mic selection + background listener (instant) -----
    def _start_background_listener(self):
        recognizer_test = sr.Recognizer()
        mics = sr.Microphone.list_microphone_names()
        mic_index = None

        # prefer physical mics, avoid Virtual/Mapper names
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

        # fallback to first device if nothing else
        if mic_index is None and mics:
            mic_index = 0
            print("Falling back to mic:", mics[0])

        if mic_index is None:
            print("No microphone devices available.")
            self.update_response("No microphone available")
            return

        mic = sr.Microphone(device_index=mic_index)

        # callback: very light, offload heavy work to thread
        def callback(recognizer_obj, audio):
            # don't react to own TTS
            with TTS_LOCK:
                if TTS_PLAYING:
                    return
            try:
                text = recognizer_obj.recognize_google(audio)
                if text and text.strip():
                    # immediate reaction: run in separate thread
                    threading.Thread(target=handle_command, args=(text, self), daemon=True).start()
            except sr.UnknownValueError:
                return
            except sr.RequestError as e:
                print("Speech recognition request error:", e)
                return
            except Exception as e:
                # one-off message
                print("Recognition callback error:", e)
                return

        # start background listener and store stop handle
        global BG_LISTENER_STOP
        try:
            # note: listen_in_background creates its own Recognizer internally
            rec = sr.Recognizer()
            BG_LISTENER_STOP = rec.listen_in_background(mic, callback, phrase_time_limit=4)
        except Exception as e:
            print("Background listener failed, falling back to blocking loop:", e)
            # fallback to blocking loop in a thread
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

    # ----- dragging -----
    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self._drag_pos = ev.globalPosition().toPoint() - self.frameGeometry().topLeft()
            ev.accept()

    def mouseMoveEvent(self, ev):
        if self._drag_pos is not None and ev.buttons() & Qt.LeftButton:
            self.move(ev.globalPosition().toPoint() - self._drag_pos)
            ev.accept()

    def mouseReleaseEvent(self, ev):
        self._drag_pos = None
        ev.accept()

    def closeEvent(self, ev):
        global LISTENING, BG_LISTENER_STOP
        LISTENING = False
        if BG_LISTENER_STOP:
            try:
                BG_LISTENER_STOP(wait_for_stop=False)
            except Exception:
                pass
        time.sleep(0.2)
        ev.accept()

# ------------------------ Run ------------------------
def main():
    app = QApplication(sys.argv)
    hud = NeonHUD()
    hud.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()