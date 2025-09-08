# rose_v22_neonhud.py
# Polished neon HUD v22:
# - Smooth open/close/minimize animations
# - Optimized animated purple gradient background
# - Peach rose icon at top-left (near mac buttons)
# - Custom-drawn waveform below "ROSE" while TTS plays
# - Edge-TTS for voice (played via default player)
# - YouTube autoplay (pytube Search -> open first result)
# - Volume & basic system commands
# - Always-listening voice input (SpeechRecognition)
# Keep HUD visuals same as v20; only internal behavior upgraded.

import sys
import os
import math
import time
import asyncio
import threading
import webbrowser
import platform
import subprocess
from datetime import timedelta

from PySide6.QtCore import Qt, QTimer, QPoint, QRect, QEasingCurve, Property, QPropertyAnimation
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton
from PySide6.QtGui import QFont, QPainter, QLinearGradient, QColor, QBrush, QPixmap

import speech_recognition as sr
import edge_tts
from pytube import Search

# -------------------- Config / Globals --------------------
LISTENING = True
TTS_PLAYING = False
TTS_LOCK = threading.Lock()

# Volume tool note: use nircmd on Windows for volume commands.
# Place nircmd.exe in PATH or same folder.

# -------------------- Utility: play TTS and manage speaking flag --------------------
def _estimate_tts_duration_seconds(text: str) -> float:
    # Rough estimate: 170 words per minute ~ 2.83 words/sec
    words = len(text.split())
    if words == 0:
        return 0.8
    return max(0.8, words / 2.8)

def speak(text: str):
    """Generate TTS via edge-tts (async) then play with default player.
       Sets TTS_PLAYING True while playback is expected.
    """
    def _run():
        global TTS_PLAYING
        with TTS_LOCK:
            TTS_PLAYING = True
        try:
            async def gen_and_play():
                communicate = edge_tts.Communicate(text, "en-US-JennyNeural")
                await communicate.save("speech.mp3")
            asyncio.run(gen_and_play())
            # Play using default system player (non-blocking)
            if platform.system() == "Windows":
                # Use start to let the system pick default player (wmplayer/groove)
                subprocess.Popen(["start", "speech.mp3"], shell=True)
            elif platform.system() == "Darwin":
                subprocess.Popen(["afplay", "speech.mp3"])
            else:
                subprocess.Popen(["xdg-open", "speech.mp3"])
            # Estimate duration and clear speaking flag after that interval
            dur = _estimate_tts_duration_seconds(text) + 0.6
            time.sleep(dur)
        except Exception as e:
            print("TTS/playback error:", e)
        finally:
            with TTS_LOCK:
                TTS_PLAYING = False

    threading.Thread(target=_run, daemon=True).start()

# -------------------- YouTube helper (pytube) --------------------
def play_youtube_song(song: str):
    """Use pytube Search to get the first result and open it (autoplay)."""
    try:
        # If user said 'play X on youtube', song may contain 'on youtube' etc. clean above caller.
        query = song.strip()
        if not query:
            webbrowser.open("https://www.youtube.com")
            return
        search = Search(query)
        # sometimes Search.results might be empty or delayed; try with fallback to open search page
        if not search.results:
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            webbrowser.open(url)
            return
        first = search.results[0]
        url = first.watch_url
        webbrowser.open(url)
    except Exception as e:
        print("YouTube play error:", e)
        url = f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}"
        webbrowser.open(url)

# -------------------- System & Volume helpers --------------------
def adjust_volume(cmd: str):
    # Windows: require nircmd.exe
    try:
        if platform.system() == "Windows":
            if "up" in cmd:
                os.system("nircmd.exe changesysvolume 5000")
            elif "down" in cmd:
                os.system("nircmd.exe changesysvolume -5000")
            elif "mute" in cmd:
                os.system("nircmd.exe mutesysvolume 1")
            elif "unmute" in cmd:
                os.system("nircmd.exe mutesysvolume 0")
        elif platform.system() == "Darwin":
            # macOS fallback uses osascript (not precise)
            if "up" in cmd:
                os.system("osascript -e 'set volume output volume (output volume of (get volume settings) + 10)'")
            elif "down" in cmd:
                os.system("osascript -e 'set volume output volume (output volume of (get volume settings) - 10)'")
        else:
            # Linux placeholder (amixer)
            if "up" in cmd:
                os.system("amixer -D pulse sset Master 5%+")
            elif "down" in cmd:
                os.system("amixer -D pulse sset Master 5%-")
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

# -------------------- Voice command handler --------------------
def handle_command(cmd: str, hud_ref):
    """Process recognized text and execute actions. HUD unchanged visually."""
    cmd = cmd.lower().strip()
    if not cmd:
        return

    # Update HUD text
    hud_ref.update_response(f"You said: {cmd}")

    # Play music on YouTube: accept phrases like "play arz kiya h by anuv jain"
    if cmd.startswith("play "):
        # remove leading 'play '
        song = cmd[5:]
        # remove trailing 'on youtube' if present
        song = song.replace("on youtube", "").strip()
        hud_ref.update_response(f"Playing {song} on YouTube...")
        speak(f"Playing {song} on YouTube")
        play_youtube_song(song)
        return

    # Volume commands
    if "volume up" in cmd or "increase volume" in cmd or "volume higher" in cmd:
        adjust_volume("up")
        speak("Volume increased")
        hud_ref.update_response("Volume increased")
        return
    if "volume down" in cmd or "decrease volume" in cmd or "volume lower" in cmd:
        adjust_volume("down")
        speak("Volume decreased")
        hud_ref.update_response("Volume decreased")
        return
    if "mute" in cmd and "unmute" not in cmd:
        adjust_volume("mute")
        speak("Muted")
        hud_ref.update_response("Muted")
        return
    if "unmute" in cmd:
        adjust_volume("unmute")
        speak("Unmuted")
        hud_ref.update_response("Unmuted")
        return

    # System commands
    if "shutdown" in cmd:
        hud_ref.update_response("Shutting down...")
        speak("Shutting down the system")
        system_action("shutdown")
        return
    if "restart" in cmd:
        hud_ref.update_response("Restarting...")
        speak("Restarting the system")
        system_action("restart")
        return

    # Open simple apps
    if "notepad" in cmd:
        hud_ref.update_response("Opening Notepad...")
        speak("Opening Notepad")
        if platform.system() == "Windows":
            subprocess.Popen(["notepad.exe"])
        return
    if "calculator" in cmd:
        hud_ref.update_response("Opening Calculator...")
        speak("Opening Calculator")
        if platform.system() == "Windows":
            subprocess.Popen(["calc.exe"])
        return

    # Greetings / default
    if any(g in cmd for g in ("hello", "hi", "hey")):
        speak("Hello. I'm Rose, your healer.")
        hud_ref.update_response("Hello. I'm Rose, your healer.")
        return

    # fallback
    speak(f"I heard: {cmd}")
    hud_ref.update_response(f"I heard: {cmd}")

# -------------------- Optimized HUD with smooth animations --------------------
class NeonHUD(QWidget):
    def __init__(self):
        super().__init__()

        # Window flags and transparency
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(520, 300)
        self.setMinimumSize(360, 220)

        # Peach rose icon (drawn into QPixmap)
        self.icon_pix = self._build_peach_rose_icon(28)

        # UI elements
        self.title_label = QLabel("ROSE", self)
        self.title_label.setFont(QFont("Segoe UI", 28, QFont.Bold))
        self.title_label.setStyleSheet("color: white;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setGeometry(0, 36, self.width(), 50)

        self.response_label = QLabel("Hi, I'm Rose, your healer...", self)
        self.response_label.setFont(QFont("Segoe UI", 14))
        self.response_label.setStyleSheet("color: white;")
        self.response_label.setAlignment(Qt.AlignCenter)
        self.response_label.setWordWrap(True)
        self.response_label.setGeometry(20, 120, self.width() - 40, 80)

        # Mac-style buttons (top-left)
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

        # draggable
        self._drag_pos = None

        # animation state
        self._fade_anim = None
        self._geom_anim = None

        # gradient animation param (smooth)
        self._grad_phase = 0.0
        self._grad_timer = QTimer(self)
        self._grad_timer.timeout.connect(self._on_grad_tick)
        self._grad_timer.start(40)  # ~25 FPS for smooth but light

        # waveform animation param
        self._wave_phase = 0.0
        self._wave_timer = QTimer(self)
        self._wave_timer.timeout.connect(self._on_wave_tick)
        self._wave_timer.start(35)

        # Start listener thread (always listening)
        threading.Thread(target=self._start_listening, daemon=True).start()

        # show with a smooth fade-in
        self.setWindowOpacity(0.0)
        self._animate_show()

    # ---------- UI helpers ----------
    def _build_peach_rose_icon(self, size_px: int) -> QPixmap:
        """Draw a simple peach-colored rose icon into a QPixmap."""
        pix = QPixmap(size_px, size_px)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        center = size_px / 2
        petal_color = QColor(255, 179, 153)  # peach
        stroke = QColor(210, 120, 100)
        p.setBrush(petal_color)
        p.setPen(stroke)
        # draw 5 petals
        for i in range(5):
            angle = i * (360 / 5)
            rad = math.radians(angle)
            x = center + math.cos(rad) * (size_px * 0.12)
            y = center + math.sin(rad) * (size_px * 0.12)
            rect = QRect(int(x - size_px * 0.22), int(y - size_px * 0.22), int(size_px * 0.44), int(size_px * 0.44))
            p.drawEllipse(rect)
        # center circle
        p.setBrush(QColor(255, 140, 120))
        p.drawEllipse(int(center - size_px * 0.12), int(center - size_px * 0.12), int(size_px * 0.24), int(size_px * 0.24))
        p.end()
        return pix

    def update_response(self, text: str):
        self.response_label.setText(text)

    # ---------- animations ----------
    def _animate_show(self):
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(420)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._fade_anim.start()

    def _animate_close(self):
        # fade out then close
        if self._fade_anim and self._fade_anim.state() == QPropertyAnimation.Running:
            self._fade_anim.stop()
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(350)
        anim.setStartValue(self.windowOpacity())
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        anim.finished.connect(self.close)
        anim.start()
        self._fade_anim = anim

    def _animate_minimize(self):
        # smooth fade then minimize (and restore opacity on restore)
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(300)
        anim.setStartValue(self.windowOpacity())
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InOutCubic)

        def do_minimize():
            self.showMinimized()
            # wait a bit and restore small opacity so when restored it fades in
            self.setWindowOpacity(0.0)

        anim.finished.connect(do_minimize)
        anim.start()
        self._fade_anim = anim

    def toggle_max_restore(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    # ---------- gradient tick (optimized) ----------
    def _on_grad_tick(self):
        # advance phase slowly
        self._grad_phase += 0.008
        if self._grad_phase > math.tau:
            self._grad_phase -= math.tau
        # lightweight update (no heavy recalculation)
        self.update()  # triggers paintEvent

    # ---------- waveform tick ----------
    def _on_wave_tick(self):
        self._wave_phase += 0.14
        if self._wave_phase > math.tau:
            self._wave_phase -= math.tau
        # only update waveform area to be slightly more efficient
        waveform_rect = QRect(20, self.height() - 70, self.width() - 40, 48)
        self.update(waveform_rect)

    # ---------- paint ----------
    def paintEvent(self, ev):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # animated purple gradient (use sin to smoothly vary color)
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

        # draw peach rose icon near top-left (to the right of buttons)
        icon_x = 90
        icon_y = 6
        painter.drawPixmap(icon_x, icon_y, self.icon_pix)

        # subtle inner glow (simulate glow by translucent rounded rect)
        painter.setBrush(QColor(255, 255, 255, 10))
        painter.drawRoundedRect(10, 10, w - 20, h - 20, 18, 18)

        # custom waveform if TTS playing
        is_speaking = False
        with TTS_LOCK:
            is_speaking = TTS_PLAYING

        if is_speaking:
            self._draw_waveform(painter)

        # draw title text with soft glow (draw multiple passes)
        title_rect = self.title_label.geometry()
        for i in range(4, 0, -1):
            alpha = int(30 / i)
            glow_color = QColor(255, 255, 255, alpha)
            painter.setPen(glow_color)
            f = QFont("Segoe UI", 28 + i, QFont.Bold)
            painter.setFont(f)
            painter.drawText(title_rect, Qt.AlignCenter, self.title_label.text())
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI", 28, QFont.Bold))
        painter.drawText(title_rect, Qt.AlignCenter, self.title_label.text())

    def _draw_waveform(self, painter: QPainter):
        # draw an animated set of vertical bars centered beneath the title
        bar_count = max(8, int(self.width() / 28))
        rect_w = self.width() - 40
        rect_h = 48
        x0 = 20
        y0 = self.height() - 80
        spacing = rect_w / bar_count
        base_color = QColor(255, 255, 255, 200)

        for i in range(bar_count):
            phase = self._wave_phase + (i * 0.35)
            # produce smooth height between 0.15..1.0
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

    # ---------- Listening thread ----------
    def _start_listening(self):
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        # set some aggressiveness to ambient adaptation
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.4
        recognizer.operation_timeout = None
        while LISTENING:
            try:
                with mic as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = recognizer.listen(source, phrase_time_limit=5)
                # try recognition
                try:
                    text = recognizer.recognize_google(audio)
                    if text and text.strip():
                        handle_command(text, self)
                except sr.UnknownValueError:
                    # didn't catch speech, ignore
                    continue
                except sr.RequestError as e:
                    print("Speech recognition error:", e)
                    continue
            except Exception as e:
                # general audio capture error: keep loop alive
                print("Microphone/listen error:", e)
                time.sleep(0.5)
                continue

    # ---------- mouse drag ----------
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

    # ---------- cleanup ----------
    def closeEvent(self, ev):
        global LISTENING
        LISTENING = False
        # small delay to let TTS threads finish
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
