"""
Rose AI Assistant v30 - Refactored Version
Enhanced with modular architecture, better error handling, and improved features
"""

import sys
import os
import time
import threading
import webbrowser
import platform
import subprocess
import json
from typing import Optional
from datetime import datetime

# Import our new modules
from config import config_manager
from error_handler import error_handler_instance, error_handler
from help_system import help_system, CommandCategory
from ai_services import gemini_service, mood_analyzer, language_processor
from media_services import tts_service, music_service, spotify_service, volume_service
from voice_commands import voice_command_manager
from theme_manager import theme_manager
from plugin_system import plugin_manager
from fast_tts import fast_tts
from performance_optimizer import performance_optimizer

# PySide6 imports
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QRect  # pyright: ignore[reportMissingImports]
from PySide6.QtWidgets import (  # pyright: ignore[reportMissingImports]
    QApplication, QWidget, QLabel, QPushButton, QMenu, QScrollArea, QTextEdit,
    QGraphicsOpacityEffect, QVBoxLayout, QHBoxLayout, QProgressBar, QFileDialog
)
from PySide6.QtGui import QFont, QPixmap, QCloseEvent, QColor  # pyright: ignore[reportMissingImports]

# Optional imports with graceful fallbacks
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView  # pyright: ignore[reportMissingImports]
    USE_WEBENGINE = True
except ImportError:
    QWebEngineView = None
    USE_WEBENGINE = False
    print("⚠️ WebEngine not available - HTML background disabled")

try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    sr = None
    SPEECH_AVAILABLE = False
    error_handler_instance.log_warning("Speech recognition not available")

# Global state
LISTENING = True
BG_LISTENER_STOP = None

class RoseHUD(QWidget):
    """Enhanced Rose HUD with improved architecture"""
    
    SNAP_MARGIN = 30
    SNAP_ANIM_MS = 240

    def __init__(self):
        super().__init__()
        self.setup_window()
        self.setup_ui()
        self.setup_timers()
        self.start_services()
        
        # Initialize voice commands
        self._setup_voice_commands()
        
        # Load plugins
        plugin_count = plugin_manager.load_plugins()
        if plugin_count > 0:
            print(f"✅ Loaded {plugin_count} plugins")
        
        # Run performance optimization
        performance_optimizer.run_full_optimization()
        
        # Welcome message
        self.append_response("🌹 Rose v30 Enhanced - Ready!")
        self.append_response("Say 'help' to see all available commands")
        self.append_response("Try: 'show my mood', 'play music', or 'what can you do'")

    def setup_window(self):
        """Setup window properties"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(
            config_manager.config.ui.window_width,
            config_manager.config.ui.window_height
        )
        self._drag_offset = None
        self._is_max = False
        
        # Setup background
        self.setup_background()
        
        # Apply current theme
        self.apply_theme()

    def setup_background(self):
        """Setup animated background"""
        if USE_WEBENGINE and os.path.exists("gradient_circle_design.html"):
            self.web = QWebEngineView(self)
            with open("gradient_circle_design.html", "r", encoding="utf-8") as f:
                html_content = f.read()
            self.web.setHtml(html_content)
            self.web.setGeometry(0, 0, self.width(), self.height())
            self.web.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        else:
            self.web = None
            # Fallback gradient background
            primary = config_manager.config.ui.primary_color
            secondary = config_manager.config.ui.secondary_color
            self.setStyleSheet(f"""
                QWidget {{
                    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, 
                        stop:0 {primary}22, 
                        stop:0.5 {secondary}44, 
                        stop:1 {primary}22);
                }}
            """)

    def setup_ui(self):
        """Setup user interface"""
        self.setup_controls()
        self.setup_title()
        self.setup_response_area()
        self.setup_menu()
        self.apply_theme()

    def setup_controls(self):
        """Setup window controls"""
        # Close button
        self.close_btn = QPushButton("×", self)
        self.close_btn.setGeometry(12, 12, 20, 20)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: #FF5C5C;
                border-radius: 10px;
                border: none;
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #FF4444;
            }
            QPushButton:pressed {
                background: #CC3333;
            }
        """)
        self.close_btn.clicked.connect(self.close_application)

        # Minimize button
        self.min_btn = QPushButton("−", self)
        self.min_btn.setGeometry(40, 12, 20, 20)
        self.min_btn.setStyleSheet("""
            QPushButton {
                background: #FFBD44;
                border-radius: 10px;
                border: none;
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #FFAA22;
            }
            QPushButton:pressed {
                background: #DD8800;
            }
        """)
        self.min_btn.clicked.connect(self.minimize_animated)

        # Maximize button
        self.max_btn = QPushButton("□", self)
        self.max_btn.setGeometry(68, 12, 20, 20)
        self.max_btn.setStyleSheet("""
            QPushButton {
                background: #28C840;
                border-radius: 10px;
                border: none;
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #22AA33;
            }
            QPushButton:pressed {
                background: #1A8822;
            }
        """)
        self.max_btn.clicked.connect(self.toggle_max_restore)

        # Rose icon
        self.rose_icon = QLabel(self)
        self.rose_icon.setText("🌹")
        self.rose_icon.setFont(QFont("Segoe UI Emoji", 14))
        self.rose_icon.setGeometry(92, 8, 28, 28)

    def setup_title(self):
        """Setup title with animation"""
        self.title_label = QLabel("ROSE", self)
        self.title_label.setFont(QFont("Segoe UI", 48, QFont.Bold))
        self.title_label.setStyleSheet("color: white;")
        self.title_label.setGeometry(0, self.height()//2 - 60, self.width(), 120)
        self.title_label.setAlignment(Qt.AlignCenter)
        
        # Opacity effect for animation
        self._title_op = QGraphicsOpacityEffect(self.title_label)
        self.title_label.setGraphicsEffect(self._title_op)
        self._title_op.setOpacity(1.0)
        self._title_anim = None

    def setup_response_area(self):
        """Setup response display area"""
        self.response_area = QScrollArea(self)
        self.response_area.setGeometry(40, self.height()-220, self.width()-80, 160)
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

    def setup_menu(self):
        """Setup context menu"""
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
        
        # Add menu items
        self.setup_menu_items()
        self.menu_btn.setMenu(self.menu)

    def setup_menu_items(self):
        """Setup menu items"""
        # Help and Info
        self.menu.addAction("❓ Help", lambda: self.handle_command("help"))
        self.menu.addAction("📋 Commands", lambda: self.handle_command("commands"))
        self.menu.addAction("🔧 Setup Guide", lambda: self.handle_command("setup guide"))
        self.menu.addSeparator()
        
        # Mood and Wellness
        self.menu.addAction("😊 Show Mood", lambda: self.handle_command("show my mood"))
        self.menu.addAction("🌡️ Mood Temperature", lambda: self.handle_command("mood temperature"))
        self.menu.addAction("📊 Week Summary", lambda: self.handle_command("show week summary"))
        self.menu.addSeparator()
        
        # Media
        self.menu.addAction("🎵 Play Music", lambda: self.handle_command("play music on youtube"))
        self.menu.addAction("🎧 Spotify Controls", lambda: self.handle_command("spotify play"))
        self.menu.addAction("🔊 Volume Control", lambda: self.handle_command("volume up"))
        self.menu.addSeparator()
        
        # Productivity
        self.menu.addAction("📝 Add Reminder", lambda: self.handle_command("remind me to"))
        self.menu.addAction("📅 Export Calendar", lambda: self.handle_command("export calendar"))
        self.menu.addAction("⏱️ Time Tracking", lambda: self.handle_command("start tracking"))
        self.menu.addSeparator()
        
        # Creative
        self.menu.addAction("☁️ Word Cloud", lambda: self.handle_command("word cloud"))
        self.menu.addAction("🎨 Theme from Image", lambda: self.handle_command("change theme from image"))
        self.menu.addAction("📁 Upload Document", lambda: self.handle_command("upload document"))
        self.menu.addSeparator()
        
        # Themes
        self.menu.addAction("🌌 Cosmic Theme", lambda: self.switch_theme("cosmic"))
        self.menu.addAction("🌙 Dark Theme", lambda: self.switch_theme("dark"))
        self.menu.addAction("☀️ Light Theme", lambda: self.switch_theme("light"))
        self.menu.addAction("⚡ Neon Theme", lambda: self.switch_theme("neon"))
        self.menu.addAction("🎯 Minimal Theme", lambda: self.switch_theme("minimal"))
        self.menu.addAction("🌊 Ocean Theme", lambda: self.switch_theme("ocean"))
        self.menu.addSeparator()
        
        # Feature Toggles
        self.menu.addAction("🎤 Toggle Voice", self.toggle_voice_feature)
        self.menu.addAction("😊 Toggle Mood Tracking", self.toggle_mood_feature)
        self.menu.addAction("🎵 Toggle Music", self.toggle_music_feature)
        self.menu.addAction("🔊 Toggle TTS", self.toggle_tts_feature)

    def setup_timers(self):
        """Setup timers for animations and proactive features"""
        # Fade title after 5s
        QTimer.singleShot(5000, self.fade_title)
        
        # Geometry refresh timer
        self._update_geom_timer = QTimer(self)
        self._update_geom_timer.timeout.connect(self._on_geometry_refresh)
        self._update_geom_timer.start(120)
        
        # Proactive timer
        self.proactive_timer = QTimer(self)
        self.proactive_timer.timeout.connect(self.proactive_check)
        self.proactive_timer.start(config_manager.config.features.proactive_check_interval * 1000)

    def _setup_voice_commands(self):
        """Setup voice command handlers"""
        # Connect voice command handlers to actual methods
        voice_command_manager._handle_system_command = self.close_application
        voice_command_manager._handle_minimize = self.minimize_animated
        voice_command_manager._handle_maximize = self.toggle_max_restore
        voice_command_manager._handle_play_music = lambda text: self.handle_command("play music")
        voice_command_manager._handle_stop_music = lambda text: self.handle_command("stop music")
        voice_command_manager._handle_volume_up = lambda text: self.handle_command("volume up")
        voice_command_manager._handle_volume_down = lambda text: self.handle_command("volume down")
        
        # Add custom commands
        voice_command_manager.add_custom_command(
            "change theme|switch theme|new theme",
            self._handle_theme_change,
            "Change the UI theme",
            category="ui"
        )
        
        voice_command_manager.add_custom_command(
            "fast response|quick response|speed up",
            self._handle_speed_up,
            "Enable fast response mode",
            category="system"
        )
    
    def _handle_theme_change(self, text: str):
        """Handle theme change command"""
        themes = theme_manager.get_available_themes()
        if "cosmic" in text.lower():
            self.switch_theme("cosmic")
        elif "dark" in text.lower():
            self.switch_theme("dark")
        elif "light" in text.lower():
            self.switch_theme("light")
        elif "neon" in text.lower():
            self.switch_theme("neon")
        elif "minimal" in text.lower():
            self.switch_theme("minimal")
        elif "ocean" in text.lower():
            self.switch_theme("ocean")
        else:
            # Cycle through themes
            current_theme = theme_manager.current_theme.name.lower()
            current_index = themes.index(current_theme) if current_theme in themes else 0
            next_index = (current_index + 1) % len(themes)
            self.switch_theme(themes[next_index])
    
    def _handle_speed_up(self, text: str):
        """Handle speed up command"""
        self.append_response("🚀 Fast response mode enabled!")
        # Enable fast TTS and reduce delays
        fast_tts.set_rate("+50%")
        self.append_response("TTS speed increased, response time optimized!")
    
    def apply_theme(self):
        """Apply current theme to the UI"""
        theme = theme_manager.get_theme()
        if theme:
            # Apply theme stylesheet
            self.setStyleSheet(theme_manager.get_theme_stylesheet())
            
            # Update button styles
            if hasattr(self, 'close_btn'):
                self.close_btn.setStyleSheet(theme_manager.get_button_styles("close"))
            if hasattr(self, 'min_btn'):
                self.min_btn.setStyleSheet(theme_manager.get_button_styles("minimize"))
            if hasattr(self, 'max_btn'):
                self.max_btn.setStyleSheet(theme_manager.get_button_styles("maximize"))
    
    def switch_theme(self, theme_name: str):
        """Switch to a different theme"""
        if theme_manager.set_theme(theme_name):
            self.apply_theme()
            self.append_response(f"🎨 Switched to {theme_name} theme!")
            fast_tts.speak(f"Switched to {theme_name} theme")
        else:
            self.append_response(f"❌ Theme '{theme_name}' not found")
    
    def start_services(self):
        """Start background services"""
        if config_manager.config.features.enable_voice and SPEECH_AVAILABLE:
            self._start_background_listener()

    def _hex_to_rgba(self, hex_color: str, alpha: float) -> str:
        """Convert hex color to rgba string"""
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"{r}, {g}, {b}, {alpha}"
        except:
            return f"255, 105, 180, {alpha}"

    def handle_command(self, cmd: str) -> None:
        """Handle voice/text commands with improved error handling"""
        if not cmd:
            return
        
        cmd_norm = cmd.lower().strip()
        error_handler_instance.log_info(f"Processing command: {cmd_norm}")
        
        # Add to response area
        self.append_response(f"> {cmd_norm}")
        
        # Handle help commands first
        if self._handle_help_commands(cmd_norm):
            return
        
        # Analyze mood if enabled
        if config_manager.config.features.enable_mood_tracking:
            mood_data = mood_analyzer.analyze_mood(cmd)
            if mood_data:
                self._update_mood_display()
        
        # Handle specific command categories
        if self._handle_voice_commands(cmd_norm):
            return
        elif self._handle_mood_commands(cmd_norm):
            return
        elif self._handle_media_commands(cmd_norm):
            return
        elif self._handle_productivity_commands(cmd_norm):
            return
        elif self._handle_system_commands(cmd_norm):
            return
        elif self._handle_creative_commands(cmd_norm):
            return
        else:
            # Fallback to AI response
            self._handle_ai_response(cmd_norm)

    def _handle_help_commands(self, cmd_norm: str) -> bool:
        """Handle help-related commands"""
        if cmd_norm in ["help", "what can you do"]:
            response = help_system.get_help()
            self.append_response(response)
            tts_service.speak("Here's what I can help you with")
            return True
        
        elif cmd_norm == "commands":
            response = help_system.get_commands()
            self.append_response(response)
            tts_service.speak("Here are all available commands")
            return True
        
        elif cmd_norm == "setup guide":
            response = help_system.get_setup_guide()
            self.append_response(response)
            tts_service.speak("Here's the setup guide")
            return True
        
        elif cmd_norm.startswith("help "):
            category_name = cmd_norm[5:].strip()
            # Find matching category
            for category in CommandCategory:
                if category_name.lower() in category.value.lower():
                    response = help_system.get_help(category)
                    self.append_response(response)
                    tts_service.speak(f"Here's help for {category.value}")
                    return True
        
        return False

    def _handle_voice_commands(self, cmd_norm: str) -> bool:
        """Handle voice and speech commands using the new voice command system"""
        # First try the new voice command system
        if voice_command_manager.process_voice_input(cmd_norm):
            return True
        
        # Fallback to old system for complex commands
        if any(g in cmd_norm for g in ["hello", "hi", "hey"]):
            greeting = "Hello! I'm Rose, your AI assistant."
            if mood_analyzer.mood_history:
                recent_mood = mood_analyzer.get_current_mood()
                if recent_mood and recent_mood["compound"] > 0.3:
                    greeting += " You seem happy today! 😊"
                elif recent_mood and recent_mood["compound"] < -0.3:
                    greeting += " I'm here if you need support 💜"
            
            self.append_response(greeting)
            fast_tts.speak(greeting)
            return True
        
        elif "speak in" in cmd_norm:
            language = cmd_norm.split("speak in")[-1].strip()[:2]
            if language_processor.set_language(language):
                response = f"Switching to {language_processor.get_language_name(language)}"
                self.append_response(response)
                fast_tts.speak(response, language)
                return True
        
        elif "set personality" in cmd_norm:
            personality = cmd_norm.split("set personality")[-1].strip()
            config_manager.config.ui.personality = personality
            config_manager.save_config()
            response = f"Personality set to {personality}"
            self.append_response(response)
            tts_service.speak(response)
            return True
        
        return False

    def _handle_mood_commands(self, cmd_norm: str) -> bool:
        """Handle mood and wellness commands"""
        if "show my mood" in cmd_norm or "mood chart" in cmd_norm:
            if mood_analyzer.mood_history:
                response = "Here's your mood journey with me"
                self.append_response(response)
                tts_service.speak(response)
                # TODO: Show mood visualization
            else:
                response = "I need more conversation data to show your mood chart"
                self.append_response(response)
                tts_service.speak(response)
            return True
        
        elif "mood temperature" in cmd_norm:
            if mood_analyzer.mood_history:
                recent_mood = mood_analyzer.get_current_mood()
                if recent_mood:
                    temperature = int((recent_mood["compound"] + 1) * 50)
                    response = f"🌡️ Mood Temperature: {temperature}°"
                    self.append_response(response)
                    tts_service.speak(f"Your mood temperature is {temperature} degrees")
            else:
                response = "🌡️ No mood data available yet"
                self.append_response(response)
                tts_service.speak(response)
            return True
        
        return False

    def _handle_media_commands(self, cmd_norm: str) -> bool:
        """Handle media and music commands"""
        if "play music" in cmd_norm or ("play" in cmd_norm and "youtube" in cmd_norm):
            if "youtube" in cmd_norm:
                song = cmd_norm.replace("play", "").replace("on youtube", "").replace("youtube", "").strip()
            else:
                song = cmd_norm.replace("play music", "").strip()
                if not song:
                    song = "music"
            
            try:
                music_service.play_youtube_song(song)
                response = f"Playing {song} on YouTube"
                self.append_response(response)
                tts_service.speak(response)
            except Exception as e:
                response = f"Opening YouTube to play {song}"
                self.append_response(response)
                tts_service.speak(response)
            return True
        
        elif "spotify" in cmd_norm:
            if "play" in cmd_norm or "pause" in cmd_norm:
                try:
                    spotify_service.play_pause()
                    response = "Toggling Spotify"
                    self.append_response(response)
                    tts_service.speak(response)
                except Exception as e:
                    response = error_handler_instance.handle_error(e, "Spotify control")
                    self.append_response(response)
            return True
        
        elif any(x in cmd_norm for x in ["volume up", "increase volume"]):
            volume_service.adjust_volume("up")
            response = "Volume increased"
            self.append_response(response)
            tts_service.speak(response)
            return True
        
        elif any(x in cmd_norm for x in ["volume down", "decrease volume"]):
            volume_service.adjust_volume("down")
            response = "Volume decreased"
            self.append_response(response)
            tts_service.speak(response)
            return True
        
        return False

    def _handle_productivity_commands(self, cmd_norm: str) -> bool:
        """Handle productivity commands"""
        if "remind me to" in cmd_norm:
            task = cmd_norm.split("remind me to", 1)[1].strip()
            # TODO: Implement reminder system
            response = f"Reminder added: {task}"
            self.append_response(response)
            tts_service.speak(response)
            return True
        
        return False

    def _handle_system_commands(self, cmd_norm: str) -> bool:
        """Handle system control commands"""
        if "open browser" in cmd_norm or "open brave" in cmd_norm or "open chrome" in cmd_norm:
            webbrowser.open("https://www.google.com")
            response = "Opening browser"
            self.append_response(response)
            tts_service.speak(response)
            return True
        
        return False

    def _handle_creative_commands(self, cmd_norm: str) -> bool:
        """Handle creative feature commands"""
        if "word cloud" in cmd_norm:
            response = "Generating word cloud from our conversations"
            self.append_response(response)
            tts_service.speak(response)
            # TODO: Implement word cloud generation
            return True
        
        return False

    def _handle_ai_response(self, cmd_norm: str) -> None:
        """Handle AI response for unrecognized commands"""
        try:
            if gemini_service.is_available():
                system_instruction = f"You are Rose, a helpful AI assistant. Personality: {config_manager.config.ui.personality}"
                response = gemini_service.call_with_context(
                    cmd_norm, 
                    system_instruction,
                    config_manager.config.ui.language
                )
                self.append_response(response)
                tts_service.speak(response)
            else:
                response = f"I heard: {cmd_norm}. To use AI features, please configure your Gemini API key."
                self.append_response(response)
                tts_service.speak(response)
        except Exception as e:
            response = error_handler_instance.handle_error(e, "AI response")
            self.append_response(response)

    def _update_mood_display(self):
        """Update mood display indicator"""
        # TODO: Implement mood indicator update
        pass

    def toggle_voice_feature(self):
        """Toggle voice recognition feature"""
        current_state = config_manager.toggle_feature("voice")
        status = "enabled" if current_state else "disabled"
        response = f"Voice recognition {status}"
        self.append_response(response)
        tts_service.speak(response)
        
        # Restart voice recognition if enabled
        if current_state and SPEECH_AVAILABLE:
            self._start_background_listener()

    def toggle_mood_feature(self):
        """Toggle mood tracking feature"""
        current_state = config_manager.toggle_feature("mood_tracking")
        status = "enabled" if current_state else "disabled"
        response = f"Mood tracking {status}"
        self.append_response(response)
        tts_service.speak(response)

    def toggle_music_feature(self):
        """Toggle music integration feature"""
        current_state = config_manager.toggle_feature("music_integration")
        status = "enabled" if current_state else "disabled"
        response = f"Music integration {status}"
        self.append_response(response)
        tts_service.speak(response)

    def toggle_tts_feature(self):
        """Toggle text-to-speech feature"""
        current_state = config_manager.toggle_feature("tts")
        status = "enabled" if current_state else "disabled"
        response = f"Text-to-speech {status}"
        self.append_response(response)
        # Don't use TTS to announce TTS toggle
        print(f"[TTS] {response}")

    def proactive_check(self):
        """Proactive suggestions and check-ins"""
        # Smart volume adjustment
        volume_msg = volume_service.smart_adjust()
        if volume_msg:
            self.append_response(volume_msg)
            tts_service.speak(volume_msg)
        
        # Mood-based suggestions
        if mood_analyzer.mood_history:
            recent_mood = mood_analyzer.get_current_mood()
            if recent_mood and recent_mood["compound"] < -0.3:
                suggestion = "Your mood seems low. How about a 10-minute break to meditate?"
                self.append_response(suggestion)
                tts_service.speak(suggestion)

    def append_response(self, text: str):
        """Append text to response area"""
        self.response_content.append(text)
        self.response_content.verticalScrollBar().setValue(
            self.response_content.verticalScrollBar().maximum()
        )

    def fade_title(self):
        """Animate title fade out"""
        if self._title_anim and hasattr(self._title_anim, 'state'):
            try:
                self._title_anim.stop()
            except:
                pass
        
        anim = QPropertyAnimation(self._title_op, b"opacity")
        anim.setDuration(1200)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        anim.finished.connect(self.title_label.hide)
        anim.start()
        self._title_anim = anim

    def _on_geometry_refresh(self):
        """Update UI geometry on resize"""
        if self.web:
            self.web.setGeometry(0, 0, self.width(), self.height())
        self.title_label.setGeometry(0, self.height()//2 - 60, self.width(), 120)
        self.response_area.setGeometry(40, self.height()-220, self.width()-80, 160)
        self.menu_btn.setGeometry(self.width()-62, 10, 50, 30)

    def _start_background_listener(self):
        """Start background voice recognition"""
        global BG_LISTENER_STOP
        if not SPEECH_AVAILABLE:
            self.append_response("[Voice recognition not available]")
            return
        
        try:
            recognizer = sr.Recognizer()
            microphone = sr.Microphone()
            
            def callback(recognizer, audio):
                if tts_service.is_playing():
                    return
                try:
                    text = recognizer.recognize_google(audio)
                    if text and text.strip():
                        threading.Thread(
                            target=self.handle_command, 
                            args=(text,), 
                            daemon=True
                        ).start()
                except sr.UnknownValueError:
                    pass
                except Exception as e:
                    error_handler_instance.handle_error(e, "Voice recognition")
            
            BG_LISTENER_STOP = recognizer.listen_in_background(microphone, callback, phrase_time_limit=4)
            error_handler_instance.log_info("Background voice recognition started")
            
        except Exception as e:
            error_handler_instance.handle_error(e, "Voice recognition setup")
            self.append_response("[Voice recognition setup failed]")

    # Window control methods
    def close_application(self):
        """Close the application immediately"""
        global LISTENING, BG_LISTENER_STOP
        LISTENING = False
        if BG_LISTENER_STOP:
            try:
                BG_LISTENER_STOP(wait_for_stop=False)
            except:
                pass
        config_manager.save_config()
        self.close()
        # Get the QApplication instance and quit
        app = QApplication.instance()
        if app:
            app.quit()

    def close_animated(self):
        """Animated close"""
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(300)
        anim.setStartValue(self.windowOpacity())
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        anim.finished.connect(self._do_close)
        anim.start()

    def _do_close(self):
        """Perform actual close"""
        global LISTENING, BG_LISTENER_STOP
        LISTENING = False
        if BG_LISTENER_STOP:
            try:
                BG_LISTENER_STOP(wait_for_stop=False)
            except:
                pass
        config_manager.save_config()
        self.close()

    def minimize_animated(self):
        """Animated minimize"""
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(240)
        anim.setStartValue(self.windowOpacity())
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        def do_min():
            self.showMinimized()
            self.setWindowOpacity(0.0)
        anim.finished.connect(do_min)
        anim.start()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_Escape:
            self.close_application()
        elif event.key() == Qt.Key_F11:
            self.toggle_max_restore()
        else:
            super().keyPressEvent(event)

    def toggle_max_restore(self):
        """Toggle maximize/restore"""
        if self.isMaximized():
            self.showNormal()
            self._is_max = False
        else:
            self.showMaximized()
            self._is_max = True

    # Dragging and snapping
    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self._drag_offset = ev.globalPosition().toPoint() - self.frameGeometry().topLeft()
            ev.accept()
        elif ev.button() == Qt.RightButton:
            self.show_context_menu(ev.globalPosition().toPoint())

    def show_context_menu(self, position):
        """Show right-click context menu"""
        context_menu = QMenu(self)
        context_menu.setStyleSheet("""
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
        
        context_menu.addAction("❌ Close", self.close_application)
        context_menu.addAction("➖ Minimize", self.minimize_animated)
        context_menu.addAction("□ Maximize", self.toggle_max_restore)
        context_menu.addSeparator()
        context_menu.addAction("🔄 Restart", self.restart_application)
        
        context_menu.exec(position)

    def restart_application(self):
        """Restart the application"""
        import sys
        import os
        python = sys.executable
        os.execl(python, python, *sys.argv)

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
        """Snap window to screen edge"""
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

    def closeEvent(self, ev: QCloseEvent):
        """Handle close event"""
        global LISTENING, BG_LISTENER_STOP
        LISTENING = False
        if BG_LISTENER_STOP:
            try:
                BG_LISTENER_STOP(wait_for_stop=False)
            except:
                pass
        config_manager.save_config()
        ev.accept()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Rose AI Assistant v30")
    app.setApplicationVersion("30.0")
    
    # Apply application-wide styling
    app.setStyleSheet("""
        QApplication {
            font-family: 'Segoe UI', Arial, sans-serif;
        }
    """)
    
    # Create and show HUD
    hud = RoseHUD()
    hud.show()
    
    # Start application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
