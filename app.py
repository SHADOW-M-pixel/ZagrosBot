from flask import Flask, request
import threading
import main  # این فایل، همون main.py خودمونه

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Web Server is Running!"

# این بخش بعداً برای زرین‌پال استفاده میشه
@app.route('/verify-payment')
def verify_payment():
    # فعلاً یه پیام ساده برمی‌گردونه
    return "Payment Verification Page"

# اجرای ربات تلگرام در یک ترد (Thread) جداگانه
def run_bot():
    main.main()

if __name__ == "__main__":
    # ربات رو توی پس‌زمینه روشن کن
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    # وب‌سرور رو روی پورت 8080 روشن کن
    app.run(host="0.0.0.0", port=8080)