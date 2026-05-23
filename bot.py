import os
import re
import asyncio
import subprocess
from pathlib import Path

from rubka.asynco import Robot
from rubka.context import Message
import yt_dlp

# ---------- تنظیمات اولیه ----------
TOKEN = "IIBGE0GTQVSBGRKBQTBZSPWHJAQPMTLFSHHSSGDRUFNOXKOUHEHCOLTOKQPDPOWY"
DOWNLOAD_DIR = Path("downloads")
MAX_DURATION_MINUTES = 30

# ---------- متون پیام‌ها (همانند قبل) ----------
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

# ---------- توابع کمکی ----------
def setup_download_dir():
    DOWNLOAD_DIR.mkdir(exist_ok=True)

def parse_song_name(user_input: str) -> str:
    user_input = user_input.replace('@songdownload597_bot', '')
    if user_input.startswith('/song'):
        return user_input[5:].strip()
    return ""

def is_spotify_link(text: str) -> bool:
    return 'open.spotify.com' in text

def is_valid_duration(duration_seconds: int) -> bool:
    return duration_seconds <= (MAX_DURATION_MINUTES * 60)

# ---------- دانلود با استفاده از PO Token Provider داخلی تصویر ----------
async def download_from_youtube(song_query: str) -> dict:
    # در این تصویر داکر، اسکریپت run-pot-server.sh سرور PO Token را روی پورت 4416 راه می‌اندازد
    po_proc = None
    try:
        # اجرای اسکریپت آماده (در پس‌زمینه)
        po_proc = subprocess.Popen(["/usr/local/bin/run-pot-server.sh"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # منتظر آماده شدن سرور
        await asyncio.sleep(4)

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
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'web'],
                    'skip': ['hls', 'dash'],
                    # استفاده از PO Token Provider محلی (bgutil)
                    'po_token_provider': 'bgutil:http://127.0.0.1:4416/get_pot',
                },
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{song_query}", download=True)
            if 'entries' in info:
                video = info['entries'][0]
            else:
                video = info

            title = video.get('title', song_query)
            duration = video.get('duration', 0)
            base_title = re.sub(r'[\\/*?:"<>|]', '', title)
            file_path = DOWNLOAD_DIR / f"{base_title}.mp3"
            if not file_path.exists():
                for f in DOWNLOAD_DIR.glob("*.mp3"):
                    if f.stem.startswith(base_title[:30]):
                        file_path = f
                        break
            return {'file_path': str(file_path), 'title': title, 'duration': duration}
    finally:
        if po_proc:
            po_proc.terminate()
            await asyncio.sleep(1)
            po_proc.kill()

async def download_audio(song_query: str) -> dict:
    return await download_from_youtube(song_query)

def cleanup_file(file_path: str):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ حذف شد: {file_path}")
    except Exception as e:
        print(f"⚠️ خطا در حذف فایل: {e}")

async def send_audio_with_caption(message: Message, audio_path: str, title: str):
    with open(audio_path, 'rb') as audio_file:
        await message.reply_audio(
            audio=audio_file,
            caption="🖇️♥️",
            title=title
        )
    cleanup_file(audio_path)

# ---------- راه‌اندازی ربات روبیکا ----------
bot = Robot(token=TOKEN)

@bot.on_message(commands=["start"])
async def start_handler(_: Robot, message: Message):
    await message.reply(START_TEXT_MSG, parse_mode="Markdown")

@bot.on_message(commands=["song"])
async def song_handler(_: Robot, message: Message):
    user_input = message.text or ""
    song_name = parse_song_name(user_input)
    if not song_name:
        await message.reply(INVALID_COMMAND_ERROR_TEXT_MSG, parse_mode="Markdown")
        return
    if is_spotify_link(song_name):
        await message.reply(SPOTIFY_INPUT_ERROR_TEXT_MSG, parse_mode="Markdown")
        return

    status_msg = await message.reply(f"🎵 جستجو و دانلود:\n`{song_name}`\n⬇️ لطفاً صبر کنید...")
    try:
        result = await download_audio(song_name)
        file_path = result['file_path']
        title = result['title']
        duration_sec = result['duration']
        if duration_sec > 0 and not is_valid_duration(duration_sec):
            await status_msg.delete()
            await message.reply(TOO_LONG_ERROR_TEXT_MSG, parse_mode="Markdown")
            if os.path.exists(file_path):
                cleanup_file(file_path)
            return
        await status_msg.delete()
        await send_audio_with_caption(message, file_path, title)
        await message.reply(CONFIRMATION_TEXT_MSG, parse_mode="Markdown")
    except Exception as e:
        await status_msg.delete()
        error_text = f"❌ خطا در دانلود یا ارسال:\n`{str(e)}`"
        await message.reply(error_text)
        print(f"❌ خطا: {e}")

def main():
    setup_download_dir()
    print("🎵 ربات دانلود آهنگ با روش PO Token (تصویر آماده) راه‌اندازی شد...")
    print("⏳ در حال اتصال به سرور روبیکا...")
    bot.run()

if __name__ == "__main__":
    main()
