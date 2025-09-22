"""
Rose AI Assistant Configuration Management
Handles all configuration, API keys, and settings securely
"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class APIConfig:
    """API configuration settings"""
    gemini_api_key: str = ""
    openweather_api_key: str = ""
    newsapi_api_key: str = ""
    email_user: str = ""
    email_pass: str = ""

@dataclass
class UIConfig:
    """UI and display settings"""
    window_width: int = 880
    window_height: int = 600
    primary_color: str = "#FF69B4"
    secondary_color: str = "#9932CC"
    accent_color: str = "#FFB6C1"
    language: str = "en"
    personality: str = "caring"

@dataclass
class FeatureConfig:
    """Feature toggles and settings"""
    enable_voice: bool = True
    enable_gestures: bool = True
    enable_screen_analysis: bool = True
    enable_mood_tracking: bool = True
    enable_music_integration: bool = True
    enable_calendar_export: bool = True
    enable_email: bool = True
    max_conversation_history: int = 100
    max_mood_history: int = 100
    proactive_check_interval: int = 300  # seconds

@dataclass
class RoseConfig:
    """Main configuration container"""
    api: APIConfig
    ui: UIConfig
    features: FeatureConfig
    
    def __init__(self):
        self.api = APIConfig()
        self.ui = UIConfig()
        self.features = FeatureConfig()

class ConfigManager:
    """Manages configuration loading, saving, and environment variable handling"""
    
    def __init__(self, config_file: str = "rose_config.json"):
        self.config_file = Path(config_file)
        self.config = RoseConfig()
        self.load_config()
        self.load_from_env()
    
    def load_config(self) -> None:
        """Load configuration from file"""
        # Load from .env file first
        from dotenv import load_dotenv
        load_dotenv()
        
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._update_config_from_dict(data)
        except Exception as e:
            print(f"Config load error: {e}")
    
    def save_config(self) -> None:
        """Save configuration to file"""
        try:
            config_dict = {
                'api': asdict(self.config.api),
                'ui': asdict(self.config.ui),
                'features': asdict(self.config.features)
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Config save error: {e}")
    
    def load_from_env(self) -> None:
        """Load sensitive data from environment variables"""
        # API Keys - You can add your API key directly here as a fallback
        GEMINI_API_KEY_DIRECT = "AIzaSyApR_SG0n9FatvRuLxB9Sydbmt0kkwHCKE"  # Add your API key here: "AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        
        self.config.api.gemini_api_key = os.getenv('GEMINI_API_KEY', GEMINI_API_KEY_DIRECT)
        self.config.api.openweather_api_key = os.getenv('OPENWEATHER_API_KEY', self.config.api.openweather_api_key)
        self.config.api.newsapi_api_key = os.getenv('ROSE_NEWSAPI_API_KEY', self.config.api.newsapi_api_key)
        self.config.api.email_user = os.getenv('ROSE_EMAIL_USER', self.config.api.email_user)
        self.config.api.email_pass = os.getenv('ROSE_EMAIL_PASS', self.config.api.email_pass)
        
        # UI Settings
        self.config.ui.language = os.getenv('ROSE_LANGUAGE', self.config.ui.language)
        self.config.ui.personality = os.getenv('ROSE_PERSONALITY', self.config.ui.personality)
    
    def _update_config_from_dict(self, data: Dict[str, Any]) -> None:
        """Update configuration from dictionary"""
        if 'api' in data:
            for key, value in data['api'].items():
                if hasattr(self.config.api, key):
                    setattr(self.config.api, key, value)
        
        if 'ui' in data:
            for key, value in data['ui'].items():
                if hasattr(self.config.ui, key):
                    setattr(self.config.ui, key, value)
        
        if 'features' in data:
            for key, value in data['features'].items():
                if hasattr(self.config.features, key):
                    setattr(self.config.features, key, value)
    
    def get_api_key(self, service: str) -> str:
        """Get API key for a service"""
        return getattr(self.config.api, f"{service}_api_key", "")
    
    def set_api_key(self, service: str, key: str) -> None:
        """Set API key for a service"""
        setattr(self.config.api, f"{service}_api_key", key)
        self.save_config()
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        return getattr(self.config.features, f"enable_{feature}", False)
    
    def toggle_feature(self, feature: str) -> bool:
        """Toggle a feature on/off"""
        current = self.is_feature_enabled(feature)
        setattr(self.config.features, f"enable_{feature}", not current)
        self.save_config()
        return not current

# Global config instance
config_manager = ConfigManager()
