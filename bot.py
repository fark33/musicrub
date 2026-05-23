import os
import re
from pathlib import Path

from rubka.asynco import Robot
from rubka.context import Message
import yt_dlp

# توکن ربات – بهتر است از متغیر محیطی خوانده شود
TOKEN = os.getenv("TOKEN", "IIBGE0GTQVSBGRKBQTBZSPWHJAQPMTLFSHHSSGDRUFNOXKOUHEHCOLTOKQPDPOWY")
DOWNLOAD_DIR = Path("downloads")


def setup_download_dir():
    """ایجاد پوشه دانلود در صورت نبودن"""
    DOWNLOAD_DIR.mkdir(exist_ok=True)


async def download_audio(song_query: str) -> str:
    """
    جستجو در یوتیوب و دانلود اولین نتیجه به صورت MP3
    برگرداندن مسیر فایل دانلود شده
    """
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
        'default_search': 'ytsearch',   # جستجوی خودکار
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # جستجو و دانلود اولین نتیجه
        info = ydl.extract_info(f"ytsearch1:{song_query}", download=True)

        if 'entries' in info:
            video_info = info['entries'][0]
        else:
            video_info = info

        # ساخت نام فایل پاک و ایمن
        base_title = video_info.get('title', song_query)
        safe_title = re.sub(r'[\\/*?:"<>|]', "", base_title)
        downloaded_file = DOWNLOAD_DIR / f"{safe_title}.mp3"

        if downloaded_file.exists():
            return str(downloaded_file)
        else:
            raise FileNotFoundError(f"فایل پیدا نشد: {downloaded_file}")


def cleanup_file(file_path: str):
    """حذف فایل از روی سرور بعد از ارسال"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"پاک شد: {file_path}")
    except Exception as e:
        print(f"خطا در حذف فایل: {e}")


async def send_audio_with_caption(message: Message, audio_path: str):
    """ارسال فایل صوتی با کپشن مشخص و سپس حذف فایل"""
    with open(audio_path, 'rb') as audio_file:
        await message.reply_audio(
            audio=audio_file,
            caption="🖇️♥️"
        )
    cleanup_file(audio_path)


# ساخت نمونه ربات
bot = Robot(token=TOKEN)


@bot.on_message(commands=["start"])
async def start_command(bot: Robot, message: Message):
    """دستور خوشامدگویی"""
    await message.reply(
        "🎵 به ربات دانلود آهنگ خوش آمدید!\n\n"
        "برای دانلود آهنگ مورد نظر، دستور زیر را ارسال کنید:\n"
        "/ahang --- نام آهنگ یا خواننده\n\n"
        "مثال:\n"
        "/ahang --- محسن ابراهیم زاده جدایی\n"
        "/ahang --- Shajarian"
    )


@bot.on_message(commands=["ahang"])
async def ahang_command(bot: Robot, message: Message):
    """پردازش درخواست دانلود آهنگ"""
    text = message.text or ""
    match = re.search(r"/ahang\s+---\s+(.+)", text)

    if not match:
        await message.reply(
            "❌ فرمت دستور اشتباه است!\n"
            "لطفاً به شکل زیر ارسال کنید:\n"
            "/ahang --- نام آهنگ یا خواننده"
        )
        return

    song_query = match.group(1).strip()
    if not song_query:
        await message.reply("❌ نام آهنگ یا خواننده نمی‌تواند خالی باشد.")
        return

    # پیام وضعیت
    status_msg = await message.reply(f"🔍 در حال جستجو و دانلود **{song_query}** ...")

    try:
        audio_path = await download_audio(song_query)
        await status_msg.delete()
        await send_audio_with_caption(message, audio_path)
    except Exception as e:
        await status_msg.delete()
        await message.reply(f"❌ خطا در دانلود یا ارسال: {str(e)}")


def main():
    setup_download_dir()
    print("ربات با موفقیت راه‌اندازی شد...")
    bot.run()


if __name__ == "__main__":
    main()
