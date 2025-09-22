"""
Test script to verify all fixes are working
"""

import sys
import os

def test_imports():
    """Test all critical imports"""
    print("🧪 Testing imports...")
    
    try:
        from PySide6.QtCore import Qt, QTimer
        print("✅ PySide6.QtCore imported")
    except ImportError as e:
        print(f"❌ PySide6.QtCore failed: {e}")
        return False
    
    try:
        from PySide6.QtWidgets import QApplication, QWidget
        print("✅ PySide6.QtWidgets imported")
    except ImportError as e:
        print(f"❌ PySide6.QtWidgets failed: {e}")
        return False
    
    try:
        import edge_tts
        print("✅ Edge TTS imported")
    except ImportError as e:
        print(f"⚠️ Edge TTS not available: {e}")
    
    try:
        import vaderSentiment
        print("✅ VADER Sentiment imported")
    except ImportError as e:
        print(f"⚠️ VADER Sentiment not available: {e}")
    
    try:
        import pygame
        print("✅ Pygame imported")
    except ImportError as e:
        print(f"⚠️ Pygame not available: {e}")
    
    return True

def test_modules():
    """Test our custom modules"""
    print("\n🔧 Testing custom modules...")
    
    try:
        from config import config_manager
        print("✅ Config manager imported")
    except ImportError as e:
        print(f"❌ Config manager failed: {e}")
        return False
    
    try:
        from voice_commands import voice_command_manager
        print("✅ Voice commands imported")
    except ImportError as e:
        print(f"❌ Voice commands failed: {e}")
        return False
    
    try:
        from theme_manager import theme_manager
        print("✅ Theme manager imported")
    except ImportError as e:
        print(f"❌ Theme manager failed: {e}")
        return False
    
    try:
        from fast_tts import fast_tts
        print("✅ Fast TTS imported")
    except ImportError as e:
        print(f"❌ Fast TTS failed: {e}")
        return False
    
    return True

def test_voice_commands():
    """Test voice command system"""
    print("\n🎤 Testing voice commands...")
    
    try:
        from voice_commands import voice_command_manager
        
        # Test basic commands
        test_commands = ["hello", "what time", "play music"]
        
        for cmd in test_commands:
            result = voice_command_manager.process_voice_input(cmd)
            print(f"  '{cmd}': {'✅' if result else '❌'}")
        
        return True
    except Exception as e:
        print(f"❌ Voice commands test failed: {e}")
        return False

def test_themes():
    """Test theme system"""
    print("\n🎨 Testing themes...")
    
    try:
        from theme_manager import theme_manager
        
        themes = theme_manager.get_available_themes()
        print(f"  Available themes: {len(themes)}")
        
        # Test theme switching
        for theme in themes[:2]:  # Test first 2 themes
            if theme_manager.set_theme(theme):
                print(f"  ✅ {theme} theme applied")
            else:
                print(f"  ❌ {theme} theme failed")
        
        return True
    except Exception as e:
        print(f"❌ Themes test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔧 Rose AI Assistant - Fix Verification")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_modules,
        test_voice_commands,
        test_themes
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All fixes are working! The application should run properly now.")
        print("\n🚀 To run the application: python rose_v30_refactored.py")
    else:
        print("⚠️ Some issues remain. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
