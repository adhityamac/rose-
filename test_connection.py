import requests

try:
    r = requests.get("https://google.com", timeout=5)
    print("Connection OK:", r.status_code)
except Exception as e:
    print("Connection failed:", e)
