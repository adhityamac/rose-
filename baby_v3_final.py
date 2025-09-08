import pyttsx3
import speech_recognition as sr
import pywhatkit
import wikipedia
import pyjokes
import os
import openai
import time

# --- Setup ---
listener = sr.Recognizer()
engine = pyttsx3.init()
openai.api_key = "ab99ac8a4ec34990a8093b337bf6b7be.wczwJ41HzsTog3h2"  

def talk(text):
    print(f"Baby says: {text}")
    engine.say(text)
    engine.runAndWait()

def listen():
    try:
        with sr.Microphone() as source:
            listener.adjust_for_ambient_noise(source)
            print("Listening...")
            voice = listener.listen(source, timeout=5, phrase_time_limit=7)
            command = listener.recognize_google(voice)
            command = command.lower()
            if 'baby' in command:
                command = command.replace('baby', '').strip()
                print(f"You said: {command}")
                return command
    except Exception as e:
        print(f"Listen Error: {e}")
        return ""
    return ""

def open_app(app_name):
    app_name = app_name.lower()
    if "chrome" in app_name:
        os.startfile("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
    elif "vscode" in app_name:
        os.startfile("C:\\Users\\Adhi\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe")
    elif "calculator" in app_name:
        os.system("calc")
    else:
        talk("App not found on this PC.")

def ask_chatgpt(question):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": question}]
        )
        answer = response['choices'][0]['message']['content']
        return answer
    except Exception as e:
        print(f"ChatGPT Error: {e}")
        return "Sorry, I cannot answer that right now."

def run_baby():
    command = listen()
    if command:
        if 'play' in command:
            song = command.replace('play', '').strip()
            if song:
                talk(f"Playing {song} on YouTube")
                pywhatkit.playonyt(song)
            else:
                talk("Please tell me the song name.")
        elif 'wikipedia' in command:
            topic = command.replace('wikipedia', '').strip()
            if topic:
                info = wikipedia.summary(topic, sentences=2)
                talk(info)
            else:
                talk("Please tell me the topic.")
        elif 'joke' in command:
            talk(pyjokes.get_joke())
        elif 'open' in command:
            app = command.replace('open', '').strip()
            if app:
                open_app(app)
            else:
                talk("Please tell me which app to open.")
        elif 'stop' in command or 'bye' in command:
            talk("Goodbye Adhi!")
            exit()
        else:
            # Anything else goes to ChatGPT
            answer = ask_chatgpt(command)
            talk(answer)
    time.sleep(0.5)
    run_baby()

# --- Start ---
talk("Baby v3 is online and ready to assist you!")
run_baby()
