"""
Rose AI Assistant AI Services Module
Handles all AI-related functionality including Gemini, mood analysis, and language processing
"""

import asyncio
import threading
import time
import requests
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import base64

from config import config_manager
from error_handler import error_handler_instance, APIConnectionError, FeatureNotAvailableError

class GeminiService:
    """Handles Gemini AI API interactions"""
    
    def __init__(self):
        self.api_key = config_manager.get_api_key("gemini")
        self.base_url = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"
        self.conversation_history = []
        self.max_history = config_manager.config.features.max_conversation_history
    
    def is_available(self) -> bool:
        """Check if Gemini service is available"""
        return bool(self.api_key)
    
    def call_gemini(self, prompt: str, language: Optional[str] = None, context: str = "") -> str:
        """Make a call to Gemini API with error handling"""
        if not self.is_available():
            raise FeatureNotAvailableError("Gemini API key not configured")
        
        try:
            payload = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": 200}
            }
            
            if language:
                payload["systemInstruction"] = {"parts": [{"text": f"Respond in {language}."}]}
            
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                json=payload,
                timeout=8
            )
            
            if response.status_code != 200:
                raise APIConnectionError(f"Gemini API error: {response.status_code}")
            
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"].strip()
            
        except requests.exceptions.RequestException as e:
            raise APIConnectionError(f"Network error calling Gemini: {str(e)}")
        except Exception as e:
            return error_handler_instance.handle_error(e, f"Gemini call in {context}")
    
    def call_with_context(self, prompt: str, system_instruction: str = "", language: Optional[str] = None) -> str:
        """Call Gemini with conversation context and system instruction"""
        if not self.is_available():
            raise FeatureNotAvailableError("Gemini API key not configured")
        
        try:
            # Add to conversation history
            self.conversation_history.append({"role": "user", "parts": [{"text": prompt}]})
            
            # Limit history size
            if len(self.conversation_history) > self.max_history:
                self.conversation_history = self.conversation_history[-self.max_history:]
            
            payload = {
                "contents": self.conversation_history,
                "generationConfig": {"maxOutputTokens": 200}
            }
            
            if system_instruction:
                payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
            
            if language:
                if "systemInstruction" not in payload:
                    payload["systemInstruction"] = {"parts": []}
                payload["systemInstruction"]["parts"].append({"text": f"Respond in {language}."})
            
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                json=payload,
                timeout=8
            )
            
            if response.status_code != 200:
                error_msg = f"Gemini API error: {response.status_code}\n"
                try:
                    error_details = response.json()
                    if "error" in error_details:
                        error_msg += f"Details: {error_details['error'].get('message', 'Unknown error')}\n"
                except:
                    pass
                    
                error_msg += "\nTroubleshooting:\n"
                error_msg += "1. Check API key format (should start with 'AIza')\n"
                error_msg += "2. Ensure API key is not expired\n"
                error_msg += "3. Run 'python setup_api_key.py' to reconfigure\n"
                error_msg += "4. Visit https://makersuite.google.com/app/apikey for a new key"
                raise APIConnectionError(error_msg)
            
            result = response.json()
            ai_reply = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            # Add AI response to history
            self.conversation_history.append({"role": "model", "parts": [{"text": ai_reply}]})
            
            return ai_reply
            
        except requests.exceptions.RequestException as e:
            raise APIConnectionError(f"Network error calling Gemini: {str(e)}")
        except Exception as e:
            return error_handler_instance.handle_error(e, "Gemini context call")
    
    def analyze_document(self, file_path: str, analysis_type: str = "general") -> str:
        """Analyze uploaded document with Gemini"""
        if not self.is_available():
            raise FeatureNotAvailableError("Gemini API key not configured")
        
        try:
            parts = [{"text": f"Analyze this document for {analysis_type} insights."}]
            
            if file_path.endswith(".pdf"):
                from PyPDF2 import PdfReader
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
                raise ValueError("Unsupported file type")
            
            payload = {
                "contents": [{"role": "user", "parts": parts}],
                "generationConfig": {"maxOutputTokens": 300}
            }
            
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                json=payload,
                timeout=10
            )
            
            if response.status_code != 200:
                raise APIConnectionError(f"Gemini API error: {response.status_code}")
            
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"].strip()
            
        except Exception as e:
            return error_handler_instance.handle_error(e, f"Document analysis of {file_path}")

class MoodAnalyzer:
    """Handles mood analysis and tracking"""
    
    def __init__(self):
        self.sentiment_analyzer = None
        self.mood_history = []
        self.max_history = config_manager.config.features.max_mood_history
        self._initialize_sentiment_analyzer()
    
    def _initialize_sentiment_analyzer(self):
        """Initialize sentiment analyzer if available"""
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
            error_handler_instance.log_info("VADER sentiment analyzer initialized")
        except ImportError:
            error_handler_instance.log_warning("VADER sentiment not available - mood tracking disabled")
    
    def is_available(self) -> bool:
        """Check if mood analysis is available"""
        return self.sentiment_analyzer is not None
    
    def analyze_mood(self, text: str) -> Optional[Dict[str, Any]]:
        """Analyze mood from text"""
        if not self.is_available():
            return None
        
        try:
            scores = self.sentiment_analyzer.polarity_scores(text)
            mood_data = {
                "timestamp": datetime.now().isoformat(),
                "text": text[:100],  # Store first 100 chars
                "compound": scores['compound'],
                "positive": scores['pos'],
                "negative": scores['neg'],
                "neutral": scores['neu']
            }
            
            # Add to history
            self.mood_history.append(mood_data)
            
            # Limit history size
            if len(self.mood_history) > self.max_history:
                self.mood_history.pop(0)
            
            return mood_data
            
        except Exception as e:
            error_handler_instance.handle_error(e, "Mood analysis")
            return None
    
    def get_current_mood(self) -> Optional[Dict[str, Any]]:
        """Get most recent mood data"""
        return self.mood_history[-1] if self.mood_history else None
    
    def get_mood_trend(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get mood trend for specified days"""
        if not self.mood_history:
            return []
        
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        recent_moods = [
            mood for mood in self.mood_history
            if datetime.fromisoformat(mood["timestamp"]).timestamp() > cutoff_date
        ]
        return recent_moods
    
    def get_mood_summary(self) -> str:
        """Get mood summary text"""
        if not self.mood_history:
            return "No mood data available yet"
        
        recent_mood = self.get_current_mood()
        if not recent_mood:
            return "No recent mood data"
        
        compound = recent_mood["compound"]
        if compound > 0.5:
            return "You're feeling very positive! 😊"
        elif compound > 0.1:
            return "You're in a good mood! 🙂"
        elif compound > -0.1:
            return "You're feeling neutral 😐"
        elif compound > -0.5:
            return "You seem a bit down 😔"
        else:
            return "You're feeling quite low 😢"

class LanguageProcessor:
    """Handles language detection and processing"""
    
    def __init__(self):
        self.supported_languages = {
            "en": "English",
            "es": "Spanish", 
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese"
        }
        self.current_language = config_manager.config.ui.language
    
    def detect_language(self, text: str) -> str:
        """Simple language detection (can be enhanced with proper library)"""
        # Simple heuristic-based detection
        if any(word in text.lower() for word in ["hola", "gracias", "por favor"]):
            return "es"
        elif any(word in text.lower() for word in ["bonjour", "merci", "s'il vous plaît"]):
            return "fr"
        elif any(word in text.lower() for word in ["guten tag", "danke", "bitte"]):
            return "de"
        elif any(word in text.lower() for word in ["ciao", "grazie", "per favore"]):
            return "it"
        elif any(word in text.lower() for word in ["olá", "obrigado", "por favor"]):
            return "pt"
        elif any(word in text.lower() for word in ["привет", "спасибо", "пожалуйста"]):
            return "ru"
        elif any(word in text.lower() for word in ["こんにちは", "ありがとう", "お願いします"]):
            return "ja"
        elif any(word in text.lower() for word in ["안녕하세요", "감사합니다", "부탁드립니다"]):
            return "ko"
        elif any(word in text.lower() for word in ["你好", "谢谢", "请"]):
            return "zh"
        else:
            return "en"  # Default to English
    
    def set_language(self, language: str) -> bool:
        """Set current language"""
        if language in self.supported_languages:
            self.current_language = language
            config_manager.config.ui.language = language
            config_manager.save_config()
            return True
        return False
    
    def get_language_name(self, code: str) -> str:
        """Get language name from code"""
        return self.supported_languages.get(code, "Unknown")
    
    def get_voice_for_language(self, language: str) -> str:
        """Get appropriate voice for language"""
        voice_mapping = {
            "en": "en-US-JennyNeural",
            "es": "es-ES-ElviraNeural",
            "fr": "fr-FR-DeniseNeural",
            "de": "de-DE-KatjaNeural",
            "it": "it-IT-ElsaNeural",
            "pt": "pt-BR-FranciscaNeural",
            "ru": "ru-RU-SvetlanaNeural",
            "ja": "ja-JP-NanamiNeural",
            "ko": "ko-KR-SunHiNeural",
            "zh": "zh-CN-XiaoxiaoNeural"
        }
        return voice_mapping.get(language, "en-US-JennyNeural")

# Global service instances
gemini_service = GeminiService()
mood_analyzer = MoodAnalyzer()
language_processor = LanguageProcessor()
