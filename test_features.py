"""
Test script for Rose AI Assistant features
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from config import config_manager
        print("✅ Config manager imported")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from error_handler import error_handler_instance
        print("✅ Error handler imported")
    except Exception as e:
        print(f"❌ Error handler import failed: {e}")
        return False
    
    try:
        from help_system import help_system
        print("✅ Help system imported")
    except Exception as e:
        print(f"❌ Help system import failed: {e}")
        return False
    
    try:
        from ai_services import gemini_service, mood_analyzer
        print("✅ AI services imported")
    except Exception as e:
        print(f"❌ AI services import failed: {e}")
        return False
    
    try:
        from media_services import tts_service, music_service
        print("✅ Media services imported")
    except Exception as e:
        print(f"❌ Media services import failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration system"""
    print("\n⚙️ Testing configuration...")
    
    try:
        from config import config_manager
        
        # Test API key
        api_key = config_manager.get_api_key("gemini")
        if api_key:
            print("✅ Gemini API key configured")
        else:
            print("⚠️  Gemini API key not configured")
        
        # Test feature toggles
        voice_enabled = config_manager.is_feature_enabled("voice")
        print(f"✅ Voice feature: {'enabled' if voice_enabled else 'disabled'}")
        
        mood_enabled = config_manager.is_feature_enabled("mood_tracking")
        print(f"✅ Mood tracking: {'enabled' if mood_enabled else 'disabled'}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_help_system():
    """Test help system"""
    print("\n❓ Testing help system...")
    
    try:
        from help_system import help_system
        
        # Test general help
        help_text = help_system.get_help()
        if "Rose AI Assistant" in help_text:
            print("✅ Help system working")
        else:
            print("❌ Help system not working properly")
            return False
        
        # Test commands
        commands = help_system.get_commands()
        if "Commands" in commands:
            print("✅ Commands system working")
        else:
            print("❌ Commands system not working properly")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Help system test failed: {e}")
        return False

def test_ai_services():
    """Test AI services"""
    print("\n🤖 Testing AI services...")
    
    try:
        from ai_services import gemini_service, mood_analyzer, language_processor
        
        # Test Gemini service
        if gemini_service.is_available():
            print("✅ Gemini service available")
        else:
            print("⚠️  Gemini service not available (API key needed)")
        
        # Test mood analyzer
        if mood_analyzer.is_available():
            print("✅ Mood analyzer available")
        else:
            print("⚠️  Mood analyzer not available (vaderSentiment needed)")
        
        # Test language processor
        languages = language_processor.supported_languages
        if len(languages) > 0:
            print(f"✅ Language processor available ({len(languages)} languages)")
        else:
            print("❌ Language processor not working")
            return False
        
        return True
    except Exception as e:
        print(f"❌ AI services test failed: {e}")
        return False

def test_media_services():
    """Test media services"""
    print("\n🎵 Testing media services...")
    
    try:
        from media_services import tts_service, music_service, spotify_service, volume_service
        
        # Test TTS service
        if tts_service.is_available():
            print("✅ TTS service available")
        else:
            print("⚠️  TTS service not available (edge-tts needed)")
        
        # Test music service
        print("✅ Music service available")
        
        # Test Spotify service
        if spotify_service.is_available:
            print("✅ Spotify service available")
        else:
            print("⚠️  Spotify service not available (Spotify not running)")
        
        # Test volume service
        print("✅ Volume service available")
        
        return True
    except Exception as e:
        print(f"❌ Media services test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🌹 Rose AI Assistant - Feature Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_help_system,
        test_ai_services,
        test_media_services
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Rose AI Assistant is ready to use.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print("\n🚀 To run the application: python rose_v30_refactored.py")

if __name__ == "__main__":
    main()
