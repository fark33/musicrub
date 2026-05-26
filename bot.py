import os
import re
import random
import threading
from flask import Flask, jsonify
from rubka import Robot, context
from responses import handcrafted_responses, get_random_response
from question import questions

# --- بخش اول: تنظیمات وب سرور Flask (برای Health Check) ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return jsonify({'status': 'ok'})

def run_flask():
    app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)

# --- بخش دوم: تنظیمات ربات روبیکا ---
def normalize_text(text: str) -> str:
    text = re.sub(r'(.)\1{2,}', r'\1\1', text)
    return text.strip()

def get_response(user_message: str) -> str | None:
    msg = user_message.strip()
    if not msg:
        return None
    msg_norm = normalize_text(msg)

    for key, resp in handcrafted_responses.items():
        if normalize_text(key) == msg_norm:
            return get_random_response(resp)

    for key, resp in handcrafted_responses.items():
        if key in msg_norm or msg_norm in key:
            return get_random_response(resp)

    farewell_patterns = [
        (r'خدانگهدار+', "خدانگهدار عزیزم، دلم برات تنگ میشه💔"),
        (r'خداحافظ|خدافظ', "خدانگهدار، فراموشم نکن🌹"),
        (r'\b(بای|بای بای|فعلا)\b', "بای عشقم، زود برگرد"),
    ]
    for pattern, resp in farewell_patterns:
        if re.search(pattern, msg, re.IGNORECASE):
            return get_random_response(resp)

    if re.search(r'\bبغل\b', msg):
        return "بیا بغلم 🫂"

    return None

BOT_TOKEN = "IIBGE0GTQVSBGRKBQTBZSPWHJAQPMTLFSHHSSGDRUFNOXKOUHEHCOLTOKQPDPOWY"
bot = Robot(token=BOT_TOKEN)

# === مهم: دکوراتورهای اختصاصی دستورات باید اول قرار بگیرند ===
@bot.on_message(commands=["start"])
async def start_command(bot: Robot, message: context.Message):
    await message.reply(
        "سلام! من فری باتم. هرچی بگی جواب دارم 😎\n"
        "بگو ببینم چته؟\n"
        "فقط کافیه بنویسی «سوال» تا یه سوال تصادفی ازت بپرسم."
    )

@bot.on_message(commands=["help"])
async def help_command(bot: Robot, message: context.Message):
    await message.reply(
        "فقط یه چیزی بگو، جواب قشنگ می‌گیری.\n"
        "مثال: سلام، خوبی، بغل، خدانگهدار،...\n"
        "با نوشتن «سوال» یه سوال تصادفی می‌پرسم."
    )

@bot.on_message()
async def handle_message(bot: Robot, message: context.Message):
    if message.author_id == bot.user_id:
        return

    if message.sticker:
        sticker_emoji = message.sticker.emoji
        if sticker_emoji in ["👋", "🙋", "🙏"]:
            await message.reply("خدانگهدار عزیزم، دلم برات تنگ میشه💔")
            return

    if message.text:
        text = message.text.strip()

        if text in ["سوال", "سوال؟", "سوال!"]:
            if questions:
                random_question = random.choice(questions)
                await message.reply(random_question)
            else:
                await message.reply("سوالی توی لیست نیست :(")
            return

        response = get_response(text)
        if response:
            await message.reply(response)
            return

        await message.reply("متوجه نشدم 😅 یه طور دیگه بگو یا از من سوال بپرس!")

# --- بخش سوم: اجرای همزمان ربات و وب سرور ---
if __name__ == "__main__":
    print("ربات روبیکا و وب سرور Flask در حال روشن شدن هستند...")
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("وب سرور Flask روی پورت 8000 روشن شد.")
    print("ربات در حال اتصال به روبیکا است...")
    bot.run()
