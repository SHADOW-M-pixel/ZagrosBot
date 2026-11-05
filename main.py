import io
import os
import urllib.request
import qrcode
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from database import (
    init_db, add_user, is_subscribed, check_and_update_qr_limit
)
import instaloader
import yt_dlp
import google.generativeai as genai

# ============ تنظیمات ============
BOT_TOKEN = "9034441691:AAGXKjJp1KnAJf4iwyonJHg65CvLpiDSu6M"
# کلید API هوش مصنوعی (بعداً باید از سایت گوگل بگیری، فعلاً خالی بذار)
GEMINI_API_KEY = "" 
# ==================================

# تنظیمات پروکسی سیستم
def setup_proxy():
    try:
        proxies = urllib.request.getproxies()
        if 'https' in proxies:
            os.environ['HTTP_PROXY'] = proxies['https']
            os.environ['HTTPS_PROXY'] = proxies['https']
            print(f"✅ پروکسی سیستم: {proxies['https']}")
    except:
        pass

setup_proxy()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username or "")
    
    keyboard = [
        [InlineKeyboardButton("🔳 ساخت QR Code", callback_data="qr")],
        [InlineKeyboardButton("📥 دانلود اینستاگرام", callback_data="insta")],
        [InlineKeyboardButton("📺 دانلود یوتیوب", callback_data="yt")],
        [InlineKeyboardButton("🤖 چت با هوش مصنوعی", callback_data="ai")],
        [InlineKeyboardButton("🖼 عکس به PDF", callback_data="pdf")],
        [InlineKeyboardButton("💎 خرید اشتراک", callback_data="buy")],
        [InlineKeyboardButton("📊 وضعیت اشتراک", callback_data="status")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"سلام {user.first_name}! 👋\nبه سوپر ربات زاگرس خوش اومدی.\nاز منوی زیر انتخاب کن:"
    await update.message.reply_text(text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    context.user_data["awaiting"] = None
    
    if data == "qr":
        context.user_data["awaiting"] = "qr"
        await query.edit_message_text("متن یا لینک برای ساخت QR رو بفرست:")
    elif data == "insta":
        context.user_data["awaiting"] = "insta"
        await query.edit_message_text("لینک پست اینستاگرام رو بفرست:")
    elif data == "yt":
        context.user_data["awaiting"] = "yt"
        await query.edit_message_text("لینک ویدیوی یوتیوب رو بفرست:")
    elif data == "ai":
        context.user_data["awaiting"] = "ai"
        await query.edit_message_text("سوالت رو بپرس تا هوش مصنوعی جواب بده:")
    elif data == "pdf":
        context.user_data["awaiting"] = "pdf"
        await query.edit_message_text("عکس رو بفرست تا به PDF تبدیل کنم:")
    elif data == "buy":
        await query.edit_message_text("💎 اشتراک ماهانه: ۵۰,۰۰۰ تومان\n\nدرگاه پرداخت هنوز متصل نشده.")
    elif data == "status":
        if is_subscribed(query.from_user.id):
            await query.edit_message_text("✅ اشتراک فعال داری.")
        else:
            await query.edit_message_text("❌ اشتراک فعال نداری. نسخه رایگان: روزی ۳ بار.")
    elif data == "back":
        await start(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    awaiting = context.user_data.get("awaiting")
    if not awaiting: return
    
    user_id = update.effective_user.id
    if not check_and_update_qr_limit(user_id):
        await update.message.reply_text("⛔ محدودیت روزانه نسخه رایگان پر شده. اشتراک بخر.")
        context.user_data["awaiting"] = None
        return
    
    if awaiting == "qr":
        text = update.message.text
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        await update.message.reply_photo(photo=buffer, caption="✅ QR شما آماده‌ست!")
        context.user_data["awaiting"] = None

    elif awaiting == "insta":
        url = update.message.text
        msg = await update.message.reply_text("⏳ در حال دانلود از اینستاگرام...")
        try:
            L = instaloader.Instaloader()
            shortcode = url.split("/")[-2]
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            if post.typename == "GraphImage":
                img_bytes = io.BytesIO()
                L.download_pic(img_bytes, post.url, post.date_utc)
                img_bytes.seek(0)
                await update.message.reply_photo(photo=img_bytes, caption="✅ دانلود شد.")
            else:
                await update.message.reply_text("فعلاً فقط عکس پشتیبانی می‌شود.")
        except:
            await update.message.reply_text("❌ خطا در دانلود. لینک را چک کنید.")
        await msg.delete()
        context.user_data["awaiting"] = None

    elif awaiting == "yt":
        url = update.message.text
        msg = await update.message.reply_text("⏳ در حال دانلود از یوتیوب (ممکن است کمی طول بکشد)...")
        try:
            ydl_opts = {'format': 'best[ext=mp4]', 'outtmpl': f'yt_{user_id}.mp4'}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # ارسال ویدیو
            await update.message.reply_video(video=open(f'yt_{user_id}.mp4', 'rb'), caption="✅ دانلود شد.")
            os.remove(f'yt_{user_id}.mp4') # پاک کردن فایل
        except Exception as e:
            print(e)
            await update.message.reply_text("❌ خطا در دانلود یوتیوب. لینک را چک کنید.")
        await msg.delete()
        context.user_data["awaiting"] = None

    elif awaiting == "ai":
        prompt = update.message.text
        msg = await update.message.reply_text("🤖 در حال فکر کردن...")
        try:
            if not GEMINI_API_KEY:
                await update.message.reply_text("❌ کلید API هوش مصنوعی تنظیم نشده است.")
            else:
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)
                await update.message.reply_text(response.text)
        except Exception as e:
            await update.message.reply_text("❌ خطا در ارتباط با هوش مصنوعی.")
        await msg.delete()
        context.user_data["awaiting"] = None

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting") != "pdf": return
    user_id = update.effective_user.id
    if not check_and_update_qr_limit(user_id):
        await update.message.reply_text("⛔ محدودیت پر شده.")
        context.user_data["awaiting"] = None
        return
    msg = await update.message.reply_text("⏳ در حال تبدیل...")
    try:
        photo_file = await update.message.photo[-1].get_file()
        img_bytes = io.BytesIO()
        await photo_file.download_to_memory(img_bytes)
        img_bytes.seek(0)
        img = Image.open(img_bytes)
        pdf_bytes = io.BytesIO()
        img.convert('RGB').save(pdf_bytes, format="PDF")
        pdf_bytes.seek(0)
        await update.message.reply_document(document=pdf_bytes, filename=f"image_{user_id}.pdf", caption="✅ PDF آماده شد.")
    except Exception as e:
        await update.message.reply_text("❌ خطا در تبدیل.")
    await msg.delete()
    context.user_data["awaiting"] = None

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).connect_timeout(30.0).read_timeout(30.0).write_timeout(30.0).pool_timeout(30.0).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()