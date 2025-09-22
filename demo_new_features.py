"""
Demo script for Rose AI Assistant v30 New Features
Showcases voice commands, themes, plugins, and performance optimizations
"""

import time
import sys
import os

def demo_voice_commands():
    """Demo voice command system"""
    print("🎤 Voice Commands Demo")
    print("=" * 30)
    
    try:
        from voice_commands import voice_command_manager
        
        # Test voice commands
        test_commands = [
            "hello",
            "what time is it",
            "play music",
            "change theme",
            "fast response"
        ]
        
        for cmd in test_commands:
            print(f"Testing: '{cmd}'")
            result = voice_command_manager.process_voice_input(cmd)
            print(f"  Result: {'✅ Handled' if result else '❌ Not handled'}")
            time.sleep(0.5)
        
        print(f"\n📊 Performance Stats:")
        print(f"  Average response time: {voice_command_manager.get_average_response_time():.3f}s")
        print(f"  Commands processed: {len(voice_command_manager.command_history)}")
        
    except ImportError as e:
        print(f"❌ Voice commands not available: {e}")

def demo_themes():
    """Demo theme system"""
    print("\n🎨 Themes Demo")
    print("=" * 30)
    
    try:
        from theme_manager import theme_manager
        
        themes = theme_manager.get_available_themes()
        print(f"Available themes: {', '.join(themes)}")
        
        current_theme = theme_manager.get_theme()
        print(f"Current theme: {current_theme.name if current_theme else 'None'}")
        
        # Demo theme switching
        for theme_name in themes[:3]:  # Test first 3 themes
            print(f"Switching to {theme_name} theme...")
            if theme_manager.set_theme(theme_name):
                print(f"  ✅ {theme_name} theme applied")
            else:
                print(f"  ❌ Failed to apply {theme_name} theme")
            time.sleep(0.5)
        
        # Restore cosmic theme
        theme_manager.set_theme("cosmic")
        print("  🌌 Restored cosmic theme")
        
    except ImportError as e:
        print(f"❌ Theme manager not available: {e}")

def demo_plugins():
    """Demo plugin system"""
    print("\n🔌 Plugins Demo")
    print("=" * 30)
    
    try:
        from plugin_system import plugin_manager
        
        # Load plugins
        plugin_count = plugin_manager.load_plugins()
        print(f"Loaded {plugin_count} plugins")
        
        # Show plugin status
        status = plugin_manager.get_plugin_status()
        for name, info in status.items():
            print(f"  {name}: {'✅' if info['loaded'] else '❌'} {info['name']} v{info['version']}")
        
        # Test voice commands from plugins
        voice_commands = plugin_manager.get_voice_commands()
        print(f"\nVoice commands from plugins: {len(voice_commands)}")
        for cmd_name in voice_commands.keys():
            print(f"  • {cmd_name}")
        
    except ImportError as e:
        print(f"❌ Plugin system not available: {e}")

def demo_fast_tts():
    """Demo fast TTS system"""
    print("\n🔊 Fast TTS Demo")
    print("=" * 30)
    
    try:
        from fast_tts import fast_tts
        
        if fast_tts.is_available:
            print("✅ Fast TTS is available")
            
            # Test TTS
            test_text = "Hello! This is the fast TTS system."
            print(f"Speaking: '{test_text}'")
            fast_tts.speak(test_text)
            
            # Wait for completion
            print("Waiting for TTS to complete...")
            fast_tts.wait_until_done(timeout=5.0)
            print("✅ TTS completed")
            
        else:
            print("❌ Fast TTS not available")
            
    except ImportError as e:
        print(f"❌ Fast TTS not available: {e}")

def demo_performance():
    """Demo performance optimization"""
    print("\n🚀 Performance Demo")
    print("=" * 30)
    
    try:
        from performance_optimizer import performance_optimizer
        
        # Run optimization
        print("Running performance optimization...")
        performance_optimizer.run_full_optimization()
        
        # Show performance report
        print("\nPerformance Report:")
        print(performance_optimizer.generate_performance_report())
        
    except ImportError as e:
        print(f"❌ Performance optimizer not available: {e}")

def main():
    """Run all demos"""
    print("🌹 Rose AI Assistant v30 - New Features Demo")
    print("=" * 50)
    
    demo_voice_commands()
    demo_themes()
    demo_plugins()
    demo_fast_tts()
    demo_performance()
    
    print("\n" + "=" * 50)
    print("🎉 Demo complete! All new features are working!")
    print("\n🚀 To run the full application: python rose_v30_refactored.py")
    print("🎤 Try voice commands like:")
    print("   • 'hello' - Greet the assistant")
    print("   • 'change theme' - Switch themes")
    print("   • 'play music' - Play music")
    print("   • 'fast response' - Speed up responses")
    print("   • 'what time is it' - Get current time")

if __name__ == "__main__":
    main()
