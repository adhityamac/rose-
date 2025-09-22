"""
Python Library Cleanup Script for Rose AI Assistant
Identifies and removes unnecessary libraries
"""

import subprocess
import sys

# Required libraries for Rose AI Assistant
REQUIRED_LIBRARIES = {
    'PySide6',           # GUI framework
    'requests',          # HTTP requests
    'SpeechRecognition', # Voice recognition
    'edge-tts',          # Text-to-speech
    'pytube',            # YouTube integration
    'vaderSentiment',    # Mood analysis
    'matplotlib',        # Data visualization
    'wordcloud',         # Word cloud generation
    'colorthief',        # Color extraction
    'opencv-python',     # Computer vision
    'mediapipe',         # Gesture recognition
    'PyPDF2',            # PDF processing
    'pyautogui',         # Screen capture
    'icalendar',         # Calendar export
    'geopy',             # Location services
    'emoji',             # Emoji processing
    'google-generativeai', # Gemini AI
    'google-api-python-client', # Google APIs
    'google-auth',       # Google authentication
    'google-auth-httplib2', # Google auth HTTP
    'googleapis-common-protos', # Google protobuf
    'grpcio',            # gRPC for Google APIs
    'grpcio-status',     # gRPC status
    'protobuf',          # Protocol buffers
    'proto-plus',        # Protocol buffer utilities
    'cachetools',        # Caching utilities
    'certifi',           # SSL certificates
    'charset-normalizer', # Character encoding
    'urllib3',           # HTTP library
    'six',               # Python 2/3 compatibility
    'setuptools',        # Package management
    'pip',               # Package installer
    'packaging',         # Package utilities
    'typing_extensions', # Type hints
    'pydantic',          # Data validation
    'pydantic_core',     # Pydantic core
    'annotated-types',   # Type annotations
    'tzdata',            # Timezone data
    'tzlocal',           # Local timezone
    'sniffio',           # Async library detection
    'anyio',             # Async utilities
    'h11',               # HTTP/1.1 protocol
    'httpcore',          # HTTP core
    'httpx',             # HTTP client
    'idna',              # Internationalized domain names
    'click',             # Command line interface
    'colorama',          # Cross-platform colored terminal
    'python-dotenv',     # Environment variables
    'pillow',            # Image processing
    'beautifulsoup4',    # HTML parsing
    'soupsieve',         # CSS selectors
    'blinker',           # Signal system
    'cffi',              # C Foreign Function Interface
    'pycparser',         # C parser
    'pyasn1',            # ASN.1 library
    'pyasn1_modules',    # ASN.1 modules
    'rsa',               # RSA encryption
    'uritemplate',       # URI template
    'tenacity',          # Retry library
    'tqdm',              # Progress bars
    'websockets',        # WebSocket client
    'vosk',              # Speech recognition
    'srt',               # Subtitle processing
    'pyjokes',           # Joke library
    'wikipedia',         # Wikipedia API
    'pywhatkit',         # WhatsApp automation
    'pyttsx3',           # Text-to-speech
    'pySmartDL',         # Download manager
    'pyjsparser',        # JavaScript parser
    'Js2Py',             # JavaScript to Python
    'MouseInfo',         # Mouse information
    'PyGetWindow',       # Window management
    'PyMsgBox',          # Message boxes
    'PyRect',            # Rectangle utilities
    'PyScreeze',         # Screenshot utilities
    'pytweening',        # Animation tweening
    'PyPrind',           # Progress indicators
    'pyperclip',         # Clipboard access
    'pywin32',           # Windows API
    'pywin32-ctypes',    # Windows API ctypes
    'pypiwin32',         # Windows utilities
    'comtypes',          # COM types
    'pefile',            # PE file parser
    'altgraph',          # Graph algorithms
    'pyinstaller',       # Executable creator
    'pyinstaller-hooks-contrib', # PyInstaller hooks
    'docopt',            # Command line parser
    'Flask',             # Web framework
    'Jinja2',            # Template engine
    'MarkupSafe',        # Safe markup
    'Werkzeug',          # WSGI utilities
    'itsdangerous',      # Secure data serialization
    'httplib2',          # HTTP library
    'google-ai-generativelanguage', # Google AI
    'google-api-core',   # Google API core
    'google-genai',      # Google Generative AI
    'typing-inspection', # Type inspection
}

def get_installed_packages():
    """Get list of installed packages"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format=freeze'], 
                              capture_output=True, text=True)
        packages = {}
        for line in result.stdout.strip().split('\n'):
            if '==' in line:
                name, version = line.split('==', 1)
                packages[name.lower()] = version
        return packages
    except Exception as e:
        print(f"Error getting installed packages: {e}")
        return {}

def identify_unnecessary_packages():
    """Identify packages that are not required"""
    installed = get_installed_packages()
    unnecessary = []
    
    for package in installed:
        if package.lower() not in [lib.lower() for lib in REQUIRED_LIBRARIES]:
            unnecessary.append((package, installed[package]))
    
    return unnecessary

def uninstall_packages(packages):
    """Uninstall specified packages"""
    for package, version in packages:
        try:
            print(f"Uninstalling {package}...")
            subprocess.run([sys.executable, '-m', 'pip', 'uninstall', package, '-y'], 
                         check=True)
            print(f"✅ Uninstalled {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to uninstall {package}: {e}")
        except Exception as e:
            print(f"❌ Error uninstalling {package}: {e}")

def main():
    print("🧹 Rose AI Assistant - Library Cleanup")
    print("=" * 50)
    
    print("\n📋 Scanning installed packages...")
    unnecessary = identify_unnecessary_packages()
    
    if not unnecessary:
        print("✅ All installed packages are required for Rose AI Assistant!")
        return
    
    print(f"\n📦 Found {len(unnecessary)} potentially unnecessary packages:")
    print("-" * 50)
    
    for i, (package, version) in enumerate(unnecessary, 1):
        print(f"{i:2d}. {package} (v{version})")
    
    print("\n⚠️  WARNING: This will uninstall the packages listed above.")
    print("Make sure you don't need them for other projects!")
    
    choice = input("\nDo you want to proceed? (y/N): ").strip().lower()
    
    if choice in ['y', 'yes']:
        print("\n🗑️  Uninstalling unnecessary packages...")
        uninstall_packages(unnecessary)
        print("\n✅ Cleanup completed!")
    else:
        print("\n❌ Cleanup cancelled.")

if __name__ == "__main__":
    main()
