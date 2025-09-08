# rose_v7_phase3_alwayson.py
"""
Rose v7 Phase 3 — Always listening, voice output, contextual memory, music control,
jokes/quotes, sleek HUD with neon purple text, persistent main loop.
"""

import os, sys, time, threading, json
import requests
import pyttsx3
import speech_recognition as sr
import pywhatkit
import wikipedia
import pyjokes
from PySide6.QtWidgets import QApplication, QWidget, QTextEdit, QVBoxLayout, QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QColor

# ---------------- CONFIG ----------------
GLOW_COLOR = "#9b30ff"  # neon purple
KB_DIR = "kb_docs"       
INDEX_SAVE = "kb_index"
MAX_MEMORY = 10

# ---------------- Voice & recognizer ----------------
engine = pyttsx3.init()
engine.setProperty("rate", 160)
recognizer = sr.Recognizer()

def talk(text):
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print("TTS error:", e)

# ---------------- Chat memory ----------------
CHAT_HISTORY = []  # stores previous messages as tuples (user, ai)

# ---------------- Utility functions ----------------
def is_online(test_url="https://google.com", timeout=5):
    try:
        requests.get(test_url, timeout=timeout)
        return True
    except:
        return False

def safe_pywhatkit_send(to_number, message, hour, minute):
    if not is_online():
        print("[WARNING] Internet not detected. Cannot send WhatsApp message.")
        return
    try:
        pywhatkit.sendwhatmsg(to_number, message, hour, minute)
        print("[INFO] Message sent successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to send message: {e}")

# ---------------- AI logic / Offline QA ----------------
EMBED_MODEL = "all-MiniLM-L6-v2"
LOCAL_EMBS = None
LOCAL_TEXTS = None
FAISS_INDEX = None
HAS_FAISS = False

def try_load_local_index():
    global LOCAL_EMBS, LOCAL_TEXTS, FAISS_INDEX, HAS_FAISS
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        import faiss
        if os.path.exists(INDEX_SAVE):
            meta_path = os.path.join(INDEX_SAVE, "meta.json")
            emb_path = os.path.join(INDEX_SAVE, "embeddings.npy")
            if os.path.exists(meta_path) and os.path.exists(emb_path):
                with open(meta_path, "r", encoding="utf8") as f:
                    LOCAL_TEXTS = json.load(f)
                LOCAL_EMBS = np.load(emb_path)
                d = LOCAL_EMBS.shape[1]
                index = faiss.IndexFlatL2(d)
                index.add(LOCAL_EMBS)
                FAISS_INDEX = index
                HAS_FAISS = True
                print("Loaded local FAISS index.")
    except Exception as e:
        print("Local index load failed:", e)

def local_qa(query, k=3):
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        model = SentenceTransformer(EMBED_MODEL)
    except Exception:
        return None
    q_emb = model.encode([query], convert_to_numpy=True)
    if HAS_FAISS and FAISS_INDEX is not None:
        D, I = FAISS_INDEX.search(q_emb, k)
        return "\n\n".join([LOCAL_TEXTS[i]["text"] for i in I[0]])
    else:
        sims = (LOCAL_EMBS @ q_emb[0]) / ((np.linalg.norm(LOCAL_EMBS, axis=1) * np.linalg.norm(q_emb[0])) + 1e-8)
        idxs = sims.argsort()[::-1][:k]
        return "\n\n".join([LOCAL_TEXTS[i]["text"] for i in idxs])

# ---------------- Command processing ----------------
def process_command(command):
    command = command.lower()
    global CHAT_HISTORY

    # App commands
    if "open" in command:
        app_name = command.replace("open", "").strip()
        try:
            if "brave" in app_name:
                path = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
                if os.path.exists(path):
                    os.startfile(path)
                else:
                    os.startfile("https://www.google.com")
            elif "chrome" in app_name:
                os.startfile("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
            elif "vscode" in app_name or "code" in app_name:
                os.startfile(f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe")
            else:
                os.startfile("https://www.google.com")
            resp = f"Opened {app_name}"
        except Exception as e:
            resp = f"Failed to open {app_name}: {e}"
        return resp

    # Music control
    if "play" in command:
        song = command.replace("play", "").strip()
        pywhatkit.playonyt(song)
        return f"Playing {song} on YouTube"

    # Wikipedia
    if "wikipedia" in command:
        topic = command.replace("wikipedia", "").strip()
        try:
            return wikipedia.summary(topic, sentences=2)
        except Exception as e:
            return f"Wikipedia error: {e}"

    # Jokes / quotes
    if "joke" in command:
        return pyjokes.get_joke()
    if "quote" in command or "motivation" in command:
        return pywhatkit.info("motivational quotes", return_value=True)[:200]

    # Shutdown
    if "shutdown" in command:
        talk("Shutting down PC")
        os.system("shutdown /s /t 5")
        return "Shutting down PC"

    # Exit
    if "bye" in command or "stop" in command:
        talk("Goodbye!")
        sys.exit()

    # Contextual memory
    memory_prompt = ""
    for u, a in CHAT_HISTORY[-MAX_MEMORY:]:
        memory_prompt += f"User: {u}\nAI: {a}\n"
    memory_prompt += f"User: {command}\nAI:"
    
    # Local QA fallback
    ans = local_qa(command) if LOCAL_EMBS is not None else None
    if ans:
        CHAT_HISTORY.append((command, ans))
        return ans

    # Default
    CHAT_HISTORY.append((command, f"I heard: {command}"))
    return f"I heard: {command}"

# ---------------- Listener Thread ----------------
class ListenerThread(QThread):
    heard_signal = Signal(str)

    def run(self):
        while True:
            try:
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
                    try:
                        text = recognizer.recognize_google(audio)
                        if text.strip():
                            self.heard_signal.emit(text)
                    except sr.UnknownValueError:
                        continue
            except Exception:
                continue

# ---------------- HUD ----------------
class RoseHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        screen = app.primaryScreen().geometry()
        width, height = 520, 380
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.setGeometry(x, y, width, height)
        self.setStyleSheet("background-color: rgba(0,0,0,200); border-radius: 12px;")

        layout = QVBoxLayout()
        self.text_area = QTextEdit()
        self.text_area.setStyleSheet(f"background-color: rgba(0,0,0,0); color: {GLOW_COLOR}; font-family: Consolas; font-size: 12pt;")
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)

        exit_btn = QPushButton("Exit")
        exit_btn.setStyleSheet("background-color: rgba(255,0,0,160); color: white; font-weight: bold;")
        exit_btn.clicked.connect(lambda: sys.exit())
        layout.addWidget(exit_btn)

        self.setLayout(layout)

        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(30)
        glow.setColor(QColor(GLOW_COLOR))
        glow.setOffset(0)
        self.text_area.setGraphicsEffect(glow)

        # Listener
        self.listener = ListenerThread()
        self.listener.heard_signal.connect(self.on_command)
        self.listener.start()

        self.append_text("🌹 Rose v7 online — listening...")

        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_scroll)
        self.timer.start(250)

    def append_text(self, t):
        self.text_area.append(t)
        self.text_area.repaint()

    def on_command(self, command):
        self.append_text(f"You said: {command}")
        threading.Thread(target=self._process_and_show, args=(command,), daemon=True).start()

    def _process_and_show(self, command):
        self.append_text("Rose: thinking...")
        resp = process_command(command)
        self.append_text(f"Rose: {resp}")
        talk(resp)

    def auto_scroll(self):
        sb = self.text_area.verticalScrollBar()
        sb.setValue(sb.maximum())

# ---------------- MAIN ----------------
if __name__ == "__main__":
    try_load_local_index()
    app = QApplication(sys.argv)
    hud = RoseHUD()
    hud.show()
    sys.exit(app.exec())
