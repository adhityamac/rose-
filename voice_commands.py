"""
Voice Commands System for Rose AI Assistant
Fast, responsive voice command processing with custom command support
"""

import re
import time
import threading
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from enum import Enum

class CommandPriority(Enum):
    HIGH = 1
    NORMAL = 2
    LOW = 3

@dataclass
class VoiceCommand:
    """Represents a voice command"""
    pattern: str
    handler: Callable
    description: str
    priority: CommandPriority = CommandPriority.NORMAL
    requires_confirmation: bool = False
    category: str = "general"

class VoiceCommandManager:
    """Manages voice commands and custom commands"""
    
    def __init__(self):
        self.commands: Dict[str, VoiceCommand] = {}
        self.custom_commands: Dict[str, VoiceCommand] = {}
        self.command_history: List[str] = []
        self.is_processing = False
        self.response_times = []
        
        # Initialize default commands
        self._setup_default_commands()
    
    def _setup_default_commands(self):
        """Setup default voice commands for fast response"""
        
        # System commands (HIGH priority)
        self.add_command(
            "close|exit|quit|shutdown",
            self._handle_system_command,
            "Close the application",
            CommandPriority.HIGH,
            category="system"
        )
        
        self.add_command(
            "minimize|min|hide",
            self._handle_minimize,
            "Minimize the window",
            CommandPriority.HIGH,
            category="system"
        )
        
        self.add_command(
            "maximize|max|fullscreen",
            self._handle_maximize,
            "Maximize the window",
            CommandPriority.HIGH,
            category="system"
        )
        
        # Media commands (NORMAL priority)
        self.add_command(
            "play music|start music|music",
            self._handle_play_music,
            "Play music",
            CommandPriority.NORMAL,
            category="media"
        )
        
        self.add_command(
            "stop music|pause music|stop",
            self._handle_stop_music,
            "Stop music",
            CommandPriority.NORMAL,
            category="media"
        )
        
        self.add_command(
            "volume up|louder|increase volume",
            self._handle_volume_up,
            "Increase volume",
            CommandPriority.NORMAL,
            category="media"
        )
        
        self.add_command(
            "volume down|quieter|decrease volume",
            self._handle_volume_down,
            "Decrease volume",
            CommandPriority.NORMAL,
            category="media"
        )
        
        # AI commands (NORMAL priority)
        self.add_command(
            "hello|hi|hey|greetings",
            self._handle_greeting,
            "Greet the assistant",
            CommandPriority.NORMAL,
            category="ai"
        )
        
        self.add_command(
            "what time|current time|time",
            self._handle_time,
            "Get current time",
            CommandPriority.NORMAL,
            category="ai"
        )
        
        self.add_command(
            "what date|current date|date",
            self._handle_date,
            "Get current date",
            CommandPriority.NORMAL,
            category="ai"
        )
        
        # Help commands (LOW priority)
        self.add_command(
            "help|commands|what can you do",
            self._handle_help,
            "Show available commands",
            CommandPriority.LOW,
            category="help"
        )
        
        self.add_command(
            "list commands|show commands",
            self._handle_list_commands,
            "List all commands",
            CommandPriority.LOW,
            category="help"
        )
    
    def add_command(self, pattern: str, handler: Callable, description: str, 
                   priority: CommandPriority = CommandPriority.NORMAL,
                   requires_confirmation: bool = False, category: str = "general"):
        """Add a voice command"""
        command = VoiceCommand(
            pattern=pattern,
            handler=handler,
            description=description,
            priority=priority,
            requires_confirmation=requires_confirmation,
            category=category
        )
        self.commands[pattern] = command
    
    def add_custom_command(self, pattern: str, handler: Callable, description: str,
                          priority: CommandPriority = CommandPriority.NORMAL,
                          requires_confirmation: bool = False, category: str = "custom"):
        """Add a custom voice command"""
        command = VoiceCommand(
            pattern=pattern,
            handler=handler,
            description=description,
            priority=priority,
            requires_confirmation=requires_confirmation,
            category=category
        )
        self.custom_commands[pattern] = command
    
    def process_voice_input(self, text: str) -> bool:
        """Process voice input and execute matching command"""
        if self.is_processing:
            return False
            
        start_time = time.time()
        self.is_processing = True
        
        try:
            # Normalize text
            text = text.lower().strip()
            self.command_history.append(text)
            
            # Check custom commands first (higher priority)
            for pattern, command in self.custom_commands.items():
                if self._match_pattern(pattern, text):
                    self._execute_command(command, text)
                    self._record_response_time(start_time)
                    return True
            
            # Check default commands
            for pattern, command in self.commands.items():
                if self._match_pattern(pattern, text):
                    self._execute_command(command, text)
                    self._record_response_time(start_time)
                    return True
            
            return False
            
        finally:
            self.is_processing = False
    
    def _match_pattern(self, pattern: str, text: str) -> bool:
        """Check if text matches command pattern"""
        # Split pattern by | for multiple options
        patterns = pattern.split('|')
        for p in patterns:
            if re.search(p.strip(), text, re.IGNORECASE):
                return True
        return False
    
    def _execute_command(self, command: VoiceCommand, text: str):
        """Execute a command"""
        try:
            if command.requires_confirmation:
                # TODO: Implement confirmation system
                pass
            
            # Execute in separate thread for non-blocking
            threading.Thread(
                target=command.handler,
                args=(text,),
                daemon=True
            ).start()
            
        except Exception as e:
            print(f"Error executing command: {e}")
    
    def _record_response_time(self, start_time: float):
        """Record response time for performance monitoring"""
        response_time = time.time() - start_time
        self.response_times.append(response_time)
        
        # Keep only last 100 response times
        if len(self.response_times) > 100:
            self.response_times = self.response_times[-100:]
    
    def get_average_response_time(self) -> float:
        """Get average response time"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    def get_commands_by_category(self, category: str) -> List[VoiceCommand]:
        """Get commands by category"""
        all_commands = {**self.commands, **self.custom_commands}
        return [cmd for cmd in all_commands.values() if cmd.category == category]
    
    def get_all_commands(self) -> List[VoiceCommand]:
        """Get all commands"""
        return list(self.commands.values()) + list(self.custom_commands.values())
    
    # Default command handlers
    def _handle_system_command(self, text: str):
        """Handle system commands"""
        print("🔄 Closing application...")
        # This will be connected to the main app's close method
    
    def _handle_minimize(self, text: str):
        """Handle minimize command"""
        print("➖ Minimizing window...")
        # This will be connected to the main app's minimize method
    
    def _handle_maximize(self, text: str):
        """Handle maximize command"""
        print("□ Maximizing window...")
        # This will be connected to the main app's maximize method
    
    def _handle_play_music(self, text: str):
        """Handle play music command"""
        print("🎵 Playing music...")
        # This will be connected to the music service
    
    def _handle_stop_music(self, text: str):
        """Handle stop music command"""
        print("⏹️ Stopping music...")
        # This will be connected to the music service
    
    def _handle_volume_up(self, text: str):
        """Handle volume up command"""
        print("🔊 Volume up...")
        # This will be connected to the volume service
    
    def _handle_volume_down(self, text: str):
        """Handle volume down command"""
        print("🔉 Volume down...")
        # This will be connected to the volume service
    
    def _handle_greeting(self, text: str):
        """Handle greeting command"""
        greetings = [
            "Hello! How can I help you today?",
            "Hi there! What would you like to do?",
            "Hey! I'm here and ready to assist!",
            "Greetings! What can I do for you?"
        ]
        import random
        response = random.choice(greetings)
        print(f"👋 {response}")
    
    def _handle_time(self, text: str):
        """Handle time command"""
        from datetime import datetime
        current_time = datetime.now().strftime("%I:%M %p")
        print(f"🕐 Current time is {current_time}")
    
    def _handle_date(self, text: str):
        """Handle date command"""
        from datetime import datetime
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        print(f"📅 Today is {current_date}")
    
    def _handle_help(self, text: str):
        """Handle help command"""
        print("🤖 I can help you with:")
        print("• System: close, minimize, maximize")
        print("• Media: play music, stop music, volume up/down")
        print("• AI: hello, what time, what date")
        print("• Help: help, list commands")
    
    def _handle_list_commands(self, text: str):
        """Handle list commands"""
        print("📋 Available commands:")
        for cmd in self.get_all_commands():
            print(f"• {cmd.pattern} - {cmd.description}")

# Global instance
voice_command_manager = VoiceCommandManager()
