import os
import re
import asyncio
from random import randint
from pathlib import Path

from rubka.asynco import Robot
from rubka.context import Message
import yt_dlp

# ------------------------------------------------------------
# متون پیام‌ها (قبلاً در text_msg.py بودند)
# ------------------------------------------------------------
START_TEXT_MSG = (
    '🤖 Hello user!\n\n'
    '📩 I can download songs for you. Just send me the song name in below format:\n'
    '*/song*  _song name_  or\n'
    '*/song*  _musician name - song name_\n\n'
    'to download some songs. 🎶\n\n'
    '**■ ProTips**💡[ »Learn Bot](https://t.me/sanilaassistant_bot) \n'
    '                          [»Rate Bot](https://t.me/sanilaassistant_bot)\n'
    '                          [»Get help](https://t.me/sanilaassistant_bot)\n'
    '                          [»Give feedback](https://t.me/sanilaassistant_bot)'
)

CONFIRMATION_TEXT_MSG = (
    "✅ Song downloaded successfully!\n\n"
    "**■ ProTips**💡[ »Learn Bot](https://t.me/sanilaassistant_bot) \n"
    "                          [»Rate Bot](https://t.me/sanilaassistant_bot)\n"
    "                          [»Get help](https://t.me/sanilaassistant_bot)\n"
    "                          [»Give feedback](https://t.me/sanilaassistant_bot)"
)

SPOTIFY_INPUT_ERROR_TEXT_MSG = (
    '‼️ *Oops! The bot does not support Spotify links!*\n'
    'Try: "*/song* _song name_"\n'
    'or: "*/song* _musician name - song name_"\n\n'
    '**■ ProTips**💡[ »Learn Bot](https://t.me/sanilaassistant_bot) \n'
    '                          [»Rate Bot](https://t.me/sanilaassistant_bot)\n'
    '                          [»Get help](https://t.me/sanilaassistant_bot)\n'
    '                          [»Give feedback](https://t.me/sanilaassistant_bot)'
)

INVALID_COMMAND_ERROR_TEXT_MSG = (
    '‼️ *Oops! Invalid command!*\n'
    'Try: "*/song* _song name_"\n'
    'or: "*/song* _musician name - song name_"\n\n'
    '**■ ProTips**💡[ »Learn Bot](https://t.me/sanilaassistant_bot) \n'
    '                          [»Rate Bot](https://t.me/sanilaassistant_bot)\n'
    '                          [»Get help](https://t.me/sanilaassistant_bot)\n'
    '                          [»Give feedback](https://t.me/sanilaassistant_bot)'
)

TOO_LONG_ERROR_TEXT_MSG = (
    '‼️ *Oops! Video too long to convert!*\n'
    'Order something 30 minutes or less.\n\n'
    '**■ ProTips**💡[ »Learn Bot](https://t.me/sanilaassistant_bot) \n'
    '                          [»Rate Bot](https://t.me/sanilaassistant_bot)\n'
    '                          [»Get help](https://t.me/sanilaassistant_bot)\n'
    '                          [»Give feedback](https://t.me/sanilaassistant_bot)'
)

# ------------------------------------------------------------
# تنظیمات اصلی ربات
# ------------------------------------------------------------
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("❌ توکن ربات در متغیر محیطی TOKEN پیدا نشد.")

DOWNLOAD_DIR = Path("downloads")
MAX_DURATION_MINUTES = 30   # حداکثر مدت مجاز (دقیقه)


def setup_download_dir():
    DOWNLOAD_DIR.mkdir(exist_ok=True)


def parse_song_name(user_input: str) -> str:
    """
    استخراج نام آهنگ از دستور /song
    """
    # حذف ذکر بات (در تلگرام گاهی اضافه می‌شد)
    user_input = user_input.replace('@songdownload597_bot', '')
    if user_input.startswith('/song'):
        song_name = user_input[5:].strip()
        return song_name
    return ""


def is_spotify_link(text: str) -> bool:
    """بررسی لینک اسپاتیفای"""
    return 'open.spotify.com' in text


def is_valid_duration(duration_seconds: int) -> bool:
    """بررسی اینکه طول ویدیو کمتر از MAX_DURATION_MINUTES باشد"""
    return duration_seconds <= (MAX_DURATION_MINUTES * 60)


async def search_and_download(song_query: str) -> dict:
    """
    جستجو در یوتیوب و دانلود اولین نتیجه به صورت MP3.
    برگرداندن دیکشنری شامل مسیر فایل، عنوان و مدت زمان (ثانیه).
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '256',
        }],
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',
        'extract_flat': False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # جستجو و دانلود اولین نتیجه
        info = ydl.extract_info(f"ytsearch1:{song_query}", download=True)
        if 'entries' in info:
            video = info['entries'][0]
        else:
            video = info

        title = video.get('title', song_query)
        duration = video.get('duration', 0)  # ثانیه
        # پیدا کردن فایل نهایی (با پسوند mp3)
        base_title = re.sub(r'[\\/*?:"<>|]', '', title)
        file_path = DOWNLOAD_DIR / f"{base_title}.mp3"
        if not file_path.exists():
            # گاهی yt-dlp نام فایل را با کاراکترهای متفاوت ذخیره می‌کند
            for f in DOWNLOAD_DIR.glob("*.mp3"):
                if f.stem.startswith(base_title[:30]):
                    file_path = f
                    break
        return {
            'file_path': str(file_path),
            'title': title,
            'duration': duration
        }


def cleanup_file(file_path: str):
    """حذف فایل از سرور بعد از ارسال"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ حذف شد: {file_path}")
    except Exception as e:
        print(f"⚠️ خطا در حذف فایل: {e}")


# ------------------------------------------------------------
# راه‌اندازی ربات روبیکا
# ------------------------------------------------------------
bot = Robot(token=TOKEN)


@bot.on_message(commands=["start"])
async def start_handler(_: Robot, message: Message):
    """دستور /start"""
    await message.reply(START_TEXT_MSG, parse_mode="Markdown")


@bot.on_message(commands=["song"])
async def song_handler(_: Robot, message: Message):
    """دستور /song - پردازش درخواست آهنگ"""
    user_input = message.text or ""
    song_name = parse_song_name(user_input)

    # بررسی خالی بودن نام آهنگ
    if not song_name:
        await message.reply(INVALID_COMMAND_ERROR_TEXT_MSG, parse_mode="Markdown")
        return

    # بررسی لینک اسپاتیفای
    if is_spotify_link(song_name):
        await message.reply(SPOTIFY_INPUT_ERROR_TEXT_MSG, parse_mode="Markdown")
        return

    # ارسال پیام در حال دانلود
    status_msg = await message.reply(f"🎵 جستجو و دانلود:\n`{song_name}`\n⬇️ لطفاً صبر کنید...")

    try:
        # دانلود آهنگ
        result = await search_and_download(song_name)
        duration_sec = result['duration']
        file_path = result['file_path']
        title = result['title']

        # بررسی مدت زمان
        if not is_valid_duration(duration_sec):
            await status_msg.delete()
            await message.reply(TOO_LONG_ERROR_TEXT_MSG, parse_mode="Markdown")
            # حذف فایل اگر دانلود شده باشد
            if os.path.exists(file_path):
                cleanup_file(file_path)
            return

        # حذف پیام وضعیت
        await status_msg.delete()

        # ارسال فایل صوتی با کپشن 🖇️♥️
        with open(file_path, 'rb') as audio_file:
            await message.reply_audio(
                audio=audio_file,
                caption="🖇️♥️",
                title=title  # عنوان آهنگ
            )

        # ارسال پیام تأیید نهایی
        await message.reply(CONFIRMATION_TEXT_MSG, parse_mode="Markdown")

        # حذف فایل از سرور
        cleanup_file(file_path)

    except Exception as e:
        await status_msg.delete()
        error_text = f"❌ خطا در دانلود یا ارسال:\n`{str(e)}`"
        await message.reply(error_text)
        print(f"❌ خطا: {e}")


def main():
    setup_download_dir()
    print("🎵 ربات دانلود آهنگ برای روبیکا راه‌اندازی شد...")
    bot.run()


if __name__ == "__main__":
    main()
