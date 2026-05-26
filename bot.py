import os
import re
import random
import asyncio
import threading
from flask import Flask, jsonify
from rubka import Robot, context
from responses import handcrafted_responses, get_random_response
from question import questions

# -------------------- Flask Health Check --------------------
app = Flask(__name__)

@app.route('/')
def health_check():
    return jsonify({'status': 'ok'})

def run_flask():
    app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)

# -------------------- توابع کمکی ربات --------------------
def normalize_text(text: str) -> str:
    """حذف کاراکترهای تکراری (بیش از ۲ بار) و حذف فاصله اضافی"""
    if not isinstance(text, str):
        return ""
    text = re.sub(r'(.)\1{2,}', r'\1\1', text)
    return text.strip()

def get_response(user_message: str):
    """پیدا کردن پاسخ مناسب از دیکشنری دستی"""
    if not user_message:
        return None
    msg_norm = normalize_text(user_message)

    # تطابق دقیق
    for key, resp in handcrafted_responses.items():
        if normalize_text(key) == msg_norm:
            return get_random_response(resp)

    # تطابق جزئی (کلمه درون پیام)
    for key, resp in handcrafted_responses.items():
        if key in msg_norm or msg_norm in key:
            return get_random_response(resp)

    # الگوهای خداحافظی
    farewell_patterns = [
        (r'خدانگهدار+', "خدانگهدار عزیزم، دلم برات تنگ میشه💔"),
        (r'خداحافظ|خدافظ', "خدانگهدار، فراموشم نکن🌹"),
        (r'\b(بای|بای بای|فعلا)\b', "بای عشقم، زود برگرد"),
    ]
    for pattern, resp in farewell_patterns:
        if re.search(pattern, user_message, re.IGNORECASE):
            return get_random_response(resp)

    if re.search(r'\bبغل\b', user_message):
        return "بیا بغلم 🫂"

    return None

# -------------------- راه‌اندازی ربات --------------------
BOT_TOKEN = "IIBGE0GTQVSBGRKBQTBZSPWHJAQPMTLFSHHSSGDRUFNOXKOUHEHCOLTOKQPDPOWY"   # <-- توکن خودت رو اینجا بذار

bot = Robot(token=BOT_TOKEN)

# فقط یک دکوراتور برای همه پیام‌ها (بدون دکوراتور جداگانه برای /start و /help)
@bot.on_message()
async def handle_all(bot: Robot, message: context.Message):
    # لاگ ساده برای اطمینان از دریافت پیام (در ترمینال چاپ می‌شه)
    print(f"[DEBUG] پیام دریافت شد: {message.text} از {message.author_id}")

    # نادیده گرفتن پیام‌های خود ربات
    if message.author_id == bot.user_id:
        return

    # پاسخ به استیکر
    if message.sticker:
        emoji = message.sticker.emoji
        if emoji in ["👋", "🙋", "🙏"]:
            await message.reply("خدانگهدار عزیزم، دلم برات تنگ میشه💔")
        return

    # پردازش متن
    if not message.text:
        return

    text = message.text.strip()

    # دستور start
    if text == "/start":
        await message.reply(
            "سلام! من فری باتم. هرچی بگی جواب دارم 😎\n"
            "بگو ببینم چته؟\n"
            "فقط کافیه بنویسی «سوال» تا یه سوال تصادفی ازت بپرسم."
        )
        return

    # دستور help
    if text == "/help":
        await message.reply(
            "فقط یه چیزی بگو، جواب قشنگ می‌گیری.\n"
            "مثال: سلام، خوبی، بغل، خدانگهدار،...\n"
            "با نوشتن «سوال» یه سوال تصادفی می‌پرسم."
        )
        return

    # سوال تصادفی
    if text in ["سوال", "سوال؟", "سوال!"]:
        if questions:
            rand_q = random.choice(questions)
            await message.reply(rand_q)
        else:
            await message.reply("سوالی توی لیست نیست :(")
        return

    # پاسخ‌های دستی از responses.py
    resp = get_response(text)
    if resp:
        await message.reply(resp)
        return

    # اگر هیچ تطابقی نداشت
    await message.reply("متوجه نشدم 😅 یه طور دیگه بگو یا از من سوال بپرس!")

# -------------------- اجرا با asyncio --------------------
if __name__ == "__main__":
    # راه‌اندازی فلاسک در یک ترد جداگانه
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("وب سرور Flask روی پورت 8000 روشن شد.")

    print("ربات در حال اتصال به روبیکا است...")
    # استفاده از asyncio.run به جای bot.run()
    asyncio.run(bot.run())
