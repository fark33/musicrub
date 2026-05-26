import asyncio
from rubka import Robot
from rubka.context import Message

# توکن واقعی خود را اینجا وارد کنید
BOT_TOKEN = "IIBGE0GTQVSBGRKBQTBZSPWHJAQPMTLFSHHSSGDRUFNOXKOUHEHCOLTOKQPDPOWY"

bot = Robot(token=BOT_TOKEN)

@bot.on_message()
async def echo_handler(bot: Robot, message: Message):
    try:
        print(f"پیام دریافت شد: {message.text} از {message.author_id} در {message.chat_id}")
        await message.reply(f"دوست جان، پیام شما دریافت شد: {message.text}")
    except Exception as e:
        print(f"خطا در هندلر: {e}")

print("ربات Echo ساده راه‌اندازی شد...")
# اجرای ربات به صورت صحیح و آسنکرون
asyncio.run(bot.run())
