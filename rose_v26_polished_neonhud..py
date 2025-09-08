# rose_v26_instant.py
# v26 HUD (instant talk-back) — keeps v26 visuals, mic fixed, listen_in_background for immediate replies

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

# -------------------- Globals --------------------
LISTENING = True
TTS_PLAYING = False
TTS_LOCK = threading.Lock()
BG_LISTENER_STOP = None  # function returned by listen_in_background, to stop when closing

# -------------------- TTS helpers --------------------
def _estimate_tts_duration_seconds(text: str) -> float:
    words = len(text.split())
    return max(0.6, words / 2.8)

def _play_audio_file(path: str):
    """Open audio with default system player in non-blocking way."""
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
    """Generate TTS (edge-tts) and play it; set TTS_PLAYING while playing."""
    def _run():
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
    threading.Thread(target=_run, daemon=True).start()

# -------------------- YouTube helper --------------------
def play_youtube_song(song: str):
    """Use pytube Search to open the first found video (autoplay in browser)."""
    try:
        query = song.strip()
        if not query:
            webbrowser.open("https://www.youtube.com")
            return
        s = Search(query)
        # sometimes Search.results is lazy; fallback to search page if empty
        if not getattr(s, "results", None):
            webbrowser.open(f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}")
            return
        first = s.results[0]
        url = getattr(first, "watch_url", None) or f"https://www.youtube.com/watch?v={first.video_id}"
        webbrowser.open(url)
    except Exception as e:
        print("YouTube error:", e)
        webbrowser.open(f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}")

# -------------------- Volume & system helpers --------------------
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
            if platform.system() == "Windows":
                os.system("shutdown /s /t 1")
            else:
                os.system("shutdown now")
        elif "restart" in cmd:
            if platform.system() == "Windows":
                os.system("shutdown /r /t 1")
            else:
                os.system("reboot")
    except Exception as e:
        print("System action error:", e)

# -------------------- Command handling --------------------
def handle_command(cmd: str, hud_ref: Optional[QWidget] = None):
    """Process the recognized text and act — HUD unchanged visually."""
    if not cmd:
        return
    cmd_norm = cmd.lower().strip()
    if hud_ref:
        hud_ref.update_response(f"You said: {cmd_norm}")

    # Play music
    if cmd_norm.startswith("play "):
        song = cmd_norm[5:].replace("on youtube", "").strip()
        if hud_ref: hud_ref.update_response(f"Playing {song} on YouTube...")
        speak(f"Playing {song} on YouTube")
        play_youtube_song(song)
        return

    # Volume
    if any(x in cmd_norm for x in ("volume up", "increase volume", "volume higher")):
        adjust_volume("up")
        speak("Volume increased")
        if hud_ref: hud_ref.update_response("Volume increased")
        return
    if any(x in cmd_norm for x in ("volume down", "decrease volume", "volume lower")):
        adjust_volume("down")
        speak("Volume decreased")
        if hud_ref: hud_ref.update_response("Volume decreased")
        return
    if "mute" in cmd_norm and "unmute" not in cmd_norm:
        adjust_volume("mute"); speak("Muted"); 
        if hud_ref: hud_ref.update_response("Muted")
        return
    if "unmute" in cmd_norm:
        adjust_volume("unmute"); speak("Unmuted"); 
        if hud_ref: hud_ref.update_response("Unmuted")
        return

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

    # Apps
    if "notepad" in cmd_norm:
        speak("Opening Notepad")
        if hud_ref: hud_ref.update_response("Opening Notepad...")
        if platform.system() == "Windows":
            subprocess.Popen(["notepad.exe"])
        return
    if "calculator" in cmd_norm:
        speak("Opening Calculator")
        if hud_ref: hud_ref.update_response("Opening Calculator...")
        if platform.system() == "Windows":
            subprocess.Popen(["calc.exe"])
        return

    # Greetings
    if any(g in cmd_norm for g in ("hello", "hi", "hey")):
        speak("Hello. I'm Rose, your healer.")
        if hud_ref: hud_ref.update_response("Hello. I'm Rose, your healer.")
        return

    # Fallback
    speak(f"I heard: {cmd}")
    if hud_ref: hud_ref.update_response(f"I heard: {cmd_norm}")

# -------------------- HUD (visuals untouched, peach rose moved) --------------------
class NeonHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(520, 300)
        self.setMinimumSize(360, 220)

        # icon (moved right of mac buttons)
        self.icon_pix = self._build_peach_rose_icon(28)

        # Title label
        self.title_label = QLabel("ROSE", self)
        self.title_label.setFont(QFont("Segoe UI", 28, QFont.Bold))
        self.title_label.setStyleSheet("color: white;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setGeometry(0, 36, self.width(), 50)

        # Response area
        self.response_label = QLabel("Hi, I'm Rose, your healer...", self)
        self.response_label.setFont(QFont("Segoe UI", 14))
        self.response_label.setStyleSheet("color: white;")
        self.response_label.setAlignment(Qt.AlignCenter)
        self.response_label.setWordWrap(True)
        self.response_label.setGeometry(20, 120, self.width() - 40, 80)

        # mac-style buttons (top-left)
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

        # place peach rose icon to the right of buttons so it doesn't overlap
        self._icon_x = 90
        self._icon_y = 6

        # internal animation state
        self._grad_phase = 0.0
        self._wave_phase = 0.0
        self._fade_anim = None

        # timers
        self._grad_timer = QTimer(self)
        self._grad_timer.timeout.connect(self._on_grad_tick)
        self._grad_timer.start(40)

        self._wave_timer = QTimer(self)
        self._wave_timer.timeout.connect(self._on_wave_tick)
        self._wave_timer.start(35)

        # dragging
        self._drag_pos = None

        # start background listener using robust selection + listen_in_background
        self._start_background_listener()

        # show with fade-in
        self.setWindowOpacity(0.0)
        self._animate_show()

    def _build_peach_rose_icon(self, size_px: int) -> QPixmap:
        pix = QPixmap(size_px, size_px)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        center = size_px / 2
        petal_color = QColor(255, 179, 153)  # peach
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

    def update_response(self, text: str):
        self.response_label.setText(text)

    # Animations (fade)
    def _animate_show(self):
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(420)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._fade_anim.start()

    def _animate_close(self):
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(350)
        anim.setStartValue(self.windowOpacity())
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InOutCubic)

        def do_close():
            global BG_LISTENER_STOP
            if BG_LISTENER_STOP:
                BG_LISTENER_STOP(wait_for_stop=False)
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

    # Gradient/wave ticks
    def _on_grad_tick(self):
        self._grad_phase += 0.008
        if self._grad_phase > math.tau:
            self._grad_phase -= math.tau
        self.update()

    def _on_wave_tick(self):
        self._wave_phase += 0.14
        if self._wave_phase > math.tau:
            self._wave_phase -= math.tau
        # update waveform area only
        self.update(QRect(20, self.height() - 70, self.width() - 40, 48))

    def paintEvent(self, ev):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        phase = self._grad_phase
        c1_h = (270 + (math.sin(phase) * 20)) % 360
        c2_h = (300 + (math.cos(phase * 1.3) * 18)) % 360
        c1 = QColor.fromHsv(int(c1_h), 200, 160)
        c2 = QColor.fromHsv(int(c2_h), 200, 180)

        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0.0, c1)
        grad.setColorAt(1.0, c2)
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, 20, 20)

        # peach rose icon to the right of buttons
        painter.drawPixmap(self._icon_x, self._icon_y, self.icon_pix)

        # inner subtle glow
        painter.setBrush(QColor(255, 255, 255, 10))
        painter.drawRoundedRect(10, 10, w - 20, h - 20, 18, 18)

        # waveform when speaking
        with TTS_LOCK:
            speaking = TTS_PLAYING
        if speaking:
            self._draw_waveform(painter)

        # title text with glow passes
        title_rect = self.title_label.geometry()
        for i in range(4, 0, -1):
            alpha = int(30 / i)
            painter.setPen(QColor(255, 255, 255, alpha))
            painter.setFont(QFont("Segoe UI", 28 + i, QFont.Bold))
            painter.drawText(title_rect, Qt.AlignCenter, self.title_label.text())
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI", 28, QFont.Bold))
        painter.drawText(title_rect, Qt.AlignCenter, self.title_label.text())

    def _draw_waveform(self, painter: QPainter):
        bar_count = max(8, int(self.width() / 28))
        rect_w = self.width() - 40
        rect_h = 48
        x0 = 20
        y0 = self.height() - 80
        spacing = rect_w / bar_count
        base_color = QColor(255, 255, 255, 200)

        for i in range(bar_count):
            phase = self._wave_phase + (i * 0.35)
            h_ratio = 0.2 + 0.8 * (0.5 + 0.5 * math.sin(phase))
            bar_h = rect_h * h_ratio
            bx = int(x0 + i * spacing + spacing * 0.15)
            bw = int(spacing * 0.7)
            by = int(y0 + (rect_h - bar_h) / 2)
            alpha = int(120 + 80 * h_ratio)
            col = QColor(base_color.red(), base_color.green(), base_color.blue(), alpha)
            painter.setBrush(col)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(bx, by, bw, int(bar_h), 6, 6)

    # -------------------- Mic: robust selection + listen_in_background for instant replies --------------------
    def _start_background_listener(self):
        recognizer = sr.Recognizer()
        mic_index = None
        mics = sr.Microphone.list_microphone_names()

        # pick first real mic (avoid "Sound Mapper" and virtual devices)
        for i, name in enumerate(mics):
            if "Sound Mapper" in name or "Stereo Mix" in name or "Primary Sound Driver" in name:
                continue
            try:
                # quick test to open the mic
                with sr.Microphone(device_index=i) as s:
                    recognizer.adjust_for_ambient_noise(s, duration=0.8)
                mic_index = i
                print("Using mic:", name)
                break
            except Exception:
                continue

        # fallback to first mic if none preferred found
        if mic_index is None and mics:
            mic_index = 0
            print("Falling back to mic:", mics[0])

        if mic_index is None:
            print("No microphone devices available.")
            return

        mic = sr.Microphone(device_index=mic_index)

        # callback runs in background thread per chunk (instant-ish)
        def callback(recognizer_obj, audio):
            # ignore while TTS is playing to avoid capturing own voice
            with TTS_LOCK:
                if TTS_PLAYING:
                    return
            try:
                text = recognizer_obj.recognize_google(audio)
                if text and text.strip():
                    # handle in a separate thread to keep callback fast
                    threading.Thread(target=handle_command, args=(text, self), daemon=True).start()
            except sr.UnknownValueError:
                return
            except sr.RequestError as e:
                print("Speech recognition request error:", e)
                return
            except Exception as e:
                # general error — don't spam console
                print("Recognition callback error:", e)
                return

        # start background listener; store stop function
        global BG_LISTENER_STOP
        try:
            BG_LISTENER_STOP = sr.Recognizer().listen_in_background(mic, callback, phrase_time_limit=4)
            # note: listen_in_background uses its own Recognizer instance; we used recognizer only for testing
        except Exception as e:
            print("Failed to start background listener:", e)
            # fallback to blocking threaded loop as last resort
            threading.Thread(target=self._fallback_listen_loop, args=(mic,), daemon=True).start()

    def _fallback_listen_loop(self, mic):
        """If listen_in_background fails, use a robust blocking loop (keeps behavior safe)."""
        r = sr.Recognizer()
        r.dynamic_energy_threshold = True
        r.pause_threshold = 0.35
        while LISTENING:
            with mic as source:
                try:
                    r.adjust_for_ambient_noise(source, duration=0.6)
                    audio = r.listen(source, phrase_time_limit=5)
                except Exception:
                    time.sleep(0.2)
                    continue
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
                print("Fallback recognition error:", e)
                time.sleep(0.5)
                continue

    # -------------------- Dragging --------------------
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

# -------------------- Run --------------------
def main():
    app = QApplication(sys.argv)
    hud = NeonHUD()
    hud.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
