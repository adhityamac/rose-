import pyttsx3
import speech_recognition as sr
import pywhatkit
import wikipedia
import pyjokes
import os
import requests

# --- Setup ---
listener = sr.Recognizer()
engine = pyttsx3.init()

def talk(text):
    engine.say(text)
    engine.runAndWait()

def listen():
    try:
        with sr.Microphone() as source:
            listener.adjust_for_ambient_noise(source)  # Handle background noise
            print("Listening...")
            voice = listener.listen(source)
            command = listener.recognize_google(voice)
            command = command.lower()
            if 'baby' in command:
                command = command.replace('baby', '').strip()
                print(f"You said: {command}")
                return command
    except:
        return ""
    return ""

def get_weather(city):
    try:
        api_key = "your_openweathermap_api_key"  # optional for now
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url).json()
        temp = response['main']['temp']
        desc = response['weather'][0]['description']
        talk(f"The temperature in {city} is {temp}°C with {desc}")
    except:
        talk("Sorry, I cannot fetch the weather right now.")

def open_app(app_name):
    app_name = app_name.lower()
    if "chrome" in app_name:
        os.startfile("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
    elif "vscode" in app_name:
        os.startfile("C:\\Users\\YourUsername\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe")
    elif "calculator" in app_name:
        os.system("calc")
    else:
        talk("App not found on this PC.")

def run_baby():
    command = listen()
    if command:
        if 'play' in command:
            song = command.replace('play', '').strip()
            if song:
                talk(f"Playing {song}")
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
        elif 'weather' in command:
            city = command.replace('weather', '').strip()
            if city:
                get_weather(city)
            else:
                talk("Please tell me the city name.")
        elif 'hello' in command or 'hi' in command:
            talk("Hello Adhi, I am Baby. How can I help?")
        elif 'stop' in command or 'bye' in command:
            talk("Goodbye Adhi!")
            exit()
        else:
            talk("Sorry, I didn't get that. Can you repeat?")
    run_baby()  # loop

# --- Start ---
talk("Baby v2.1 is online and ready!")
run_baby()
