import os
import re
import requests
from pathlib import Path

from rubka.asynco import Robot
from rubka.context import Message
import yt_dlp
from radiojavanapi import Client as RJClient
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# ---------- تنظیمات اولیه ----------
TOKEN = "IIBGE0GTQVSBGRKBQTBZSPWHJAQPMTLFSHHSSGDRUFNOXKOUHEHCOLTOKQPDPOWY"

DOWNLOAD_DIR = Path("downloads")
MAX_DURATION_MINUTES = 30

# متون پیام‌ها (همان‌هایی که قبلاً داشتید)
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

# ---------- دانلود از یوتیوب (برای آهنگ‌های غیرفارسی) ----------
async def download_from_youtube(song_query: str) -> dict:
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
            # fallback: هر فایل mp3 جدید در پوشه
            for f in DOWNLOAD_DIR.glob("*.mp3"):
                if f.stem.startswith(base_title[:30]):
                    file_path = f
                    break
        return {'file_path': str(file_path), 'title': title, 'duration': duration}

# ---------- دانلود از RadioJavan (برای آهنگ‌های فارسی) ----------
async def download_from_radiojavan(song_query: str) -> dict:
    rj_client = RJClient()
    search_results = rj_client.search(song_query)
    if not search_results:
        raise Exception("هیچ نتیجه‌ای در رادیو جوان یافت نشد.")
    
    first_song = search_results[0]
    # لینک مستقیم دانلود با کیفیت بالا (hq_link) یا لینک معمولی
    download_link = first_song.get('hq_link') or first_song.get('link')
    if not download_link:
        raise Exception("لینک دانلود پیدا نشد.")
    
    title = first_song.get('name', song_query)
    safe_title = re.sub(r'[\\/*?:"<>|]', '', title)
    file_path = DOWNLOAD_DIR / f"{safe_title}.mp3"
    
    # دانلود فایل با استفاده از requests
    response = requests.get(download_link, stream=True)
    response.raise_for_status()
    with open(file_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    duration = 0  # رادیو جوان مدت زمان نمی‌دهد
    return {'file_path': str(file_path), 'title': title, 'duration': duration}

# ---------- جستجو در Spotify و دانلود از یوتیوب ----------
async def search_spotify_and_download(song_query: str) -> dict:
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if client_id and client_secret:
        try:
            auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
            sp = spotipy.Spotify(auth_manager=auth_manager)
            results = sp.search(q=song_query, type='track', limit=1)
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                track_name = track['name']
                artist_name = track['artists'][0]['name']
                return await download_from_youtube(f"{artist_name} {track_name}")
        except Exception as e:
            print(f"Spotify error: {e}, falling back to direct YouTube search")
    # fallback به یوتیوب بدون Spotify
    return await download_from_youtube(song_query)

# ---------- تابع اصلی دانلود (تشخیص خودکار زبان فارسی) ----------
async def download_audio(song_query: str) -> dict:
    # اگر متن شامل حروف فارسی باشد، از رادیو جوان استفاده کن
    if re.search('[\u0600-\u06FF]', song_query):
        try:
            return await download_from_radiojavan(song_query)
        except Exception as e:
            print(f"RadioJavan failed: {e}, falling back to Spotify/YouTube")
            return await search_spotify_and_download(song_query)
    else:
        return await search_spotify_and_download(song_query)

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
    print("🎵 ربات دانلود آهنگ با روش ترکیبی (رادیو جوان + یوتیوب) راه‌اندازی شد...")
    bot.run()

if __name__ == "__main__":
    main()
