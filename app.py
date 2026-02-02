from flask import Flask, render_template, request, jsonify
import webbrowser, datetime, os, re, time, subprocess, random
import pyautogui
import psutil
from plyer import notification
import requests
import ctypes

# 🔥 NEW IMPORTS (ADD ONLY)
import speech_recognition as sr
import threading

# =========================
# APP CONFIG
# =========================
app = Flask(__name__)

# =========================
# GLOBAL CONTEXT MEMORY 🧠
# =========================
assistant_state = {
    "current_site": None,
    "last_search": None,
    "youtube_playing": False,
    "listening": True,
    "notes": []
}

# =========================
# TEXT CLEANING
# =========================
def clean_text(text):
    return re.sub(r"[^a-z0-9\s]", "", text.lower())

# =========================
# INTENT DETECTION
# =========================
def detect_intent(text):
    if text.startswith("open"): return "open"
    if text.startswith("search"): return "search"
    if text.startswith("play"): return "play"
    if "pause" in text: return "pause"
    if "next" in text: return "next"
    if "open first" in text: return "open_first"
    if "time" in text: return "time"
    if "date" in text: return "date"
    if any(x in text for x in ["+", "-", "*", "/"]): return "math"
    if "volume up" in text: return "volume_up"
    if "volume down" in text: return "volume_down"
    if "mute" in text: return "mute"
    if "unmute" in text: return "unmute"
    if "brightness up" in text: return "brightness_up"
    if "brightness down" in text: return "brightness_down"
    if "screenshot" in text: return "screenshot"
    if "battery" in text: return "battery"
    if "shutdown" in text: return "shutdown"
    if "restart" in text: return "restart"
    if "lock" in text: return "lock"
    if "remind" in text: return "reminder"
    if "note" in text: return "note"
    if "read notes" in text: return "read_notes"
    if "weather" in text: return "weather"
    if "system info" in text: return "system_info"
    if "joke" in text: return "joke"
    if "stop listening" in text: return "stop"
    return "unknown"

# =========================
# ENTITY EXTRACTION
# =========================
def extract_entity(text):
    apps = [
        "youtube", "google", "gmail", "github", "chrome",
        "calculator", "notepad", "spotify", "amazon",
        "flipkart", "instagram", "facebook", "twitter",
        "linkedin", "netflix", "whatsapp web",
        "downloads", "documents"
    ]
    for app in apps:
        if app in text:
            return app
    return None

# =========================
# LOCAL OLLAMA AI
# =========================
def ask_ollama(prompt):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3", "prompt": prompt, "stream": False},
            timeout=30
        )
        return response.json().get("response", "")
    except:
        return "Local AI is not running."

# =========================
# ROUTES
# =========================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/command", methods=["POST"])
def command():
    if not assistant_state["listening"]:
        return jsonify({"reply": "Assistant stopped."})

    raw = request.json["text"]
    text = clean_text(raw)
    intent = detect_intent(text)
    entity = extract_entity(text)

    websites = {
        "youtube": "https://youtube.com",
        "google": "https://google.com",
        "gmail": "https://mail.google.com",
        "github": "https://github.com",
        "spotify": "https://open.spotify.com",
        "amazon": "https://amazon.in",
        "flipkart": "https://flipkart.com",
        "instagram": "https://instagram.com",
        "facebook": "https://facebook.com",
        "twitter": "https://twitter.com",
        "linkedin": "https://linkedin.com",
        "netflix": "https://netflix.com",
        "whatsapp web": "https://web.whatsapp.com"
    }

    if intent == "open" and entity:
        if entity in websites:
            webbrowser.open(websites[entity])
        elif entity == "downloads":
            os.startfile(os.path.join(os.environ["USERPROFILE"], "Downloads"))
        elif entity == "documents":
            os.startfile(os.path.join(os.environ["USERPROFILE"], "Documents"))
        return jsonify({"reply": f"{entity} opened."})

    if intent == "search":
        query = text.replace("search", "").strip()
        webbrowser.open(f"https://google.com/search?q={query}")
        return jsonify({"reply": f"Searching {query}."})

    if intent == "time":
        return jsonify({"reply": datetime.datetime.now().strftime("%I:%M %p")})

    if intent == "date":
        return jsonify({"reply": datetime.date.today().strftime("%d %B %Y")})

    if intent == "mute":
        pyautogui.press("volumemute")
        return jsonify({"reply": "Muted."})

    if intent == "unmute":
        pyautogui.press("volumemute")
        return jsonify({"reply": "Unmuted."})

    if intent == "lock":
        ctypes.windll.user32.LockWorkStation()
        return jsonify({"reply": "System locked."})

    if intent == "joke":
        return jsonify({"reply": random.choice([
            "Why do programmers hate nature? Too many bugs 😄",
            "AI won’t take your job, bad code will 😅"
        ])})

    if intent == "stop":
        assistant_state["listening"] = False
        return jsonify({"reply": "Assistant stopped listening."})

    ai_reply = ask_ollama(raw)
    return jsonify({"reply": ai_reply})

# =========================
# 🔊 WAKE WORD LISTENER (HEY AGENT) – ADD ONLY
# =========================
def wake_word_listener():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    recognizer.energy_threshold = 300
    recognizer.pause_threshold = 0.8

    print("🎧 Wake word active – say 'hey agent'")

    while True:
        try:
            with mic as source:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)

            text = recognizer.recognize_google(audio).lower()
            print("Heard:", text)

            if text.startswith("hey agent"):
                cmd = text.replace("hey agent", "").strip()

                if cmd:
                    requests.post(
                        "http://127.0.0.1:5000/command",
                        json={"text": cmd},
                        timeout=5
                    )
                    print("✅ Command sent:", cmd)

        except sr.WaitTimeoutError:
            pass   # silence – ignore

        except sr.UnknownValueError:
            pass   # noise – ignore

        except Exception as e:
            print("❌ Wake listener error:", e)
            time.sleep(1)

# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    t = threading.Thread(target=wake_word_listener, daemon=True)
    t.start()
    app.run(debug=True)
