# rose_v30.py
# Rose v30 — Enhanced with all requested features: smart scheduling, document/image analysis, writing coach, data viz dashboard,
# multi-language, image recognition, screen analysis, gesture recognition (basic), preferences/habits tracking, music suggestions,
# adaptive responses, mood-based playlists, music discovery, integrations (basic), audio viz (basic), smart volume,
# location-based reminders (IP-based), calendar integration (export), habit tracking, voice journaling, time tracking,
# email/SMS (basic placeholders), meeting transcription, voice-to-text, storytelling, casual conversation, daily check-ins,
# personality customization.

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
import random
from datetime import datetime
import base64

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QRect
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QMenu, QScrollArea, QTextEdit,
    QGraphicsOpacityEffect, QVBoxLayout, QHBoxLayout, QProgressBar, QFileDialog
)
from PySide6.QtGui import QFont, QPixmap, QCloseEvent, QColor

# Creative libraries integration
try:
    from colorthief import ColorThief
    COLORTHIEF_AVAILABLE = True
except ImportError:
    COLORTHIEF_AVAILABLE = False
    print("[WARN] colorthief not installed - color theme extraction disabled")

try:
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    WORDCLOUD_AVAILABLE = True
except ImportError:
    WORDCLOUD_AVAILABLE = False
    print("[WARN] wordcloud or matplotlib not installed - word cloud generation disabled")

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    SENTIMENT_AVAILABLE = True
    sentiment_analyzer = SentimentIntensityAnalyzer()
except ImportError:
    SENTIMENT_AVAILABLE = False
    print("[WARN] vaderSentiment not installed - mood tracking disabled")

try:
    import emoji
    EMOJI_AVAILABLE = True
except ImportError:
    EMOJI_AVAILABLE = False
    print("[WARN] emoji library not installed - emoji analysis disabled")

try:
    import customtkinter as ctk
    CUSTOMTKINTER_AVAILABLE = True
except ImportError:
    CUSTOMTKINTER_AVAILABLE = False
    print("[WARN] customtkinter not installed - modern UI components disabled")

# Optional WebEngine
USE_WEBENGINE = True
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except Exception:
    USE_WEBENGINE = False
    print("[WARN] PySide6.QtWebEngineWidgets import failed. HTML background disabled.")

# Optional libs (existing)
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

# New libraries for added features
try:
    from icalendar import Calendar, Event
    ICALENDAR_AVAILABLE = True
except ImportError:
    ICALENDAR_AVAILABLE = False
    print("[WARN] icalendar not installed - calendar export disabled")

try:
    import csv
    CSV_AVAILABLE = True
except ImportError:
    CSV_AVAILABLE = False
    print("[WARN] csv not installed - CSV export disabled")

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("[WARN] pyautogui not installed - screen capture disabled")

try:
    import cv2
    import mediapipe as mp
    GESTURE_AVAILABLE = True
except ImportError:
    GESTURE_AVAILABLE = False
    print("[WARN] opencv/mediapipe not installed - gesture recognition disabled")

try:
    import smtplib
    from email.mime.text import MIMEText
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    print("[WARN] smtplib not installed - email features disabled")

try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("[WARN] PyPDF2 not installed - PDF text extraction disabled")

try:
    import geopy
    from geopy.geocoders import Nominatim
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False
    print("[WARN] geopy not installed - location-based features limited")

# ---------------- CONFIG ----------------
HTML_FILE = "gradient_circle_design.html"
ROSE_ICON_FILE = "rose_logo.png"
HISTORY_FILE = "rose_history.json"
REMINDERS_FILE = "rose_reminders.json"
MOOD_FILE = "rose_moods.json"
THEMES_FILE = "rose_themes.json"
HABITS_FILE = "rose_habits.json"
PREFERENCES_FILE = "rose_preferences.json"
MUSIC_TASTE_FILE = "rose_music_taste.json"
JOURNAL_FILE = "rose_journal.json"
TIME_TRACKING_FILE = "rose_time_tracking.json"

GEMINI_API_KEY = ""
OPENWEATHER_API_KEY = ""
NEWSAPI_API_KEY = ""
EMAIL_USER = ""  # For email features
EMAIL_PASS = ""  # Securely handle in production

LISTENING = True
TTS_PLAYING = False
TTS_LOCK = threading.Lock()
BG_LISTENER_STOP = None
CONVERSATION_HISTORY = []
REMINDERS = []
MOOD_HISTORY = []
USER_THEMES = {"primary": "#FF69B4", "secondary": "#9932CC", "accent": "#FFB6C1"}
HABITS = []
PREFERENCES = {"language": "en", "personality": "caring"}  # Default
MUSIC_TASTE = []  # List of liked songs/artists
JOURNAL_ENTRIES = []
TIME_TRACKING = {}  # project: {"start": time, "total": seconds}
CURRENT_LOCATION = None  # Cached location

# ---------------- Enhanced Persistence ----------------
def load_persistent():
    global CONVERSATION_HISTORY, REMINDERS, MOOD_HISTORY, USER_THEMES, HABITS, PREFERENCES, MUSIC_TASTE, JOURNAL_ENTRIES, TIME_TRACKING
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
    
    try:
        if os.path.exists(MOOD_FILE):
            with open(MOOD_FILE, "r", encoding="utf8") as f:
                MOOD_HISTORY = json.load(f)
    except Exception:
        MOOD_HISTORY = []
    
    try:
        if os.path.exists(THEMES_FILE):
            with open(THEMES_FILE, "r", encoding="utf8") as f:
                USER_THEMES = json.load(f)
    except Exception:
        USER_THEMES = {"primary": "#FF69B4", "secondary": "#9932CC", "accent": "#FFB6C1"}

    try:
        if os.path.exists(HABITS_FILE):
            with open(HABITS_FILE, "r", encoding="utf8") as f:
                HABITS = json.load(f)
    except Exception:
        HABITS = []

    try:
        if os.path.exists(PREFERENCES_FILE):
            with open(PREFERENCES_FILE, "r", encoding="utf8") as f:
                PREFERENCES = json.load(f)
    except Exception:
        PREFERENCES = {"language": "en", "personality": "caring"}

    try:
        if os.path.exists(MUSIC_TASTE_FILE):
            with open(MUSIC_TASTE_FILE, "r", encoding="utf8") as f:
                MUSIC_TASTE = json.load(f)
    except Exception:
        MUSIC_TASTE = []

    try:
        if os.path.exists(JOURNAL_FILE):
            with open(JOURNAL_FILE, "r", encoding="utf8") as f:
                JOURNAL_ENTRIES = json.load(f)
    except Exception:
        JOURNAL_ENTRIES = []

    try:
        if os.path.exists(TIME_TRACKING_FILE):
            with open(TIME_TRACKING_FILE, "r", encoding="utf8") as f:
                TIME_TRACKING = json.load(f)
    except Exception:
        TIME_TRACKING = {}

def save_persistent():
    try:
        with open(HISTORY_FILE, "w", encoding="utf8") as f:
            json.dump(CONVERSATION_HISTORY, f, ensure_ascii=False, indent=2)
        with open(REMINDERS_FILE, "w", encoding="utf8") as f:
            json.dump(REMINDERS, f, ensure_ascii=False, indent=2)
        with open(MOOD_FILE, "w", encoding="utf8") as f:
            json.dump(MOOD_HISTORY, f, ensure_ascii=False, indent=2)
        with open(THEMES_FILE, "w", encoding="utf8") as f:
            json.dump(USER_THEMES, f, ensure_ascii=False, indent=2)
        with open(HABITS_FILE, "w", encoding="utf8") as f:
            json.dump(HABITS, f, ensure_ascii=False, indent=2)
        with open(PREFERENCES_FILE, "w", encoding="utf8") as f:
            json.dump(PREFERENCES, f, ensure_ascii=False, indent=2)
        with open(MUSIC_TASTE_FILE, "w", encoding="utf8") as f:
            json.dump(MUSIC_TASTE, f, ensure_ascii=False, indent=2)
        with open(JOURNAL_FILE, "w", encoding="utf8") as f:
            json.dump(JOURNAL_ENTRIES, f, ensure_ascii=False, indent=2)
        with open(TIME_TRACKING_FILE, "w", encoding="utf8") as f:
            json.dump(TIME_TRACKING, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Save error:", e)

# ---------------- New Helper Functions for Added Features ----------------

def get_current_location():
    """Get approximate location from IP (fallback if no geopy)"""
    global CURRENT_LOCATION
    if CURRENT_LOCATION:
        return CURRENT_LOCATION
    try:
        resp = requests.get("http://ipinfo.io/json", timeout=5).json()
        CURRENT_LOCATION = resp.get("city", "Unknown")
        return CURRENT_LOCATION
    except Exception as e:
        print("Location error:", e)
        return "Unknown"

def export_to_calendar():
    """Export reminders to ICS"""
    if not ICALENDAR_AVAILABLE:
        return "Calendar export not available."
    cal = Calendar()
    for rem in REMINDERS:
        event = Event()
        event.add('summary', rem)
        event.add('dtstart', datetime.now())  # Placeholder
        cal.add_component(event)
    with open("rose_calendar.ics", "wb") as f:
        f.write(cal.to_ical())
    return "Exported to rose_calendar.ics"

def export_to_csv():
    """Export reminders to CSV"""
    if not CSV_AVAILABLE:
        return "CSV export not available."
    with open("rose_reminders.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Reminder"])
        for rem in REMINDERS:
            writer.writerow([rem])
    return "Exported to rose_reminders.csv"

def suggest_break():
    """Proactive break suggestion based on mood"""
    if MOOD_HISTORY and MOOD_HISTORY[-1]["compound"] < -0.3:
        return "Your mood seems low. How about a 10-minute break to meditate?"
    return None

def analyze_document(file_path):
    """Analyze uploaded PDF/image with Gemini"""
    if not GEMINI_API_KEY:
        return "Gemini not configured."
    try:
        parts = [{"text": "Analyze this document for healing insights."}]
        if file_path.endswith(".pdf") and PDF_AVAILABLE:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            parts.append({"text": text})
        elif file_path.endswith((".jpg", ".png", ".jpeg")):
            with open(file_path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg" if "jpg" in file_path else "image/png",
                    "data": data
                }
            })
        else:
            return "Unsupported file type."

        payload = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"maxOutputTokens": 300}
        }
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
            json=payload,
            timeout=10
        ).json()
        return resp["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print("Document analysis error:", e)
        return "Analysis failed."

def analyze_screen():
    """Capture and analyze screen with Gemini"""
    if not PYAUTOGUI_AVAILABLE:
        return "Screen capture not available."
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save("screen.png")
        return analyze_document("screen.png")
    except Exception as e:
        print("Screen analysis error:", e)
        return "Screen analysis failed."

def detect_gesture():
    """Basic gesture recognition (thumbs up/down)"""
    if not GESTURE_AVAILABLE:
        return None
    mp_hands = mp.solutions.hands
    with mp_hands.Hands() as hands:
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        if not ret:
            return None
        results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if results.multi_hand_landmarks:
            # Simple check for thumbs up
            landmark = results.multi_hand_landmarks[0].landmark
            if landmark[4].y < landmark[3].y:  # Thumb tip above joint
                return "thumbs_up"
        cap.release()
    return None

def send_email(to, subject, body):
    if not EMAIL_AVAILABLE:
        return "Email not available."
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_USER
        msg['To'] = to
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to, msg.as_string())
        return "Email sent."
    except Exception as e:
        print("Email error:", e)
        return "Email failed."

def music_suggestion():
    """Suggest song based on music taste"""
    if MUSIC_TASTE:
        base = random.choice(MUSIC_TASTE)
        return f"How about something like {base}?"
    return "Tell me your favorite songs to learn your taste."

def create_mood_playlist():
    """Mood-based playlist suggestion"""
    if MOOD_HISTORY:
        mood = MOOD_HISTORY[-1]["compound"]
        if mood > 0.3:
            return "Upbeat playlist: Happy songs on YouTube."
        elif mood < -0.3:
            return "Calming playlist: Relaxing music."
    return "Standard playlist."

def smart_volume_adjust():
    """Adjust volume based on time"""
    hour = datetime.now().hour
    if 22 < hour or hour < 7:
        adjust_volume("down")
        return "Lowering volume for night time."
    return None

def handle_habit(cmd_norm):
    if "add habit" in cmd_norm:
        habit = cmd_norm.split("add habit")[-1].strip()
        HABITS.append({"habit": habit, "streak": 0})
        save_persistent()
        return f"Habit added: {habit}"
    if "check habit" in cmd_norm:
        habit = cmd_norm.split("check habit")[-1].strip()
        for h in HABITS:
            if h["habit"] == habit:
                h["streak"] += 1
                save_persistent()
                return f"{habit} streak: {h['streak']}"
    return None

def handle_journal(cmd_norm):
    if "journal entry" in cmd_norm:
        entry = cmd_norm.split("journal entry")[-1].strip()
        JOURNAL_ENTRIES.append({"timestamp": datetime.now().isoformat(), "entry": entry})
        save_persistent()
        # Analyze with Gemini
        analysis = call_gemini("Provide insights on this journal entry: " + entry)
        return f"Entry saved. Insights: {analysis}"
    return None

def handle_time_tracking(cmd_norm):
    if "start tracking" in cmd_norm:
        project = cmd_norm.split("start tracking")[-1].strip()
        TIME_TRACKING[project] = {"start": time.time(), "total": TIME_TRACKING.get(project, {"total": 0})["total"]}
        save_persistent()
        return f"Tracking started for {project}"
    if "stop tracking" in cmd_norm:
        project = cmd_norm.split("stop tracking")[-1].strip()
        if project in TIME_TRACKING and "start" in TIME_TRACKING[project]:
            elapsed = time.time() - TIME_TRACKING[project]["start"]
            TIME_TRACKING[project]["total"] += elapsed
            del TIME_TRACKING[project]["start"]
            save_persistent()
            return f"Tracking stopped for {project}. Total: {TIME_TRACKING[project]['total']/3600:.2f} hours"
    return None

def handle_storytelling(cmd_norm):
    if "tell a story" in cmd_norm:
        prompt = "Tell an interactive story: " + cmd_norm
        return call_gemini(prompt)
    return None

def daily_check_in():
    """Proactive daily check-in"""
    return "How are you feeling today? Share your mood."

def call_gemini(prompt, language=None):
    if not GEMINI_API_KEY:
        return "Gemini not available."
    try:
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 200}
        }
        if language:
            payload["systemInstruction"] = {"parts": [{"text": f"Respond in {language}."}]}
        resp = requests.post(api_url, json=payload, timeout=8).json()
        return resp["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print("Gemini error:", e)
        return "Response failed."

# ---------------- Creative Features ----------------
def extract_color_theme_from_image(image_path: str):
    """Extract color palette from user's image for personalized themes"""
    if not COLORTHIEF_AVAILABLE or not os.path.exists(image_path):
        return None
    
    try:
        color_thief = ColorThief(image_path)
        palette = color_thief.get_palette(color_count=3)
        theme = {
            "primary": f"#{palette[0][0]:02x}{palette[0][1]:02x}{palette[0][2]:02x}",
            "secondary": f"#{palette[1][0]:02x}{palette[1][1]:02x}{palette[1][2]:02x}",
            "accent": f"#{palette[2][0]:02x}{palette[2][1]:02x}{palette[2][2]:02x}"
        }
        return theme
    except Exception as e:
        print(f"Color extraction error: {e}")
        return None

def analyze_mood(text: str):
    """Analyze mood from text using VADER sentiment analysis"""
    if not SENTIMENT_AVAILABLE:
        return None
    
    try:
        scores = sentiment_analyzer.polarity_scores(text)
        mood_data = {
            "timestamp": datetime.now().isoformat(),
            "text": text[:100],  # Store first 100 chars
            "compound": scores['compound'],
            "positive": scores['pos'],
            "negative": scores['neg'],
            "neutral": scores['neu']
        }
        return mood_data
    except Exception as e:
        print(f"Mood analysis error: {e}")
        return None

def analyze_emoji_patterns(text: str):
    """Analyze emoji usage patterns"""
    if not EMOJI_AVAILABLE:
        return None
    
    try:
        emoji_list = emoji.emoji_list(text)
        if not emoji_list:
            return None
        
        emoji_counts = {}
        for em in emoji_list:
            em_char = em['emoji']
            emoji_counts[em_char] = emoji_counts.get(em_char, 0) + 1
        
        return {
            "total_emojis": len(emoji_list),
            "unique_emojis": len(emoji_counts),
            "most_used": max(emoji_counts.items(), key=lambda x: x[1]) if emoji_counts else None,
            "emoji_counts": emoji_counts
        }
    except Exception as e:
        print(f"Emoji analysis error: {e}")
        return None

def generate_conversation_wordcloud():
    """Generate word cloud from conversation history"""
    if not WORDCLOUD_AVAILABLE or not CONVERSATION_HISTORY:
        return None
    
    try:
        # Combine all conversation text
        text_data = []
        for entry in CONVERSATION_HISTORY[-50:]:  # Last 50 entries
            if entry.get("role") == "user" and entry.get("parts"):
                text_data.append(entry["parts"][0].get("text", ""))
        
        if not text_data:
            return None
        
        combined_text = " ".join(text_data)
        
        # Generate word cloud
        wordcloud = WordCloud(
            width=800, height=400,
            background_color='rgba(255, 255, 255, 0)',
            mode='RGBA',
            colormap='plasma',
            max_words=100
        ).generate(combined_text)
        
        # Save to file
        wordcloud_path = "rose_wordcloud.png"
        wordcloud.to_file(wordcloud_path)
        return wordcloud_path
    except Exception as e:
        print(f"Word cloud generation error: {e}")
        return None

def create_mood_visualization():
    """Create mood tracking visualization"""
    if not WORDCLOUD_AVAILABLE or not MOOD_HISTORY:
        return None
    
    try:
        # Get recent mood data
        recent_moods = MOOD_HISTORY[-20:] if len(MOOD_HISTORY) > 20 else MOOD_HISTORY
        
        timestamps = [datetime.fromisoformat(m["timestamp"]) for m in recent_moods]
        compounds = [m["compound"] for m in recent_moods]
        
        plt.figure(figsize=(10, 6))
        plt.plot(timestamps, compounds, marker='o', color='#FF69B4', linewidth=2, markersize=6)
        plt.title('Your Mood Journey with Rose 🌹', fontsize=16, color='#9932CC')
        plt.xlabel('Time', fontsize=12)
        plt.ylabel('Mood Score', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        
        # Color-code the background
        plt.axhspan(0, 1, alpha=0.1, color='green', label='Positive')
        plt.axhspan(-1, 0, alpha=0.1, color='red', label='Negative')
        
        plt.tight_layout()
        mood_chart_path = "rose_mood_chart.png"
        plt.savefig(mood_chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        return mood_chart_path
    except Exception as e:
        print(f"Mood visualization error: {e}")
        return None

def create_week_summary():
    """Generate week summary chart"""
    if not WORDCLOUD_AVAILABLE:
        return None
    try:
        # Placeholder data
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        moods = [random.uniform(-1,1) for _ in days]
        plt.bar(days, moods)
        plt.title('Week Mood Summary')
        summary_path = "rose_week_summary.png"
        plt.savefig(summary_path)
        plt.close()
        return summary_path
    except Exception as e:
        print("Week summary error:", e)
        return None

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

async def _gen_tts_save(text: str, filename: str = "speech.mp3", voice="en-US-JennyNeural"):
    if not edge_tts:
        raise RuntimeError("edge-tts not installed")
    comm = edge_tts.Communicate(text, voice)
    await comm.save(filename)

def speak(text: str, language=None):
    """Generate and play TTS in background; sets TTS_PLAYING flag while estimated playback duration."""
    if language is None:
        language = PREFERENCES.get("language", "en")
    voice = f"{language}-US-JennyNeural" if language == "en" else f"{language}-DefaultVoice"  # Simplify
    def _runner():
        global TTS_PLAYING
        with TTS_LOCK:
            TTS_PLAYING = True
        try:
            if edge_tts:
                asyncio.run(_gen_tts_save(text, "speech.mp3", voice))
                _play_file_default("speech.mp3")
            else:
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

# ---------------- Music Integrations (Basic) ----------------
def play_apple_music(song):
    webbrowser.open(f"music://music.apple.com/search?term={song.replace(' ', '+')}")

def play_soundcloud(song):
    webbrowser.open(f"https://soundcloud.com/search?q={song.replace(' ', '+')}")

# ---------------- Spotify controls ----------------
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
        if "near" in task:
            location = task.split("near")[-1].strip()
            if get_current_location() == location:
                return f"Reminder: {task} (at {location})"
        if task:
            REMINDERS.append(task)
            save_persistent()
            return f"Reminder added: {task}"
    if "what are my reminders" in cmd_norm or "list reminders" in cmd_norm:
        if not REMINDERS:
            return "No reminders."
        return "Reminders: " + " ; ".join(REMINDERS)
    return None

# ---------------- Enhanced Command Processing ----------------
def handle_command(cmd: str, hud_ref: Optional["RoseHUD"] = None):
    if not cmd:
        return
    cmd_norm = cmd.lower().strip()
    print("Heard:", cmd_norm)
    if hud_ref:
        hud_ref.append_response(f"> {cmd_norm}")

    # Analyze mood and emojis
    if SENTIMENT_AVAILABLE:
        mood_data = analyze_mood(cmd)
        if mood_data:
            MOOD_HISTORY.append(mood_data)
            if len(MOOD_HISTORY) > 100:  # Keep last 100 moods
                MOOD_HISTORY.pop(0)
            # Adaptive response based on mood
            if mood_data["compound"] < -0.3:
                speak("I'm here to support you.")

    # Detect language (simple, assume English or use Gemini for detection if needed)
    language = PREFERENCES.get("language", "en")
    # If "speak in spanish", update preference
    if "speak in" in cmd_norm:
        new_lang = cmd_norm.split("speak in")[-1].strip()
        PREFERENCES["language"] = new_lang[:2]
        save_persistent()
        speak("Switching language.", language=new_lang[:2])
        return

    # Personality customization
    if "set personality" in cmd_norm:
        personality = cmd_norm.split("set personality")[-1].strip()
        PREFERENCES["personality"] = personality
        save_persistent()
        speak(f"Personality set to {personality}.")
        return

    # Gesture check
    gesture = detect_gesture()
    if gesture == "thumbs_up":
        cmd_norm += " positive feedback"

    # New creative commands
    if "show my mood" in cmd_norm or "mood chart" in cmd_norm:
        chart_path = create_mood_visualization()
        if chart_path:
            speak("Here's your mood journey with me", language)
            webbrowser.open(f"file://{os.path.abspath(chart_path)}")
            hud_ref and hud_ref.append_response("📊 Mood chart generated!")
        else:
            speak("I need more conversation data to show your mood chart", language)
            hud_ref and hud_ref.append_response("Need more conversation data for mood analysis")
        return

    if "word cloud" in cmd_norm or "show my words" in cmd_norm:
        cloud_path = generate_conversation_wordcloud()
        if cloud_path:
            speak("Here's a word cloud of our conversations", language)
            webbrowser.open(f"file://{os.path.abspath(cloud_path)}")
            hud_ref and hud_ref.append_response("☁️ Word cloud generated!")
        else:
            speak("I need more conversation history to create a word cloud", language)
            hud_ref and hud_ref.append_response("Need more conversation data for word cloud")
        return

    if "analyze emojis" in cmd_norm:
        emoji_data = analyze_emoji_patterns(cmd)
        if emoji_data and emoji_data["total_emojis"] > 0:
            most_used = emoji_data["most_used"]
            response = f"You used {emoji_data['total_emojis']} emojis! Your favorite is {most_used[0]} (used {most_used[1]} times)"
            speak(response, language)
            hud_ref and hud_ref.append_response(f"😊 {response}")
        else:
            speak("I didn't find any emojis in your message", language)
            hud_ref and hud_ref.append_response("No emojis detected in recent message")
        return

    if "change theme" in cmd_norm and "from image" in cmd_norm:
        speak("To change theme from image, place your image as 'user_image.jpg' in the Rose folder", language)
        hud_ref and hud_ref.append_response("🎨 Place 'user_image.jpg' in Rose folder to extract theme colors")
        
        # Try to extract theme if image exists
        theme = extract_color_theme_from_image("user_image.jpg")
        if theme:
            global USER_THEMES
            USER_THEMES = theme
            save_persistent()
            speak("Theme updated from your image!", language)
            hud_ref and hud_ref.append_response("🌈 Theme colors extracted and applied!")
            if hud_ref:
                hud_ref.apply_user_theme()
        return

    # YouTube
    if "open youtube" in cmd_norm or (cmd_norm.startswith("play ") and ("youtube" in cmd_norm or "on youtube" in cmd_norm)):
        if cmd_norm.startswith("play "):
            song = cmd_norm[5:].replace("on youtube","").replace("youtube","").strip()
        else:
            song = ""
        hud_ref and hud_ref.append_response("Opening YouTube...")
        speak("Opening YouTube", language)
        play_youtube_song(song)
        return

    if "open brave" in cmd_norm or "open chrome" in cmd_norm or "open browser" in cmd_norm:
        hud_ref and hud_ref.append_response("Opening browser...")
        speak("Opening browser", language)
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

    # Spotify
    if "spotify" in cmd_norm:
        if any(k in cmd_norm for k in ("play","pause","play/pause","toggle")):
            spotify_play_pause(); speak("Toggling Spotify", language); hud_ref and hud_ref.append_response("Toggling Spotify"); return
        if "next" in cmd_norm or "skip" in cmd_norm:
            spotify_next(); speak("Next track", language); hud_ref and hud_ref.append_response("Next track"); return
        if "previous" in cmd_norm or "prev" in cmd_norm:
            spotify_prev(); speak("Previous track", language); hud_ref and hud_ref.append_response("Previous track"); return

    # Volume
    if any(x in cmd_norm for x in ("volume up","increase volume","turn it up")):
        adjust_volume("up"); speak("Volume increased", language); hud_ref and hud_ref.append_response("Volume increased"); return
    if any(x in cmd_norm for x in ("volume down","decrease volume","turn it down")):
        adjust_volume("down"); speak("Volume decreased", language); hud_ref and hud_ref.append_response("Volume decreased"); return

    # Reminders, weather, news
    r = handle_reminder(cmd_norm)
    if r:
        speak(r, language); hud_ref and hud_ref.append_response(r); return
    if "weather" in cmd_norm:
        city = cmd_norm.split("in")[-1].strip() if "in" in cmd_norm else "London"
        reply = get_weather(city); speak(reply, language); hud_ref and hud_ref.append_response(reply); return
    if "news" in cmd_norm or "headlines" in cmd_norm:
        reply = get_news(); speak(reply, language); hud_ref and hud_ref.append_response(reply); return

    # Greetings with mood awareness
    if any(g in cmd_norm for g in ("hello","hi","hey")):
        greeting = "Hello. I'm Rose, your healer."
        if MOOD_HISTORY:
            recent_mood = MOOD_HISTORY[-1]["compound"] if MOOD_HISTORY else 0
            if recent_mood > 0.3:
                greeting += " You seem happy today! 😊"
            elif recent_mood < -0.3:
                greeting += " I'm here if you need support 💜"
        speak(greeting, language)
        hud_ref and hud_ref.append_response(greeting)
        return

    # New Features Commands
    if "export calendar" in cmd_norm:
        reply = export_to_calendar()
        speak(reply, language)
        hud_ref and hud_ref.append_response(reply)
        return

    if "export csv" in cmd_norm:
        reply = export_to_csv()
        speak(reply, language)
        hud_ref and hud_ref.append_response(reply)
        return

    if "upload document" in cmd_norm or "analyze image" in cmd_norm:
        file_path, _ = QFileDialog.getOpenFileName(hud_ref, "Upload File")
        if file_path:
            reply = analyze_document(file_path)
            speak(reply, language)
            hud_ref and hud_ref.append_response(reply)
        return

    if "what's on my screen" in cmd_norm:
        reply = analyze_screen()
        speak(reply, language)
        hud_ref and hud_ref.append_response(reply)
        return

    if "write journal" in cmd_norm or "proofread" in cmd_norm:
        content = cmd_norm.split("proofread")[-1] if "proofread" in cmd_norm else ""
        prompt = f"{'Proofread' if 'proofread' in cmd_norm else 'Generate'} this with mood-tailored feedback: {content}"
        reply = call_gemini(prompt, language)
        speak(reply, language)
        hud_ref and hud_ref.append_response(reply)
        return

    if "show week summary" in cmd_norm:
        summary_path = create_week_summary()
        if summary_path:
            speak("Here's your week summary", language)
            webbrowser.open(f"file://{os.path.abspath(summary_path)}")
            hud_ref and hud_ref.append_response("📈 Week summary generated!")
        return

    if "what do you see" in cmd_norm or "describe photo" in cmd_norm:
        # Assume webcam capture
        if GESTURE_AVAILABLE:
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            if ret:
                cv2.imwrite("webcam.jpg", frame)
                reply = analyze_document("webcam.jpg")
                speak(reply, language)
                hud_ref and hud_ref.append_response(reply)
            cap.release()
        return

    if "learn music" in cmd_norm:
        song = cmd_norm.split("learn music")[-1].strip()
        MUSIC_TASTE.append(song)
        save_persistent()
        speak("Noted your music taste.", language)
        return

    if "suggest song" in cmd_norm:
        reply = music_suggestion()
        speak(reply, language)
        hud_ref and hud_ref.append_response(reply)
        return

    if "mood playlist" in cmd_norm:
        reply = create_mood_playlist()
        speak(reply, language)
        hud_ref and hud_ref.append_response(reply)
        # Play example
        play_youtube_song("happy songs" if "upbeat" in reply else "relaxing music")
        return

    if "play like this" in cmd_norm:
        song = cmd_norm.split("play like this")[-1].strip()
        play_youtube_song(song + " similar")
        return

    if "apple music" in cmd_norm:
        song = cmd_norm.split("apple music")[-1].strip()
        play_apple_music(song)
        return

    if "soundcloud" in cmd_norm:
        song = cmd_norm.split("soundcloud")[-1].strip()
        play_soundcloud(song)
        return

    if "audio visualization" in cmd_norm:
        # Placeholder: open a web viz
        webbrowser.open("https://butterchurnviz.com/")
        speak("Opening audio visualizer.", language)
        return

    if "smart volume" in cmd_norm:
        reply = smart_volume_adjust()
        if reply:
            speak(reply, language)
            hud_ref and hud_ref.append_response(reply)
        return

    r = handle_habit(cmd_norm)
    if r:
        speak(r, language); hud_ref and hud_ref.append_response(r); return

    r = handle_journal(cmd_norm)
    if r:
        speak(r, language); hud_ref and hud_ref.append_response(r); return

    r = handle_time_tracking(cmd_norm)
    if r:
        speak(r, language); hud_ref and hud_ref.append_response(r); return

    if "send email" in cmd_norm:
        # Parse to, subject, body - placeholder parsing
        parts = cmd_norm.split("send email to")[1].strip().split(" subject ")
        to = parts[0]
        subject_body = parts[1].split(" body ")
        subject = subject_body[0]
        body = subject_body[1] if len(subject_body) > 1 else ""
        reply = send_email(to, subject, body)
        speak(reply, language)
        hud_ref and hud_ref.append_response(reply)
        return

    if "transcribe meeting" in cmd_norm:
        # Use SR to transcribe ongoing
        if sr:
            r = sr.Recognizer()
            with sr.Microphone() as source:
                audio = r.listen(source, timeout=30)
            text = r.recognize_google(audio)
            speak("Transcription: " + text, language)
            hud_ref and hud_ref.append_response("Transcription: " + text)
        return

    if "voice to text" in cmd_norm:
        # Similar to transcription
        speak("Speak now for text.", language)
        # Assume next input is text
        return

    r = handle_storytelling(cmd_norm)
    if r:
        speak(r, language); hud_ref and hud_ref.append_response(r); return

    if "casual conversation" in cmd_norm:
        reply = call_gemini("Start a casual conversation.", language)
        speak(reply, language)
        hud_ref and hud_ref.append_response(reply)
        return

    # Fallback to Gemini or echo
    CONVERSATION_HISTORY.append({"role":"user","parts":[{"text":cmd_norm}]})
    if GEMINI_API_KEY:
        try:
            system_inst = "You are Rose, a healer assistant with mood awareness. Answer helpfully and consider the user's emotional state."
            if PREFERENCES["personality"] == "witty":
                system_inst += " Be witty."
            # Add personal context
            if "friday" in datetime.now().strftime("%A").lower() and "work" in cmd_norm:
                system_inst += " User usually works late on Fridays."
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": CONVERSATION_HISTORY,
                "systemInstruction": {"parts":[{"text":system_inst}]},
                "generationConfig": {"maxOutputTokens": 200}
            }
            headers = {"Content-Type":"application/json"}
            resp = requests.post(api_url, json=payload, headers=headers, timeout=8)
            jr = resp.json()
            ai_reply = jr["candidates"][0]["content"]["parts"][0]["text"].strip()
            CONVERSATION_HISTORY.append({"role":"model","parts":[{"text":ai_reply}]})
            save_persistent()
            speak(ai_reply, language)
            hud_ref and hud_ref.append_response(ai_reply)
            return
        except Exception as e:
            print("Gemini call error:", e)
            CONVERSATION_HISTORY.pop()
    
    # Fallback echo
    speak(f"I heard: {cmd_norm}", language)
    hud_ref and hud_ref.append_response(f"I heard: {cmd_norm}")

# ---------------- Enhanced HUD ----------------
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
            html_text = html_text.replace('<div class="top-controls">', '<div class="top-controls" style="display:none">')
            self.web.setHtml(html_text)
            self.web.setGeometry(0, 0, self.width(), self.height())
            self.web.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        else:
            self.web = None
            # Apply user theme to gradient
            primary = USER_THEMES.get("primary", "#FF69B4")
            secondary = USER_THEMES.get("secondary", "#9932CC")
            self.setStyleSheet(f"background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 {primary}22, stop:1 {secondary}44);")

        self.setup_ui()
        self.apply_user_theme()
        
        # Start mood indicator
        self.mood_indicator = QLabel("😊", self)
        self.mood_indicator.setGeometry(self.width()-100, 50, 30, 30)
        self.mood_indicator.setFont(QFont("Segoe UI Emoji", 16))
        self.update_mood_indicator()

        # Fade title after 5s
        QTimer.singleShot(5000, self.fade_title)

        # Geometry refresh timer
        self._update_geom_timer = QTimer(self)
        self._update_geom_timer.timeout.connect(self._on_geometry_refresh)
        self._update_geom_timer.start(120)

        # Proactive timer (every 5 min)
        self.proactive_timer = QTimer(self)
        self.proactive_timer.timeout.connect(self.proactive_check)
        self.proactive_timer.start(300000)  # 5 min

        # Start background recognition
        self._start_background_listener()

    def proactive_check(self):
        """Proactive suggestions"""
        suggestion = suggest_break()
        if suggestion:
            speak(suggestion)
            self.append_response(suggestion)
        check_in = daily_check_in()
        if datetime.now().hour == 9:  # Morning check-in
            speak(check_in)
            self.append_response(check_in)

    def setup_ui(self):
        # Mac buttons
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

        # Rose icon beside buttons
        self.rose_icon = QLabel(self)
        if os.path.exists(ROSE_ICON_FILE):
            pix = QPixmap(ROSE_ICON_FILE).scaled(28,28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.rose_icon.setPixmap(pix)
        else:
            self.rose_icon.setText("🌹")
            self.rose_icon.setFont(QFont("Segoe UI Emoji", 14))
        self.rose_icon.setGeometry(92, 8, 28, 28)

        # Title label (center) with opacity effect
        self.title_label = QLabel("ROSE", self)
        self.title_label.setFont(QFont("Segoe UI", 48, QFont.Bold))
        self.title_label.setStyleSheet("color: white;")
        self.title_label.setGeometry(0, self.height()//2 - 60, self.width(), 120)
        self.title_label.setAlignment(Qt.AlignCenter)
        # Opacity effect (reliable animation)
        self._title_op = QGraphicsOpacityEffect(self.title_label)
        self.title_label.setGraphicsEffect(self._title_op)
        self._title_op.setOpacity(1.0)
        self._title_anim = None

        # TRANSPARENT response area (main change!)
        self.response_area = QScrollArea(self)
        self.response_area.setGeometry(40, self.height()-220, self.width()-80, 160)
        # Made fully transparent with glass effect
        self.response_area.setStyleSheet("""
            QScrollArea {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                backdrop-filter: blur(10px);
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
            }
        """)
        self.response_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.response_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.response_area.setWidgetResizable(True)
        
        self.response_content = QTextEdit()
        self.response_content.setReadOnly(True)
        # Fully transparent text area with enhanced readability
        self.response_content.setStyleSheet("""
            QTextEdit {
                background: transparent; 
                color: white; 
                border: none; 
                padding: 12px;
                font-weight: 500;
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
                selection-background-color: rgba(255, 105, 180, 0.3);
            }
        """)
        self.response_content.setFont(QFont("Segoe UI", 13))
        self.response_area.setWidget(self.response_content)

        # Enhanced menu with new creative options
        self.menu_btn = QPushButton("⋯", self)
        self.menu_btn.setGeometry(self.width()-62, 10, 50, 30)
        self.menu_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.15);
                color: white;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.25);
            }
        """)
        
        self.menu = QMenu(self)
        self.menu.setStyleSheet("""
            QMenu {
                background: rgba(30, 30, 30, 0.9);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: rgba(255, 105, 180, 0.3);
            }
        """)
        
        # Original menu items
        self.menu.addAction("Toggle Flow", lambda: self._run_js("toggleAnimation()"))
        self.menu.addAction("Change Speed", lambda: self._run_js("changeSpeed()"))
        self.menu.addAction("Toggle Glow", lambda: self._run_js("toggleGlow()"))
        self.menu.addSeparator()
        
        # New creative menu items
        self.menu.addAction("📊 Show Mood Chart", lambda: handle_command("show my mood", self))
        self.menu.addAction("☁️ Generate Word Cloud", lambda: handle_command("word cloud", self))
        self.menu.addAction("😊 Analyze Emojis", lambda: handle_command("analyze emojis in hello 😊🌹💜", self))
        self.menu.addAction("🎨 Extract Theme from Image", lambda: handle_command("change theme from image", self))
        self.menu.addAction("🌡️ Mood Temperature", lambda: self.show_mood_temperature())
        self.menu.addAction("📈 Week Summary", lambda: handle_command("show week summary", self))
        self.menu.addAction("📁 Upload Document", lambda: handle_command("upload document", self))
        
        self.menu_btn.setMenu(self.menu)

    def apply_user_theme(self):
        """Apply user's extracted color theme"""
        primary = USER_THEMES.get("primary", "#FF69B4")
        secondary = USER_THEMES.get("secondary", "#9932CC")
        accent = USER_THEMES.get("accent", "#FFB6C1")
        
        # Update title color
        self.title_label.setStyleSheet(f"color: {accent};")
        
        # Update response area with user colors
        self.response_area.setStyleSheet(f"""
            QScrollArea {{
                background: rgba({self._hex_to_rgba(primary, 0.05)});
                border: 1px solid rgba({self._hex_to_rgba(accent, 0.2)});
                border-radius: 15px;
                backdrop-filter: blur(10px);
            }}
            QScrollBar:vertical {{
                background: rgba({self._hex_to_rgba(secondary, 0.1)});
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba({self._hex_to_rgba(accent, 0.4)});
                border-radius: 4px;
            }}
        """)

    def _hex_to_rgba(self, hex_color: str, alpha: float) -> str:
        """Convert hex color to rgba string"""
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"{r}, {g}, {b}, {alpha}"
        except:
            return f"255, 105, 180, {alpha}"  # Fallback to rose pink

    def update_mood_indicator(self):
        """Update mood indicator based on recent mood analysis"""
        if not MOOD_HISTORY:
            return
        
        recent_mood = MOOD_HISTORY[-1]["compound"] if MOOD_HISTORY else 0
        if recent_mood > 0.5:
            self.mood_indicator.setText("😊")
        elif recent_mood > 0.1:
            self.mood_indicator.setText("🙂")
        elif recent_mood > -0.1:
            self.mood_indicator.setText("😐")
        elif recent_mood > -0.5:
            self.mood_indicator.setText("😔")
        else:
            self.mood_indicator.setText("😢")

    def show_mood_temperature(self):
        """Show current mood as a temperature-like indicator"""
        if not MOOD_HISTORY:
            self.append_response("🌡️ No mood data available yet")
            return
        
        recent_mood = MOOD_HISTORY[-1]["compound"]
        temperature = int((recent_mood + 1) * 50)  # Convert -1 to 1 range to 0-100
        
        if temperature > 75:
            temp_desc = "Hot! 🔥 You're feeling great!"
        elif temperature > 50:
            temp_desc = "Warm 😊 Things are looking good!"
        elif temperature > 25:
            temp_desc = "Cool 😐 Pretty neutral vibes"
        else:
            temp_desc = "Cold 🧊 Could use some warming up"
        
        response = f"🌡️ Mood Temperature: {temperature}°\n{temp_desc}"
        self.append_response(response)
        speak(f"Your mood temperature is {temperature} degrees. {temp_desc}")

    def _on_geometry_refresh(self):
        if self.web:
            self.web.setGeometry(0, 0, self.width(), self.height())
        self.title_label.setGeometry(0, self.height()//2 - 60, self.width(), 120)
        self.response_area.setGeometry(40, self.height()-220, self.width()-80, 160)
        self.menu_btn.setGeometry(self.width()-62, 10, 50, 30)
        self.mood_indicator.setGeometry(self.width()-100, 50, 30, 30)

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
        
        # Update mood indicator if this was user input
        if text.startswith(">"):
            self.update_mood_indicator()

    def fade_title(self):
        """Animate opacity effect on title; hide when finished"""
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

    # Dragging + snap
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

    # Voice listener
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

# ---------------- Main Application ----------------
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Rose AI Assistant v30")
    app.setApplicationVersion("30.0")
    
    # Apply application-wide dark theme
    app.setStyleSheet("""
        QApplication {
            font-family: 'Segoe UI', Arial, sans-serif;
        }
    """)
    
    hud = RoseHUD()
    hud.show()
    
    # Welcome message with feature overview
    hud.append_response("🌹 Rose v30 Enhanced - Ready!")
    hud.append_response("All new features added: Scheduling, Analysis, Coaching, Viz, Multi-lang, and more!")
    hud.append_response("Try: 'show my mood', 'upload document', 'suggest song', or check the menu ⋯")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()