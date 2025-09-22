# 🌹 Rose AI Assistant v30

A comprehensive, modular AI assistant for your PC with advanced features including voice recognition, mood tracking, media integration, and creative tools.

## ✨ Features

### 🎤 Voice & Speech
- **Voice Recognition**: Hands-free interaction using Google Speech Recognition
- **Text-to-Speech**: Natural voice responses with Edge TTS
- **Multi-language Support**: 10+ languages with appropriate voices
- **Personality Customization**: Adjustable AI personality traits

### 😊 Mood & Wellness
- **Mood Analysis**: Real-time sentiment analysis using VADER
- **Mood Tracking**: Visual mood charts and temperature indicators
- **Emoji Analysis**: Pattern recognition in emoji usage
- **Journal Integration**: AI-powered journaling with insights
- **Proactive Support**: Mood-based suggestions and check-ins

### 🎵 Media & Music
- **YouTube Integration**: Search and play music directly
- **Spotify Controls**: Play, pause, skip, previous track
- **Music Taste Learning**: Personalized recommendations
- **Mood-based Playlists**: Automatic playlist generation
- **Multi-platform Support**: Apple Music, SoundCloud integration
- **Audio Visualization**: Built-in visualizer links

### 📊 Productivity Tools
- **Smart Reminders**: Location-aware reminder system
- **Habit Tracking**: Streak counting and progress monitoring
- **Time Tracking**: Project-based time management
- **Calendar Export**: ICS format export functionality
- **CSV Export**: Data export for external tools

### 🎨 Creative Features
- **Word Cloud Generation**: Visual conversation analysis
- **Theme Extraction**: Color palette extraction from images
- **Document Analysis**: PDF and image analysis with AI
- **Screen Analysis**: Real-time screen content analysis
- **Interactive Storytelling**: AI-generated stories
- **Data Visualizations**: Mood charts and summaries

### 🔧 System Integration
- **Volume Control**: Smart volume adjustment
- **Weather Integration**: Real-time weather data
- **News Headlines**: Latest news updates
- **Browser Control**: Launch and control browsers
- **File Management**: Document upload and analysis
- **Gesture Recognition**: Basic hand gesture support

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Windows 10/11, macOS, or Linux
- Microphone (for voice features)
- Internet connection (for AI features)

### Installation

1. **Clone or download** the repository
2. **Run the setup script**:
   ```bash
   python setup.py
   ```
3. **Configure API keys** (optional but recommended):
   - Copy `.env.template` to `.env`
   - Add your API keys (see Configuration section)

4. **Launch the application**:
   ```bash
   python rose_v30_refactored.py
   ```

### First Use
1. Say **"hello"** to test voice recognition
2. Try **"help"** to see all available commands
3. Use **"show my mood"** to test mood tracking
4. Say **"play music on youtube"** to test media features

## ⚙️ Configuration

### API Keys (Optional)
Add these to your `.env` file for enhanced features:

```env
# AI Services
ROSE_GEMINI_API_KEY=your_gemini_api_key_here

# Weather Service
ROSE_OPENWEATHER_API_KEY=your_openweather_api_key_here

# News Service
ROSE_NEWSAPI_API_KEY=your_newsapi_key_here

# Email Service
ROSE_EMAIL_USER=your_email@example.com
ROSE_EMAIL_PASS=your_email_password
```

### Configuration File
The app creates `rose_config.json` for settings:
- UI colors and themes
- Feature toggles
- Language preferences
- Window settings

## 🎯 Commands

### Voice & Speech
- `"hello"` - Greet Rose
- `"speak in [language]"` - Change language
- `"set personality [type]"` - Change personality

### Mood & Wellness
- `"show my mood"` - Display mood chart
- `"mood temperature"` - Show mood as temperature
- `"write journal [entry]"` - Add journal entry
- `"analyze emojis"` - Analyze emoji usage

### Media & Music
- `"play [song] on youtube"` - Play music
- `"spotify play"` - Control Spotify
- `"suggest song"` - Get music recommendation
- `"mood playlist"` - Create mood-based playlist

### Productivity
- `"remind me to [task]"` - Add reminder
- `"add habit [habit]"` - Track new habit
- `"start tracking [project]"` - Time tracking
- `"export calendar"` - Export to calendar

### System Control
- `"volume up/down"` - Control volume
- `"weather in [city]"` - Get weather
- `"news"` - Get headlines
- `"open browser"` - Launch browser

### Creative Features
- `"word cloud"` - Generate word cloud
- `"change theme from image"` - Extract colors
- `"upload document"` - Analyze file
- `"tell a story [topic]"` - Interactive story

### Help
- `"help"` - Show general help
- `"commands"` - List all commands
- `"help [category]"` - Category-specific help
- `"what can you do"` - Show capabilities

## 🏗️ Architecture

The application is built with a modular architecture:

```
rose_v30_refactored.py    # Main application
├── config.py             # Configuration management
├── error_handler.py      # Error handling and logging
├── help_system.py        # Help and command system
├── ai_services.py        # AI and language processing
├── media_services.py     # Media and TTS services
└── requirements.txt      # Dependencies
```

### Key Components

- **ConfigManager**: Centralized configuration with environment variable support
- **ErrorHandler**: Comprehensive error handling with user-friendly messages
- **HelpSystem**: Command discovery and user guidance
- **GeminiService**: AI integration with conversation context
- **MoodAnalyzer**: Sentiment analysis and mood tracking
- **TTSService**: Text-to-speech with language support
- **MusicService**: Multi-platform music integration

## 🔧 Development

### Adding New Features

1. **Create a new service module** (e.g., `new_feature_service.py`)
2. **Add configuration options** in `config.py`
3. **Implement error handling** using `error_handler_instance`
4. **Add commands** to `help_system.py`
5. **Integrate** into main application

### Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Include comprehensive error handling
- Add logging for debugging
- Write user-friendly error messages

## 🐛 Troubleshooting

### Common Issues

**Voice recognition not working:**
- Check microphone permissions
- Install speech_recognition: `pip install speech_recognition`
- Try different microphone in system settings

**TTS not working:**
- Install edge-tts: `pip install edge-tts`
- Check audio output device
- Verify internet connection

**AI features not responding:**
- Configure Gemini API key in `.env` file
- Check internet connection
- Verify API key validity

**UI not displaying properly:**
- Install PySide6: `pip install PySide6`
- Check display scaling settings
- Try running as administrator

### Logs

Check `rose_errors.log` for detailed error information.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Google** for Speech Recognition and Gemini AI
- **Microsoft** for Edge TTS
- **PySide6** for the GUI framework
- **VADER** for sentiment analysis
- **All contributors** and the open-source community

## 📞 Support

- **Documentation**: Check this README and in-app help
- **Issues**: Report bugs on GitHub
- **Discussions**: Join community discussions
- **Email**: Contact the maintainers

---

**Made with ❤️ by the Rose AI Team**

*"Your personal AI assistant for a more connected and productive digital life."*
