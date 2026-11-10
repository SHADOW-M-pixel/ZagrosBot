from flask import Flask
import threading
import main

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Web Server is Running!"

def run_bot():
    # این خط دقیقاً همون کاری رو می‌کنه که main.py میکرد
    main.main()

if name == "__main__":
    # اجرای ربات در یک ترد جداگانه
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    # اجرای وب‌سرور در ترد اصلی (که باعث میشه برنامه زنده بمونه)
    app.run(host="0.0.0.0", port=8080)