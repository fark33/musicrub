import os
import re
import random
from rubka import Robot, context
from responses import handcrafted_responses, get_random_response
from questions import questions

def normalize_text(text: str) -> str:
    text = re.sub(r'(.)\1+', r'\1', text)
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

bot = Robot(token=os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE"))

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

        # اگر کاربر دقیقاً "سوال" نوشت
        if text in ["سوال", "سوال؟", "سوال!"]:
            if questions:
                random_question = random.choice(questions)
                await message.reply(random_question)
            else:
                await message.reply("سوالی توی لیست نیست :(")
            return

        # پاسخ‌های دستی معمولی
        response = get_response(text)
        if response:
            await message.reply(response)
            return

@bot.on_message(commands=["start"])
async def start_command(bot: Robot, message: context.Message):
    await message.reply("سلام! من فری باتم. هرچی بگی جواب دارم 😎\nبگو ببینم چته؟\nفقط کافیه بنویسی «سوال» تا یه سوال تصادفی ازت بپرسم.")

@bot.on_message(commands=["help"])
async def help_command(bot: Robot, message: context.Message):
    await message.reply("فقط یه چیزی بگو، جواب قشنگ می‌گیری.\nمثال: سلام، خوبی، بغل، خدانگهدار،...\nبا نوشتن «سوال» یه سوال تصادفی می‌پرسم.")

if __name__ == "__main__":
    print("ربات روشن شد... (فقط با 'سوال' سوال تصادفی می‌پرسد)")
    bot.run()
