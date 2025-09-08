import pyttsx3
import speech_recognition as sr
import pywhatkit
import wikipedia
import pyjokes

# --- Setup ---
listener = sr.Recognizer()
engine = pyttsx3.init()

def talk(text):
    engine.say(text)
    engine.runAndWait()

def listen():
    try:
        with sr.Microphone() as source:
            print("Listening...")
            voice = listener.listen(source)
            command = listener.recognize_google(voice)
            command = command.lower()
            if 'baby' in command:
                command = command.replace('baby', '')
                print(f"You said: {command}")
                return command
    except:
        return ""
    return ""

def run_baby():
    command = listen()
    if command:
        if 'play' in command:
            song = command.replace('play', '')
            talk(f"Playing {song}")
            pywhatkit.playonyt(song)
        elif 'wikipedia' in command:
            topic = command.replace('wikipedia', '')
            info = wikipedia.summary(topic, sentences=2)
            talk(info)
        elif 'joke' in command:
            talk(pyjokes.get_joke())
        elif 'hello' in command or 'hi' in command:
            talk("Hello Adhi, I am your Baby Assistant. How can I help?")
        elif 'stop' in command or 'bye' in command:
            talk("Goodbye Adhi!")
            exit()
        else:
            talk("Sorry, I didn't get that. Can you repeat?")
    run_baby()  # loop

# --- Start ---
talk("Baby is online and ready!")
run_baby()
