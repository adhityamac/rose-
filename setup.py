"""
Rose AI Assistant Setup Script
Helps users install dependencies and configure the application
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return False

def create_config_file():
    """Create initial configuration file"""
    config_file = Path("rose_config.json")
    if not config_file.exists():
        print("⚙️ Creating configuration file...")
        config_data = {
            "api": {
                "gemini_api_key": "",
                "openweather_api_key": "",
                "newsapi_api_key": "",
                "email_user": "",
                "email_pass": ""
            },
            "ui": {
                "window_width": 880,
                "window_height": 600,
                "primary_color": "#FF69B4",
                "secondary_color": "#9932CC",
                "accent_color": "#FFB6C1",
                "language": "en",
                "personality": "caring"
            },
            "features": {
                "enable_voice": True,
                "enable_gestures": True,
                "enable_screen_analysis": True,
                "enable_mood_tracking": True,
                "enable_music_integration": True,
                "enable_calendar_export": True,
                "enable_email": True,
                "max_conversation_history": 100,
                "max_mood_history": 100,
                "proactive_check_interval": 300
            }
        }
        
        import json
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        print("✅ Configuration file created")
    else:
        print("✅ Configuration file already exists")

def create_env_template():
    """Create environment variables template"""
    env_file = Path(".env.template")
    if not env_file.exists():
        print("🔑 Creating environment variables template...")
        env_content = """# Rose AI Assistant Environment Variables
# Copy this file to .env and fill in your API keys

# AI Services
ROSE_GEMINI_API_KEY=your_gemini_api_key_here

# Weather Service
ROSE_OPENWEATHER_API_KEY=your_openweather_api_key_here

# News Service
ROSE_NEWSAPI_API_KEY=your_newsapi_key_here

# Email Service
ROSE_EMAIL_USER=your_email@example.com
ROSE_EMAIL_PASS=your_email_password

# Language and Personality
ROSE_LANGUAGE=en
ROSE_PERSONALITY=caring
"""
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ Environment template created (.env.template)")
        print("   Copy to .env and fill in your API keys")

def check_optional_dependencies():
    """Check which optional dependencies are available"""
    print("🔍 Checking optional dependencies...")
    
    optional_deps = {
        "colorthief": "Theme extraction from images",
        "wordcloud": "Word cloud generation",
        "matplotlib": "Data visualization",
        "vaderSentiment": "Mood analysis",
        "opencv-python": "Computer vision",
        "mediapipe": "Gesture recognition",
        "pyautogui": "Screen capture",
        "icalendar": "Calendar export",
        "PyPDF2": "PDF analysis",
        "geopy": "Location services",
        "emoji": "Emoji analysis"
    }
    
    available = []
    missing = []
    
    for dep, description in optional_deps.items():
        try:
            __import__(dep)
            available.append(f"✅ {dep}: {description}")
        except ImportError:
            missing.append(f"❌ {dep}: {description}")
    
    print("\nAvailable optional features:")
    for item in available:
        print(f"  {item}")
    
    if missing:
        print("\nMissing optional features:")
        for item in missing:
            print(f"  {item}")
        print("\nTo install missing features, run:")
        print("  pip install " + " ".join([item.split()[1] for item in missing]))

def create_shortcuts():
    """Create desktop shortcuts (Windows)"""
    if platform.system() == "Windows":
        try:
            import winshell # pyright: ignore[reportMissingImports]
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            shortcut_path = os.path.join(desktop, "Rose AI Assistant.lnk")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = os.path.abspath("rose_v30_refactored.py")
            shortcut.WorkingDirectory = os.getcwd()
            shortcut.IconLocation = sys.executable
            shortcut.save()
            
            print("✅ Desktop shortcut created")
        except ImportError:
            print("ℹ️  Install pywin32 to create desktop shortcuts: pip install pywin32")
        except Exception as e:
            print(f"⚠️  Could not create shortcut: {e}")

def main():
    """Main setup function"""
    print("🌹 Rose AI Assistant Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install requirements
    if not install_requirements():
        return False
    
    # Create configuration files
    create_config_file()
    create_env_template()
    
    # Check optional dependencies
    check_optional_dependencies()# Create shortcuts
    create_shortcuts()
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Copy .env.template to .env and add your API keys")
    print("2. Run: python rose_v30_refactored.py")
    print("3. Say 'help' to see all available commands")
    print("\nFor more help, visit the GitHub repository or say 'setup guide' in the app")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
