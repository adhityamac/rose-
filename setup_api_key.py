"""
Simple API Key Setup Script for Rose AI Assistant
"""

import os
import sys

def setup_api_key():
    print("🌹 Rose AI Assistant - API Key Setup")
    print("=" * 40)
    
    print("\nTo get your Gemini API key:")
    print("1. Go to: https://makersuite.google.com/app/apikey")
    print("2. Sign in with your Google account")
    print("3. Create a new API key")
    print("4. Copy the key (starts with 'AIzaSyB...')")
    
    print("\nChoose setup method:")
    print("1. Add API key directly to config.py")
    print("2. Create .env file")
    print("3. Set environment variable")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        api_key = input("\nEnter your Gemini API key: ").strip()
        if api_key:
            # Update config.py
            try:
                with open("config.py", "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Replace the empty string with the API key
                content = content.replace(
                    'GEMINI_API_KEY_DIRECT = ""',
                    f'GEMINI_API_KEY_DIRECT = "{api_key}"'
                )
                
                with open("config.py", "w", encoding="utf-8") as f:
                    f.write(content)
                
                print("✅ API key added to config.py")
                print("You can now run: python rose_v30_refactored.py")
                
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print("❌ No API key provided")
    
    elif choice == "2":
        api_key = input("\nEnter your Gemini API key: ").strip()
        if api_key:
            try:
                with open(".env", "w", encoding="utf-8") as f:
                    f.write(f"GEMINI_API_KEY={api_key}\n")
                print("✅ .env file created with API key")
                print("You can now run: python rose_v30_refactored.py")
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print("❌ No API key provided")
    
    elif choice == "3":
        print("\nTo set environment variable:")
        print("Windows: set GEMINI_API_KEY=your_api_key_here")
        print("Linux/Mac: export GEMINI_API_KEY=your_api_key_here")
        print("\nThen run: python rose_v30_refactored.py")
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    setup_api_key()
