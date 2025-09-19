# rose_v27_fixed.py
# Rose Assistant with Clean HUD (no HTML buttons, fixed text, open apps restored)

import sys, os, time, json, asyncio, threading, platform, subprocess, webbrowser, requests
from typing import Optional
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QMenu
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWebEngineWidgets import QWebEngineView

import speech_recognition as sr
import edge_tts
from pytube import Search

# ---------------- Globals ----------------
LISTENING = True
TTS_PLAYING = False
TTS_LOCK = threading.Lock()
BG_LISTENER_STOP = None
CONVERSATION_HISTORY = []
REMINDERS = []

HISTORY_FILE = "rose_history.json"
REMINDERS_FILE = "rose_reminders.json"

# API keys
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
OPENWEATHER_API_KEY = "YOUR_OPENWEATHER_API_KEY"
NEWSAPI_API_KEY = "YOUR_NEWSAPI_API_KEY"

# ---------------- Persistence ----------------
def load_persistent_data():
    global CONVERSATION_HISTORY, REMINDERS
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f: CONVERSATION_HISTORY = json.load(f)
    if os.path.exists(REMINDERS_FILE):
        with open(REMINDERS_FILE, 'r') as f: REMINDERS = json.load(f)

def save_persistent_data():
    with open(HISTORY_FILE, 'w') as f: json.dump(CONVERSATION_HISTORY, f)
    with open(REMINDERS_FILE, 'w') as f: json.dump(REMINDERS, f)

# ---------------- TTS ----------------
def _estimate_tts_duration_seconds(text: str) -> float:
    return max(0.6, len(text.split()) / 2.8)

async def _gen_tts_save(text: str, filename: str = "speech.mp3"):
    comm = edge_tts.Communicate(text, "en-US-JennyNeural")
    await comm.save(filename)

def _play_audio_file(path: str):
    try:
        if platform.system()=="Windows": subprocess.Popen(["start", path], shell=True)
        elif platform.system()=="Darwin": subprocess.Popen(["afplay", path])
        else: subprocess.Popen(["xdg-open", path])
    except Exception as e: print("Playback error:", e)

def speak(text: str):
    def runner():
        global TTS_PLAYING
        with TTS_LOCK: TTS_PLAYING = True
        try:
            asyncio.run(_gen_tts_save(text, "speech.mp3"))
            _play_audio_file("speech.mp3")
            time.sleep(_estimate_tts_duration_seconds(text) + 0.35)
        finally:
            with TTS_LOCK: TTS_PLAYING = False
    threading.Thread(target=runner, daemon=True).start()

# ---------------- Helpers ----------------
def play_youtube_song(song: str):
    try:
        if not song: return webbrowser.open("https://www.youtube.com")
        s = Search(song)
        if not getattr(s,"results",None):
            return webbrowser.open(f"https://www.youtube.com/results?search_query={song.replace(' ','+')}")
        first = s.results[0]
        url = getattr(first,"watch_url",None) or f"https://www.youtube.com/watch?v={first.video_id}"
        webbrowser.open(url)
    except: webbrowser.open(f"https://www.youtube.com/results?search_query={song.replace(' ','+')}")

def get_weather(city: str):
    try:
        r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric").json()
        if r.get("cod")!=200: return "Sorry, couldn't fetch weather."
        return f"The weather in {city} is {r['weather'][0]['description']} with {r['main']['temp']}°C."
    except: return "Weather service failed."

def get_news():
    try:
        r = requests.get(f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWSAPI_API_KEY}").json()
        if r.get("status")!="ok": return "Couldn't fetch news."
        return "Top: " + " ".join(f"{a['title']}." for a in r['articles'][:3])
    except: return "News service failed."

def handle_reminder(cmd_norm: str):
    global REMINDERS
    if "remind me to" in cmd_norm:
        task=cmd_norm.split("remind me to")[-1].strip()
        REMINDERS.append(task); save_persistent_data()
        return f"Reminder added: {task}"
    elif "what are my reminders" in cmd_norm:
        return "Your reminders: " + "; ".join(REMINDERS) if REMINDERS else "You have no reminders."
    return None

# ---------------- HUD ----------------
class RoseHUD(QWidget):
    def __init__(self):
        super().__init__()
        load_persistent_data()
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(600,400)
        self.drag_pos=None
        self.setup_ui(); self._start_background_listener()

    def setup_ui(self):
        # HTML background (stripped buttons)
        self.web_bg=QWebEngineView(self)
        html_path=os.path.abspath("gradient_circle_design.html")
        with open(html_path,"r",encoding="utf-8") as f:
            html=f.read().replace('<div class="top-controls">','<div style="display:none">')  # hide html buttons
        self.web_bg.setHtml(html)
        self.web_bg.setGeometry(0,0,self.width(),self.height())
        self.web_bg.setAttribute(Qt.WA_TransparentForMouseEvents)

        # Rose logo beside buttons
        self.rose_icon=QLabel(self)
        self.rose_icon.setPixmap(QPixmap(32,32))
        self.rose_icon.setStyleSheet("background: transparent;")
        self.rose_icon.setGeometry(65,12,24,24)

        # Title + response
        self.title_label=QLabel("ROSE",self)
        self.title_label.setFont(QFont("Segoe UI",28,QFont.Bold))
        self.title_label.setStyleSheet("color: white;")
        self.title_label.setGeometry(0,40,self.width(),50)
        self.title_label.setAlignment(Qt.AlignCenter)

        self.response_label=QLabel("Hello, I'm Rose.",self)
        self.response_label.setFont(QFont("Segoe UI",14))
        self.response_label.setStyleSheet("color: white;")
        self.response_label.setGeometry(40,300,self.width()-80,80)
        self.response_label.setAlignment(Qt.AlignCenter)
        self.response_label.setWordWrap(True)

        # Mac-style buttons
        self.close_btn=QPushButton(self)
        self.close_btn.setGeometry(15,15,18,18)
        self.close_btn.setStyleSheet("background:#FF5C5C; border-radius:9px;")
        self.close_btn.clicked.connect(self.close)

        self.min_btn=QPushButton(self)
        self.min_btn.setGeometry(40,15,18,18)
        self.min_btn.setStyleSheet("background:#FFBD44; border-radius:9px;")
        self.min_btn.clicked.connect(self.showMinimized)

        # Menu button
        self.menu_btn=QPushButton("☰",self)
        self.menu_btn.setGeometry(self.width()-50,15,30,30)
        self.menu_btn.setStyleSheet("QPushButton{background:rgba(255,255,255,0.2);border-radius:8px;color:white;} QPushButton:hover{background:rgba(255,255,255,0.3);}")
        self.menu=QMenu(self)
        self.menu.addAction("Toggle Flow", lambda:self.inject_js("toggleAnimation()"))
        self.menu.addAction("Change Speed", lambda:self.inject_js("changeSpeed()"))
        self.menu.addAction("Toggle Glow", lambda:self.inject_js("toggleGlow()"))
        self.menu_btn.setMenu(self.menu)

        QTimer.singleShot(900,self._greet)

    def inject_js(self,script): self.web_bg.page().runJavaScript(script)
    def _greet(self): self.update_response("Hi, I'm Rose. How can I help you?"); speak("Hi, I'm Rose. How can I help you?")
    def update_response(self,text): self.response_label.setText(text)

    # Drag & snap
    def mousePressEvent(self,e): 
        if e.button()==Qt.LeftButton: self.drag_pos=e.globalPosition().toPoint()-self.frameGeometry().topLeft()
    def mouseMoveEvent(self,e):
        if self.drag_pos and e.buttons()&Qt.LeftButton: self.move(e.globalPosition().toPoint()-self.drag_pos)

    # Mic
    def _start_background_listener(self):
        rec=sr.Recognizer(); mics=sr.Microphone.list_microphone_names()
        mic_index=0 if mics else None
        if mic_index is None: return
        mic=sr.Microphone(device_index=mic_index)
        def callback(r,a):
            with TTS_LOCK:
                if TTS_PLAYING: return
            try:
                t=r.recognize_google(a)
                if t: threading.Thread(target=handle_command,args=(t,self),daemon=True).start()
            except: return
        global BG_LISTENER_STOP
        BG_LISTENER_STOP=rec.listen_in_background(mic,callback,phrase_time_limit=4)

# ---------------- Commands ----------------
def handle_command(cmd:str,hud_ref:Optional[QWidget]=None):
    cmd_norm=cmd.lower().strip()
    if hud_ref: hud_ref.update_response(f"You said: {cmd_norm}")

    # priority commands first
    if "open youtube" in cmd_norm: speak("Opening YouTube"); webbrowser.open("https://youtube.com"); return
    if "open brave" in cmd_norm: speak("Opening Brave"); os.startfile(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe") if platform.system()=="Windows" else webbrowser.open("https://brave.com"); return
    if "open chrome" in cmd_norm: speak("Opening Chrome"); os.startfile(r"C:\Program Files\Google\Chrome\Application\chrome.exe") if platform.system()=="Windows" else webbrowser.open("https://google.com"); return

    # reminders/weather/news
    r=handle_reminder(cmd_norm)
    if r: speak(r); hud_ref.update_response(r); return
    if "weather" in cmd_norm: reply=get_weather("London"); speak(reply); hud_ref.update_response(reply); return
    if "news" in cmd_norm: reply=get_news(); speak(reply); hud_ref.update_response(reply); return

    # youtube play
    if cmd_norm.startswith("play "): song=cmd_norm.replace("play","").replace("on youtube","").strip(); speak(f"Playing {song} on YouTube"); play_youtube_song(song); return

    # gemini
    global CONVERSATION_HISTORY
    CONVERSATION_HISTORY.append({"role":"user","parts":[{"text":cmd_norm}]})
    try:
        r=requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",json={"contents":CONVERSATION_HISTORY})
        ai_reply=r.json()["candidates"][0]["content"]["parts"][0]["text"]
        CONVERSATION_HISTORY.append({"role":"model","parts":[{"text":ai_reply}]})
        save_persistent_data(); speak(ai_reply); hud_ref.update_response(ai_reply)
    except: hud_ref.update_response("Sorry, I couldn't process that.")

# ---------------- Main ----------------
def main():
    app=QApplication(sys.argv); hud=RoseHUD(); hud.show(); sys.exit(app.exec())

if __name__=="__main__": main()
