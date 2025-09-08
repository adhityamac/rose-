# rose_v25_neonhud.py
# Polished Neon HUD v25:
# - Smooth animations (open/close/minimize)
# - Optimized gradient background
# - Peach rose icon at top-left
# - Custom waveform below title during TTS
# - Edge-TTS + default system player
# - YouTube autoplay via pytube Search
# - Volume & basic system commands
# - Always-listening voice input (SpeechRecognition)
# - Fixed microphone & global TTS syntax issues

import sys
import os
import math
import time
import asyncio
import threading
import webbrowser
import platform
import subprocess

from PySide6.QtCore import Qt, QTimer, QPoint, QRect, QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton
from PySide6.QtGui import QFont, QPainter, QLinearGradient, QColor, QBrush, QPixmap

import speech_recognition as sr
import edge_tts
from pytube import Search

# -------------------- Globals --------------------
LISTENING = True
TTS_PLAYING = False
TTS_LOCK = threading.Lock()

# -------------------- TTS --------------------
def _estimate_tts_duration_seconds(text: str) -> float:
    words = len(text.split())
    if words == 0:
        return 0.8
    return max(0.8, words / 2.8)

def speak(text: str):
    """Edge-TTS async + default player playback"""
    def _run():
        global TTS_PLAYING
        with TTS_LOCK:
            TTS_PLAYING = True
        try:
            async def gen_and_play():
                communicate = edge_tts.Communicate(text, "en-US-JennyNeural")
                await communicate.save("speech.mp3")
            asyncio.run(gen_and_play())

            if platform.system() == "Windows":
                subprocess.Popen(["start", "speech.mp3"], shell=True)
            elif platform.system() == "Darwin":
                subprocess.Popen(["afplay", "speech.mp3"])
            else:
                subprocess.Popen(["xdg-open", "speech.mp3"])

            dur = _estimate_tts_duration_seconds(text) + 0.6
            time.sleep(dur)
        except Exception as e:
            print("TTS/playback error:", e)
        finally:
            with TTS_LOCK:
                TTS_PLAYING = False

    threading.Thread(target=_run, daemon=True).start()

# -------------------- YouTube --------------------
def play_youtube_song(song: str):
    try:
        query = song.strip()
        if not query:
            webbrowser.open("https://www.youtube.com")
            return
        search = Search(query)
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

# -------------------- Volume / System --------------------
def adjust_volume(cmd: str):
    try:
        if platform.system() == "Windows":
            if "up" in cmd: os.system("nircmd.exe changesysvolume 5000")
            elif "down" in cmd: os.system("nircmd.exe changesysvolume -5000")
            elif "mute" in cmd: os.system("nircmd.exe mutesysvolume 1")
            elif "unmute" in cmd: os.system("nircmd.exe mutesysvolume 0")
        elif platform.system() == "Darwin":
            if "up" in cmd:
                os.system("osascript -e 'set volume output volume (output volume of (get volume settings) + 10)'")
            elif "down" in cmd:
                os.system("osascript -e 'set volume output volume (output volume of (get volume settings) - 10)'")
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

# -------------------- Voice handler --------------------
def handle_command(cmd: str, hud_ref):
    cmd = cmd.lower().strip()
    if not cmd: return
    hud_ref.update_response(f"You said: {cmd}")

    if cmd.startswith("play "):
        song = cmd[5:].replace("on youtube", "").strip()
        hud_ref.update_response(f"Playing {song} on YouTube...")
        speak(f"Playing {song} on YouTube")
        play_youtube_song(song)
        return

    if any(x in cmd for x in ["volume up","increase volume","volume higher"]):
        adjust_volume("up")
        speak("Volume increased")
        hud_ref.update_response("Volume increased")
        return
    if any(x in cmd for x in ["volume down","decrease volume","volume lower"]):
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

    if "notepad" in cmd:
        hud_ref.update_response("Opening Notepad...")
        speak("Opening Notepad")
        if platform.system() == "Windows": subprocess.Popen(["notepad.exe"])
        return
    if "calculator" in cmd:
        hud_ref.update_response("Opening Calculator...")
        speak("Opening Calculator")
        if platform.system() == "Windows": subprocess.Popen(["calc.exe"])
        return

    if any(x in cmd for x in ["hello","hi","hey"]):
        speak("Hello. I'm Rose, your healer.")
        hud_ref.update_response("Hello. I'm Rose, your healer.")
        return

    speak(f"I heard: {cmd}")
    hud_ref.update_response(f"I heard: {cmd}")

# -------------------- HUD --------------------
class NeonHUD(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(520, 300)
        self.setMinimumSize(360, 220)

        self.icon_pix = self._build_peach_rose_icon(28)

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

        self._drag_pos = None
        self._fade_anim = None
        self._geom_anim = None
        self._grad_phase = 0.0
        self._grad_timer = QTimer(self)
        self._grad_timer.timeout.connect(self._on_grad_tick)
        self._grad_timer.start(40)

        self._wave_phase = 0.0
        self._wave_timer = QTimer(self)
        self._wave_timer.timeout.connect(self._on_wave_tick)
        self._wave_timer.start(35)

        threading.Thread(target=self._start_listening, daemon=True).start()
        self.setWindowOpacity(0.0)
        self._animate_show()

    def _build_peach_rose_icon(self, size_px:int):
        pix = QPixmap(size_px, size_px)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        center = size_px/2
        petal_color = QColor(255,179,153)
        stroke = QColor(210,120,100)
        p.setBrush(petal_color)
        p.setPen(stroke)
        for i in range(5):
            angle = i*(360/5)
            rad = math.radians(angle)
            x = center + math.cos(rad)*(size_px*0.12)
            y = center + math.sin(rad)*(size_px*0.12)
            rect = QRect(int(x-size_px*0.22), int(y-size_px*0.22), int(size_px*0.44), int(size_px*0.44))
            p.drawEllipse(rect)
        p.setBrush(QColor(255,140,120))
        p.drawEllipse(int(center-size_px*0.12), int(center-size_px*0.12), int(size_px*0.24), int(size_px*0.24))
        p.end()
        return pix

    def update_response(self, text:str):
        self.response_label.setText(text)

    def _animate_show(self):
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(420)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        anim.start()
        self._fade_anim = anim

    def _animate_close(self):
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
        if self.isMaximized(): self.showNormal()
        else: self.showMaximized()

    def _on_grad_tick(self):
        self._grad_phase += 0.008
        if self._grad_phase > math.tau: self._grad_phase -= math.tau
        self.update()

    def _on_wave_tick(self):
        self._wave_phase += 0.14
        if self._wave_phase > math.tau: self._wave_phase -= math.tau
        self.update(QRect(20, self.height()-70, self.width()-40, 48))

    def paintEvent(self, ev):
        global TTS_PLAYING
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w,h = self.width(), self.height()
        phase = self._grad_phase
        c1_h = (270 + (math.sin(phase)*20)) %360
        c2_h = (300 + (math.cos(phase*1.3)*18)) %360
        c1 = QColor.fromHsv(int(c1_h),200,160)
        c2 = QColor.fromHsv(int(c2_h),200,180)
        grad = QLinearGradient(0,0,w,h)
        grad.setColorAt(0.0, c1)
        grad.setColorAt(1.0, c2)
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0,0,w,h,20,20)
        painter.drawPixmap(90,6,self.icon_pix)
        painter.setBrush(QColor(255,255,255,10))
        painter.drawRoundedRect(10,10,w-20,h-20,18,18)
        is_speaking=False
        with TTS_LOCK: is_speaking=TTS_PLAYING
        if is_speaking: self._draw_waveform(painter)

        # Title glow
        title_rect = self.title_label.geometry()
        for i in range(4,0,-1):
            alpha=int(30/i)
            glow_color=QColor(255,255,255,alpha)
            painter.setPen(glow_color)
            painter.setFont(QFont("Segoe UI",28+i,QFont.Bold))
            painter.drawText(title_rect,Qt.AlignCenter,self.title_label.text())
        painter.setPen(QColor(255,255,255))
        painter.setFont(QFont("Segoe UI",28,QFont.Bold))
        painter.drawText(title_rect,Qt.AlignCenter,self.title_label.text())

    def _draw_waveform(self, painter:QPainter):
        bar_count=max(8,int(self.width()/28))
        rect_w=self.width()-40
        rect_h=48
        x0=20
        y0=self.height()-80
        spacing=rect_w/bar_count
        base_color=QColor(255,255,255,200)
        for i in range(bar_count):
            phase=self._wave_phase+(i*0.35)
            h_ratio=0.2+0.8*(0.5+0.5*math.sin(phase))
            bar_h=rect_h*h_ratio
            bx=int(x0+i*spacing+spacing*0.15)
            bw=int(spacing*0.7)
            by=int(y0+(rect_h-bar_h)/2)
            alpha=int(120+80*h_ratio)
            col=QColor(base_color.red(),base_color.green(),base_color.blue(),alpha)
            painter.setBrush(col)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(bx,by,bw,int(bar_h),6,6)

    def _start_listening(self):
        recognizer = sr.Recognizer()
        mic = None
        for i,name in enumerate(sr.Microphone.list_microphone_names()):
            if "Microphone" in name or "Array" in name:
                mic = sr.Microphone(device_index=i)
                break
        if mic is None:
            mic = sr.Microphone()  # fallback
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.4
        recognizer.operation_timeout = None
        global LISTENING
        while LISTENING:
            try:
                with mic as source:
                    recognizer.adjust_for_ambient_noise(source,duration=0.5)
                    audio = recognizer.listen(source, phrase_time_limit=5)
                try:
                    text = recognizer.recognize_google(audio)
                    if text.strip(): handle_command(text,self)
                except sr.UnknownValueError: continue
                except sr.RequestError as e: print("Speech recognition error:",e)
            except Exception as e:
                print("Microphone/listen error:",e)
                time.sleep(0.5)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self._drag_pos=ev.globalPosition().toPoint()-self.frameGeometry().topLeft()
            ev.accept()
    def mouseMoveEvent(self, ev):
        if self._drag_pos is not None and ev.buttons() & Qt.LeftButton:
            self.move(ev.globalPosition().toPoint()-self._drag_pos)
            ev.accept()
    def mouseReleaseEvent(self, ev):
        self._drag_pos=None
        ev.accept()
    def closeEvent(self, ev):
        global LISTENING
        LISTENING=False
        time.sleep(0.2)
        ev.accept()

# -------------------- Main --------------------
def main():
    app = QApplication(sys.argv)
    hud = NeonHUD()
    hud.show()
    sys.exit(app.exec())

if __name__=="__main__":
    main()
