"""
Rose AI Assistant Media Services Module
Handles all media-related functionality including music, TTS, and visualizations
"""

import asyncio
import threading
import time
import webbrowser
import subprocess
import platform
import os
import random
from typing import Optional, List, Dict, Any
from datetime import datetime

from config import config_manager
from error_handler import error_handler_instance, FeatureNotAvailableError

class TTSService:
    """Handles text-to-speech functionality"""
    
    def __init__(self):
        self.edge_tts = None
        self.tts_playing = False
        self.tts_lock = threading.Lock()
        self._initialize_tts()
    
    def _initialize_tts(self):
        """Initialize TTS service"""
        try:
            import edge_tts  # pyright: ignore[reportMissingImports]
            self.edge_tts = edge_tts
            error_handler_instance.log_info("Edge TTS initialized")
        except ImportError:
            error_handler_instance.log_warning("Edge TTS not available - TTS disabled")
    
    def is_available(self) -> bool:
        """Check if TTS is available"""
        return self.edge_tts is not None
    
    def _estimate_tts_duration(self, text: str) -> float:
        """Estimate TTS duration in seconds"""
        words = len(text.split())
        return max(0.6, words / 2.8)
    
    def _play_file_default(self, path: str):
        """Play audio file using system default player"""
        try:
            if platform.system() == "Windows":
                subprocess.Popen(["start", path], shell=True)
            elif platform.system() == "Darwin":
                subprocess.Popen(["afplay", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            error_handler_instance.handle_error(e, "Audio playback")
    
    async def _generate_tts(self, text: str, filename: str = "speech.mp3", voice: str = "en-US-JennyNeural"):
        """Generate TTS audio file"""
        if not self.edge_tts:
            raise FeatureNotAvailableError("Edge TTS not available")
        
        comm = self.edge_tts.Communicate(text, voice)
        await comm.save(filename)
    
    def speak(self, text: str, language: Optional[str] = None) -> None:
        """Generate and play TTS in background"""
        if not self.is_available():
            print(f"[TTS fallback] {text}")
            return
        
        if language is None:
            language = config_manager.config.ui.language
        
        # Get appropriate voice for language
        from ai_services import language_processor
        voice = language_processor.get_voice_for_language(language)
        
        def _runner():
            with self.tts_lock:
                self.tts_playing = True
            
            try:
                asyncio.run(self._generate_tts(text, "speech.mp3", voice))
                self._play_file_default("speech.mp3")
            except Exception as e:
                error_handler_instance.handle_error(e, "TTS generation")
            finally:
                time.sleep(self._estimate_tts_duration(text) + 0.35)
                with self.tts_lock:
                    self.tts_playing = False
        
        threading.Thread(target=_runner, daemon=True).start()
    
    def is_playing(self) -> bool:
        """Check if TTS is currently playing"""
        return self.tts_playing

class MusicService:
    """Handles music integration and playback"""
    
    def __init__(self):
        self.pytube_search = None
        self.music_taste = []
        self._initialize_music_services()
    
    def _initialize_music_services(self):
        """Initialize music services"""
        try:
            from pytube import Search  # pyright: ignore[reportMissingImports]
            self.pytube_search = Search
            error_handler_instance.log_info("Pytube initialized")
        except ImportError:
            error_handler_instance.log_warning("Pytube not available - YouTube search limited")
    
    def play_youtube_song(self, song: str) -> None:
        """Play song on YouTube"""
        song = (song or "").strip()
        if not song:
            webbrowser.open("https://www.youtube.com")
            return
        
        try:
            if self.pytube_search:
                search = self.pytube_search(song)
                if hasattr(search, "results") and search.results:
                    first_result = search.results[0]
                    url = getattr(first_result, "watch_url", None) or f"https://www.youtube.com/watch?v={first_result.video_id}"
                    webbrowser.open(url)
                    return
        except Exception as e:
            error_handler_instance.handle_error(e, "YouTube search")
        
        # Fallback to search page
        webbrowser.open(f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}")
    
    def play_apple_music(self, song: str) -> None:
        """Search Apple Music"""
        webbrowser.open(f"music://music.apple.com/search?term={song.replace(' ', '+')}")
    
    def play_soundcloud(self, song: str) -> None:
        """Search SoundCloud"""
        webbrowser.open(f"https://soundcloud.com/search?q={song.replace(' ', '+')}")
    
    def add_to_taste(self, song: str) -> None:
        """Add song to music taste"""
        if song and song not in self.music_taste:
            self.music_taste.append(song)
            # Keep only last 50 songs
            if len(self.music_taste) > 50:
                self.music_taste.pop(0)
    
    def suggest_song(self) -> str:
        """Suggest song based on taste"""
        if self.music_taste:
            base = random.choice(self.music_taste)
            return f"How about something like {base}?"
        return "Tell me your favorite songs to learn your taste."
    
    def create_mood_playlist(self, mood: float) -> str:
        """Create mood-based playlist suggestion"""
        if mood > 0.3:
            return "Upbeat playlist: Happy songs on YouTube."
        elif mood < -0.3:
            return "Calming playlist: Relaxing music."
        else:
            return "Balanced playlist: Mixed mood songs."

class SpotifyService:
    """Handles Spotify integration"""
    
    def __init__(self):
        self.is_available = self._check_spotify_availability()
    
    def _check_spotify_availability(self) -> bool:
        """Check if Spotify is available"""
        try:
            if platform.system() == "Windows":
                # Check if Spotify is running
                result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Spotify.exe"], 
                                      capture_output=True, text=True)
                return "Spotify.exe" in result.stdout
            elif platform.system() == "Darwin":
                # Check if Spotify is running on macOS
                result = subprocess.run(["pgrep", "-f", "Spotify"], capture_output=True)
                return result.returncode == 0
            else:
                # Linux - check if playerctl is available
                result = subprocess.run(["which", "playerctl"], capture_output=True)
                return result.returncode == 0
        except Exception:
            return False
    
    def _send_media_key_windows(self, vk_code: int) -> None:
        """Send media key on Windows"""
        try:
            import ctypes
            from ctypes import wintypes
            
            user32 = ctypes.WinDLL('user32', use_last_error=True)
            INPUT_KEYBOARD = 1
            KEYEVENTF_EXTENDEDKEY = 0x0001
            KEYEVENTF_KEYUP = 0x0002
            
            class KEYBDINPUT(ctypes.Structure):
                _fields_ = (("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                           ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                           ("dwExtraInfo", wintypes.ULONG_PTR))
            
            class INPUT(ctypes.Structure):
                _fields_ = (("type", wintypes.DWORD), ("ki", KEYBDINPUT))
            
            # Key down
            ki = KEYBDINPUT(wVk=vk_code, wScan=0, dwFlags=KEYEVENTF_EXTENDEDKEY, time=0, dwExtraInfo=0)
            x = INPUT(type=INPUT_KEYBOARD, ki=ki)
            user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))
            
            # Key up
            ki_up = KEYBDINPUT(wVk=vk_code, wScan=0, dwFlags=KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, time=0, dwExtraInfo=0)
            x_up = INPUT(type=INPUT_KEYBOARD, ki=ki_up)
            user32.SendInput(1, ctypes.byref(x_up), ctypes.sizeof(x_up))
            
        except Exception as e:
            error_handler_instance.handle_error(e, "Windows media key")
    
    def play_pause(self) -> None:
        """Toggle play/pause"""
        if not self.is_available():
            raise FeatureNotAvailableError("Spotify not available")
        
        try:
            if platform.system() == "Windows":
                self._send_media_key_windows(0xB3)  # VK_MEDIA_PLAY_PAUSE
            elif platform.system() == "Darwin":
                subprocess.Popen(["osascript", "-e", 'tell application "Spotify" to playpause'])
            else:
                subprocess.run(["playerctl", "play-pause"])
        except Exception as e:
            error_handler_instance.handle_error(e, "Spotify play/pause")
    
    def next_track(self) -> None:
        """Next track"""
        if not self.is_available():
            raise FeatureNotAvailableError("Spotify not available")
        
        try:
            if platform.system() == "Windows":
                self._send_media_key_windows(0xB0)  # VK_MEDIA_NEXT_TRACK
            elif platform.system() == "Darwin":
                subprocess.Popen(["osascript", "-e", 'tell application "Spotify" to next track'])
            else:
                subprocess.run(["playerctl", "next"])
        except Exception as e:
            error_handler_instance.handle_error(e, "Spotify next track")
    
    def previous_track(self) -> None:
        """Previous track"""
        if not self.is_available():
            raise FeatureNotAvailableError("Spotify not available")
        
        try:
            if platform.system() == "Windows":
                self._send_media_key_windows(0xB1)  # VK_MEDIA_PREV_TRACK
            elif platform.system() == "Darwin":
                subprocess.Popen(["osascript", "-e", 'tell application "Spotify" to previous track'])
            else:
                subprocess.run(["playerctl", "previous"])
        except Exception as e:
            error_handler_instance.handle_error(e, "Spotify previous track")

class VolumeService:
    """Handles system volume control"""
    
    def adjust_volume(self, command: str) -> None:
        """Adjust system volume"""
        try:
            if platform.system() == "Windows":
                if "up" in command:
                    subprocess.run(["nircmd.exe", "changesysvolume", "5000"])
                elif "down" in command:
                    subprocess.run(["nircmd.exe", "changesysvolume", "-5000"])
                elif "mute" in command:
                    subprocess.run(["nircmd.exe", "mutesysvolume", "1"])
                elif "unmute" in command:
                    subprocess.run(["nircmd.exe", "mutesysvolume", "0"])
            elif platform.system() == "Darwin":
                if "up" in command:
                    subprocess.run(["osascript", "-e", "set volume output volume (output volume of (get volume settings) + 10)"])
                elif "down" in command:
                    subprocess.run(["osascript", "-e", "set volume output volume (output volume of (get volume settings) - 10)"])
            else:  # Linux
                if "up" in command:
                    subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "5%+"])
                elif "down" in command:
                    subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "5%-"])
        except Exception as e:
            error_handler_instance.handle_error(e, "Volume control")
    
    def smart_adjust(self) -> Optional[str]:
        """Smart volume adjustment based on time"""
        hour = datetime.now().hour
        if 22 < hour or hour < 7:  # Night time
            self.adjust_volume("down")
            return "Lowering volume for night time."
        return None

# Global service instances
tts_service = TTSService()
music_service = MusicService()
spotify_service = SpotifyService()
volume_service = VolumeService()
