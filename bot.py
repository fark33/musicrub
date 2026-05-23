import asyncio
import os
import re
import shutil
from pathlib import Path

from rubka import Robot, context
from rubka.message import Message

import yt_dlp


TOKEN = "IIBGE0GTQVSBGRKBQTBZSPWHJAQPMTLFSHHSSGDRUFNOXKOUHEHCOLTOKQPDPOWY"  # توکن دریافتی از بات‌فادر روبیکا
DOWNLOAD_DIR = Path("downloads")


def setup_download_dir():
    """پوشه دانلودها را ایجاد می‌کند"""
    DOWNLOAD_DIR.mkdir(exist_ok=True)


async def download_audio(song_name: str) -> str:
    """جستجو و دانلود آهنگ از یوتیوب و برگرداندن مسیر فایل دانلود شده"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'default_search': 'ytsearch',  # جستجوی خودکار در یوتیوب
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # جستجو و دانلود اولین نتیجه
            info = ydl.extract_info(f"ytsearch1:{song_name}", download=True)
            if 'entries' in info:
                video_info = info['entries'][0]
            else:
                video_info = info

            # پیدا کردن فایل نهایی (با پسوند mp3)
            base_title = video_info.get('title', song_name)
            # حذف کاراکترهای غیرمجاز در نام فایل
            safe_title = re.sub(r'[\\/*?:"<>|]', "", base_title)
            downloaded_file = DOWNLOAD_DIR / f"{safe_title}.mp3"

            if downloaded_file.exists():
                return str(downloaded_file)
            else:
                raise FileNotFoundError(f"فایل پیدا نشد: {downloaded_file}")

    except Exception as e:
        print(f"خطا در دانلود: {e}")
        raise


def cleanup_file(file_path: str):
    """پاک کردن فایل از سرور بعد از ارسال"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"فایل حذف شد: {file_path}")
    except Exception as e:
        print(f"خطا در حذف فایل: {e}")


async def send_audio_with_caption(message: Message, audio_path: str):
    """ارسال آهنگ به همراه کپشن"""
    try:
        with open(audio_path, 'rb') as audio_file:
            await message.reply_audio(
                audio=audio_file,
                caption="🖇️♥️"
            )
    except Exception as e:
        await message.reply(f"❌ خطا در ارسال فایل: {str(e)}")
        raise
    finally:
        cleanup_file(audio_path)


# راه‌اندازی ربات
bot = Robot(token=TOKEN)


@bot.on_message(commands=["start"])
async def start_command_handler(bot: Robot, message: Message):
    """دستور خوش‌آمدگویی ساده"""
    welcome_text = (
        "🎵 به ربات دانلود آهنگ خوش آمدید!\n\n"
        "برای دانلود آهنگ مورد نظر خود، دستور زیر را ارسال کنید:\n"
        "/ahang --- نام آهنگ یا خواننده\n\n"
        "مثال:\n"
        "/ahang --- Shajarian\n"
        "/ahang --- Benyamin Bahadori"
    )
    await message.reply(welcome_text)


@bot.on_message(commands=["ahang"])
async def ahang_command_handler(bot: Robot, message: Message):
    """پردازش دستور دانلود آهنگ"""
    # استخراج نام آهنگ از متن پیام
    text = message.text or ""
    match = re.search(r"/ahang\s+---\s+(.+)", text)

    if not match:
        await message.reply(
            "❌ فرمت دستور صحیح نیست!\n"
            "لطفاً به شکل زیر ارسال کنید:\n"
            "/ahang --- نام آهنگ یا خواننده"
        )
        return

    song_query = match.group(1).strip()
    if not song_query:
        await message.reply("❌ لطفاً نام آهنگ یا خواننده را وارد کنید.")
        return

    # اطلاع به کاربر برای شروع دانلود
    status_msg = await message.reply(f"🔍 در حال جستجو و دانلود آهنگ **{song_query}** ...")

    try:
        # دانلود آهنگ
        audio_file_path = await download_audio(song_query)

        # حذف پیام وضعیت
        await status_msg.delete()

        # ارسال فایل صوتی با کپشن مورد نظر
        await send_audio_with_caption(message, audio_file_path)

    except Exception as e:
        await status_msg.delete()
        await message.reply(f"❌ خطا در دانلود یا ارسال آهنگ: {str(e)}")


def main():
    setup_download_dir()
    print("ربات با موفقیت راه‌اندازی شد...")
    bot.run()


if __name__ == "__main__":
    main()
