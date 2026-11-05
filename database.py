import sqlite3
from datetime import datetime, timedelta

DB_NAME = "bot.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            expire_date TEXT,
            daily_qr_count INTEGER DEFAULT 0,
            last_qr_date TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def add_user(user_id, username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def is_subscribed(user_id):
    row = get_user(user_id)
    if not row or not row[2]: # row[2] is expire_date
        return False
    try:
        expire = datetime.fromisoformat(row[2])
        return expire > datetime.now()
    except:
        return False

def activate_subscription(user_id, days=30):
    expire = (datetime.now() + timedelta(days=days)).isoformat()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET expire_date = ? WHERE user_id = ?", (expire, user_id))
    conn.commit()
    conn.close()

def check_and_update_qr_limit(user_id, free_limit=3):
    """بررسی محدودیت روزانه. True برگردونه یعنی مجاز، False یعنی محدود شده."""
    row = get_user(user_id)
    if not row:
        return True
    today = datetime.now().date().isoformat()
    last_date = row[4] # row[4] is last_qr_date
    count = row[3] or 0 # row[3] is daily_qr_count

    if last_date != today:
        count = 0
        last_date = today

    if count >= free_limit and not is_subscribed(user_id):
        return False

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET daily_qr_count = ?, last_qr_date = ? WHERE user_id = ?",
              (count + 1, last_date, user_id))
    conn.commit()
    conn.close()
    return True