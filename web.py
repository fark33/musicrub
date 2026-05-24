# web.py
from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def health_check():
    # پاسخ ساده به Koyeb برای تأیید سلامتی
    return "OK", 200

def run_web_server():
    # اطمینان از گوش دادن به تمام اینترفیس‌های شبکه
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)

def start():
    server = Thread(target=run_web_server)
    server.daemon = True  # با بسته شدن برنامه اصلی، این thread هم بسته می‌شود
    server.start()
