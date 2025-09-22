"""
Rose AI Assistant Help System
Provides comprehensive help, command discovery, and user guidance
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class CommandCategory(Enum):
    """Command categories for organization"""
    VOICE = "Voice & Speech"
    MOOD = "Mood & Wellness"
    MEDIA = "Media & Music"
    PRODUCTIVITY = "Productivity"
    SYSTEM = "System Control"
    CREATIVE = "Creative Features"
    INTEGRATION = "Integrations"
    HELP = "Help & Info"

@dataclass
class Command:
    """Command definition"""
    trigger: str
    description: str
    category: CommandCategory
    example: str
    requires_setup: bool = False
    setup_instructions: str = ""

class HelpSystem:
    """Comprehensive help and command discovery system"""
    
    def __init__(self):
        self.commands = self._initialize_commands()
        self.categories = list(CommandCategory)
    
    def _initialize_commands(self) -> Dict[str, Command]:
        """Initialize all available commands"""
        commands = {}
        
        # Voice & Speech Commands
        voice_commands = [
            Command("hello", "Greet Rose", CommandCategory.VOICE, "hello", False),
            Command("speak in [language]", "Change language", CommandCategory.VOICE, "speak in spanish", False),
            Command("set personality [type]", "Change personality", CommandCategory.VOICE, "set personality witty", False),
            Command("voice to text", "Convert speech to text", CommandCategory.VOICE, "voice to text", True, "Requires microphone"),
            Command("transcribe meeting", "Transcribe ongoing conversation", CommandCategory.VOICE, "transcribe meeting", True, "Requires microphone"),
        ]
        
        # Mood & Wellness Commands
        mood_commands = [
            Command("show my mood", "Display mood chart", CommandCategory.MOOD, "show my mood", False),
            Command("mood chart", "Show mood visualization", CommandCategory.MOOD, "mood chart", False),
            Command("analyze emojis", "Analyze emoji usage", CommandCategory.MOOD, "analyze emojis in hello 😊", False),
            Command("mood temperature", "Show mood as temperature", CommandCategory.MOOD, "mood temperature", False),
            Command("write journal [entry]", "Add journal entry", CommandCategory.MOOD, "write journal feeling great today", False),
            Command("proofread [text]", "Get writing feedback", CommandCategory.MOOD, "proofread this text", False),
        ]
        
        # Media & Music Commands
        media_commands = [
            Command("play [song] on youtube", "Play song on YouTube", CommandCategory.MEDIA, "play happy songs on youtube", False),
            Command("open youtube", "Open YouTube", CommandCategory.MEDIA, "open youtube", False),
            Command("spotify play", "Play/pause Spotify", CommandCategory.MEDIA, "spotify play", True, "Requires Spotify running"),
            Command("spotify next", "Next track", CommandCategory.MEDIA, "spotify next", True, "Requires Spotify running"),
            Command("spotify previous", "Previous track", CommandCategory.MEDIA, "spotify previous", True, "Requires Spotify running"),
            Command("suggest song", "Get music suggestion", CommandCategory.MEDIA, "suggest song", False),
            Command("learn music [song]", "Add to music taste", CommandCategory.MEDIA, "learn music Bohemian Rhapsody", False),
            Command("mood playlist", "Create mood-based playlist", CommandCategory.MEDIA, "mood playlist", False),
            Command("apple music [song]", "Search Apple Music", CommandCategory.MEDIA, "apple music Imagine Dragons", False),
            Command("soundcloud [song]", "Search SoundCloud", CommandCategory.MEDIA, "soundcloud electronic music", False),
            Command("audio visualization", "Open audio visualizer", CommandCategory.MEDIA, "audio visualization", False),
        ]
        
        # Productivity Commands
        productivity_commands = [
            Command("remind me to [task]", "Add reminder", CommandCategory.PRODUCTIVITY, "remind me to call mom", False),
            Command("what are my reminders", "List reminders", CommandCategory.PRODUCTIVITY, "what are my reminders", False),
            Command("add habit [habit]", "Add new habit", CommandCategory.PRODUCTIVITY, "add habit exercise daily", False),
            Command("check habit [habit]", "Mark habit complete", CommandCategory.PRODUCTIVITY, "check habit exercise daily", False),
            Command("start tracking [project]", "Start time tracking", CommandCategory.PRODUCTIVITY, "start tracking coding project", False),
            Command("stop tracking [project]", "Stop time tracking", CommandCategory.PRODUCTIVITY, "stop tracking coding project", False),
            Command("export calendar", "Export to calendar", CommandCategory.PRODUCTIVITY, "export calendar", True, "Requires icalendar library"),
            Command("export csv", "Export to CSV", CommandCategory.PRODUCTIVITY, "export csv", False),
        ]
        
        # System Control Commands
        system_commands = [
            Command("volume up", "Increase volume", CommandCategory.SYSTEM, "volume up", False),
            Command("volume down", "Decrease volume", CommandCategory.SYSTEM, "volume down", False),
            Command("mute", "Mute system", CommandCategory.SYSTEM, "mute", False),
            Command("unmute", "Unmute system", CommandCategory.SYSTEM, "unmute", False),
            Command("smart volume", "Auto-adjust volume", CommandCategory.SYSTEM, "smart volume", False),
            Command("weather in [city]", "Get weather", CommandCategory.SYSTEM, "weather in London", True, "Requires OpenWeather API key"),
            Command("news", "Get news headlines", CommandCategory.SYSTEM, "news", True, "Requires NewsAPI key"),
            Command("open browser", "Open web browser", CommandCategory.SYSTEM, "open browser", False),
            Command("open brave", "Open Brave browser", CommandCategory.SYSTEM, "open brave", False),
            Command("open chrome", "Open Chrome browser", CommandCategory.SYSTEM, "open chrome", False),
        ]
        
        # Creative Features Commands
        creative_commands = [
            Command("word cloud", "Generate word cloud", CommandCategory.CREATIVE, "word cloud", True, "Requires wordcloud library"),
            Command("show my words", "Show conversation word cloud", CommandCategory.CREATIVE, "show my words", True, "Requires wordcloud library"),
            Command("change theme from image", "Extract theme from image", CommandCategory.CREATIVE, "change theme from image", True, "Place 'user_image.jpg' in folder"),
            Command("show week summary", "Generate week summary", CommandCategory.CREATIVE, "show week summary", True, "Requires matplotlib"),
            Command("tell a story [topic]", "Generate interactive story", CommandCategory.CREATIVE, "tell a story about space adventure", False),
            Command("casual conversation", "Start casual chat", CommandCategory.CREATIVE, "casual conversation", False),
        ]
        
        # Integration Commands
        integration_commands = [
            Command("upload document", "Analyze uploaded file", CommandCategory.INTEGRATION, "upload document", True, "Requires file dialog"),
            Command("analyze image", "Analyze uploaded image", CommandCategory.INTEGRATION, "analyze image", True, "Requires file dialog"),
            Command("what's on my screen", "Analyze screen content", CommandCategory.INTEGRATION, "what's on my screen", True, "Requires pyautogui"),
            Command("what do you see", "Describe webcam view", CommandCategory.INTEGRATION, "what do you see", True, "Requires webcam"),
            Command("describe photo", "Describe captured photo", CommandCategory.INTEGRATION, "describe photo", True, "Requires webcam"),
            Command("send email to [email] subject [subject] body [body]", "Send email", CommandCategory.INTEGRATION, "send email to friend@example.com subject Hello body How are you?", True, "Requires email credentials"),
        ]
        
        # Help Commands
        help_commands = [
            Command("help", "Show this help", CommandCategory.HELP, "help", False),
            Command("commands", "List all commands", CommandCategory.HELP, "commands", False),
            Command("help [category]", "Show category help", CommandCategory.HELP, "help mood", False),
            Command("what can you do", "Show capabilities", CommandCategory.HELP, "what can you do", False),
            Command("setup guide", "Show setup instructions", CommandCategory.HELP, "setup guide", False),
        ]
        
        # Combine all commands
        all_commands = (voice_commands + mood_commands + media_commands + 
                       productivity_commands + system_commands + creative_commands + 
                       integration_commands + help_commands)
        
        for cmd in all_commands:
            commands[cmd.trigger] = cmd
        
        return commands
    
    def get_help(self, category: Optional[CommandCategory] = None) -> str:
        """Get help text for all commands or specific category"""
        if category:
            return self._get_category_help(category)
        else:
            return self._get_general_help()
    
    def _get_general_help(self) -> str:
        """Get general help text"""
        help_text = "🌹 Rose AI Assistant - Help System\n\n"
        help_text += "I'm your personal AI assistant with many capabilities!\n\n"
        help_text += "📋 Available Categories:\n"
        
        for category in self.categories:
            if category != CommandCategory.HELP:
                count = len([cmd for cmd in self.commands.values() if cmd.category == category])
                help_text += f"  • {category.value}: {count} commands\n"
        
        help_text += "\n💡 Quick Tips:\n"
        help_text += "  • Say 'help [category]' for specific help\n"
        help_text += "  • Say 'commands' to see all commands\n"
        help_text += "  • Say 'what can you do' for capabilities\n"
        help_text += "  • Say 'setup guide' for installation help\n\n"
        help_text += "🎯 Popular Commands:\n"
        help_text += "  • 'hello' - Greet me\n"
        help_text += "  • 'show my mood' - See your mood chart\n"
        help_text += "  • 'play [song] on youtube' - Play music\n"
        help_text += "  • 'remind me to [task]' - Add reminder\n"
        help_text += "  • 'weather in [city]' - Get weather\n"
        
        return help_text
    
    def _get_category_help(self, category: CommandCategory) -> str:
        """Get help for specific category"""
        category_commands = [cmd for cmd in self.commands.values() if cmd.category == category]
        
        help_text = f"🌹 {category.value} Commands\n\n"
        
        for cmd in category_commands:
            help_text += f"📌 {cmd.trigger}\n"
            help_text += f"   {cmd.description}\n"
            help_text += f"   Example: '{cmd.example}'\n"
            if cmd.requires_setup:
                help_text += f"   ⚠️  Setup: {cmd.setup_instructions}\n"
            help_text += "\n"
        
        return help_text
    
    def get_commands(self) -> str:
        """Get list of all commands"""
        commands_text = "🌹 All Available Commands\n\n"
        
        for category in self.categories:
            if category == CommandCategory.HELP:
                continue
                
            category_commands = [cmd for cmd in self.commands.values() if cmd.category == category]
            if category_commands:
                commands_text += f"📂 {category.value}:\n"
                for cmd in category_commands:
                    commands_text += f"  • {cmd.trigger}\n"
                commands_text += "\n"
        
        return commands_text
    
    def get_capabilities(self) -> str:
        """Get capabilities overview"""
        capabilities = [
            "🎤 Voice Recognition & Text-to-Speech",
            "😊 Mood Analysis & Tracking",
            "🎵 Music Integration (YouTube, Spotify, Apple Music, SoundCloud)",
            "📝 Productivity Tools (Reminders, Habits, Time Tracking)",
            "🎨 Creative Features (Word Clouds, Theme Extraction, Visualizations)",
            "🌐 System Integration (Volume, Weather, News, Browser)",
            "📊 Data Analysis (Document Analysis, Screen Analysis)",
            "💬 Natural Language Processing",
            "🌍 Multi-language Support",
            "⚙️ Customizable Personality",
            "📱 Cross-platform Compatibility"
        ]
        
        capabilities_text = "🌹 Rose AI Assistant Capabilities\n\n"
        capabilities_text += "I can help you with:\n\n"
        for capability in capabilities:
            capabilities_text += f"  {capability}\n"
        
        capabilities_text += "\n💡 Just ask me anything or try a command!\n"
        return capabilities_text
    
    def get_setup_guide(self) -> str:
        """Get setup guide"""
        setup_text = "🌹 Rose AI Assistant Setup Guide\n\n"
        setup_text += "📋 Required Dependencies:\n"
        setup_text += "  • PySide6 (GUI framework)\n"
        setup_text += "  • speech_recognition (voice input)\n"
        setup_text += "  • edge-tts (text-to-speech)\n"
        setup_text += "  • requests (API calls)\n\n"
        
        setup_text += "🔧 Optional Dependencies:\n"
        setup_text += "  • colorthief (theme extraction)\n"
        setup_text += "  • wordcloud + matplotlib (visualizations)\n"
        setup_text += "  • vaderSentiment (mood analysis)\n"
        setup_text += "  • emoji (emoji analysis)\n"
        setup_text += "  • opencv + mediapipe (gesture recognition)\n"
        setup_text += "  • pyautogui (screen capture)\n"
        setup_text += "  • icalendar (calendar export)\n"
        setup_text += "  • PyPDF2 (PDF analysis)\n"
        setup_text += "  • geopy (location services)\n\n"
        
        setup_text += "🔑 API Keys (Optional but Recommended):\n"
        setup_text += "  • GEMINI_API_KEY (for AI responses)\n"
        setup_text += "  • OPENWEATHER_API_KEY (for weather)\n"
        setup_text += "  • NEWSAPI_API_KEY (for news)\n"
        setup_text += "  • EMAIL_USER & EMAIL_PASS (for email)\n\n"
        
        setup_text += "⚙️ Installation:\n"
        setup_text += "  1. Install Python 3.8+\n"
        setup_text += "  2. Install dependencies: pip install -r requirements.txt\n"
        setup_text += "  3. Set environment variables for API keys\n"
        setup_text += "  4. Run: python rose_v29_5.py\n\n"
        
        setup_text += "🎯 First Steps:\n"
        setup_text += "  1. Say 'hello' to test voice recognition\n"
        setup_text += "  2. Try 'show my mood' for mood tracking\n"
        setup_text += "  3. Use 'help' to see all commands\n"
        setup_text += "  4. Customize settings in the menu (⋯)\n"
        
        return setup_text
    
    def find_command(self, query: str) -> List[Command]:
        """Find commands matching query"""
        query = query.lower()
        matches = []
        
        for cmd in self.commands.values():
            if (query in cmd.trigger.lower() or 
                query in cmd.description.lower() or 
                query in cmd.example.lower()):
                matches.append(cmd)
        
        return matches
    
    def get_command_info(self, trigger: str) -> Optional[Command]:
        """Get detailed info about a specific command"""
        return self.commands.get(trigger.lower())

# Global help system instance
help_system = HelpSystem()
