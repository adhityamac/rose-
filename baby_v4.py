import pyttsx3
import speech_recognition as sr
import pywhatkit
import wikipedia
import pyjokes
import os
import requests
import tkinter as tk
from threading import Thread
import time

# ---------------- Setup ----------------
listener = sr.Recognizer()
engine = pyttsx3.init()
ZAI_API_KEY = "YOUR_ZAI_API_KEY"  # replace with your Z.ai key

# ---------------- Functions ----------------
def talk(text):
    hud_text.insert(tk.END, f"Baby: {text}\n")
    hud_text.see(tk.END)
    engine.say(text)
    engine.runAndWait()

def listen():
    try:
        with sr.Microphone() as source:
            listener.adjust_for_ambient_noise(source)
            voice = listener.listen(source, timeout=5, phrase_time_limit=7)
            command = listener.recognize_google(voice).lower()
            if command:
                hud_text.insert(tk.END, f"You said: {command}\n")
                hud_text.see(tk.END)
                return command
    except Exception as e:
        hud_text.insert(tk.END, f"Listen Error: {e}\n")
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
        talk("App not found.")

def ask_zai(question):
    try:
        url = "https://z.ai/api/chat"
        headers = {
            "Authorization": f"Bearer {ZAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {"messages": [{"role": "user", "content": question}]}
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return "Error: Unable to get answer from Z.ai."
    except Exception as e:
        return f"Error: {e}"

def process_command(command):
    command = command.lower()
    if 'play' in command:
        song = command.replace('play', '').strip()
        if song:
            talk(f"Playing {song} on YouTube")
            pywhatkit.playonyt(song)
    elif 'wikipedia' in command:
        topic = command.replace('wikipedia', '').strip()
        if topic:
            info = wikipedia.summary(topic, sentences=2)
            talk(info)
    elif 'joke' in command:
        talk(pyjokes.get_joke())
    elif 'open' in command:
        app = command.replace('open', '').strip()
        if app:
            open_app(app)
    elif 'stop' in command or 'bye' in command:
        talk("Goodbye! Exiting...")
        root.quit()
        exit()
    else:
        answer = ask_zai(command)
        talk(answer)

def baby_loop():
    while True:
        cmd = listen()
        if cmd:
            process_command(cmd)
        time.sleep(0.5)

def start_baby_thread():
    Thread(target=baby_loop, daemon=True).start()

# ---------------- HUD ----------------
root = tk.Tk()
root.title("Baby HUD")
root.geometry("350x250")
root.configure(bg="black")
root.attributes("-topmost", True)

hud_text = tk.Text(root, bg="black", fg="lime", font=("Consolas", 10))
hud_text.pack(expand=True, fill='both')

exit_button = tk.Button(root, text="Exit", command=lambda: root.quit())
exit_button.pack(side='bottom', fill='x')

talk("Baby v4 online. Listening always...")
start_baby_thread()
root.mainloop()
