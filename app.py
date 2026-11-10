from flask import Flask
import threading
import main

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Web Server is Running!"

# وب‌سرور Flask رو در یک ترد جداگانه اجرا می‌کنیم (چون به Signal نیاز نداره)
def run_flask():
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    # وب‌سرور رو در پس‌زمینه (Daemon) روشن می‌کنیم
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # ربات تلگرام رو در ترد اصلی (Main Thread) اجرا می‌کنیم
    main.main()
