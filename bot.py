import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Any

import requests
import wget
from youtube_search import YoutubeSearch
from youtubesearchpython import SearchVideos
from yt_dlp import YoutubeDL
from rubka.asynco import Robot
from rubka.context import Message

# ---------- تنظیمات ----------
TOKEN = os.environ.get("BOT_TOKEN", "IIBGE0GTQVSBGRKBQTBZSPWHJAQPMTLFSHHSSGDRUFNOXKOUHEHCOLTOKQPDPOWY")
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)
MAX_DOWNLOAD_TIMEOUT = 300  # حداکثر زمان دانلود (5 دقیقه)
_download_executor = ThreadPoolExecutor(max_workers=1)  # مدیریت همزمانی
_active_downloads = set()  # مجموعه برای پیگیری دانلودهای فعال

# ---------- کلاس مدیریت دانلود ----------
class DownloadManager:
    def __init__(self):
        self._active = set()
    
    async def run_in_executor(self, func, *args):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(_download_executor, func, *args)

    async def download_song(self, link: str) -> Dict[str, Any]:
        def _sync_download():
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'logger': None,
                'cookiefile': 'cookies.txt',
                'sleep_interval': 3,
                'extractor_retries': 3,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '256',
                }],
                'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
                'compat_opts': ['allow-unsafe-extractor-args'],
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                filename = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3').replace('.opus', '.mp3')
                if not os.path.exists(filename):
                    for f in DOWNLOAD_DIR.glob(f"{info['title']}*.mp3"):
                        filename = str(f)
                        break
                return {'filename': filename, 'info': info}
        return await self.run_in_executor(_sync_download)

    async def download_video(self, video_url: str) -> Dict[str, Any]:
        def _sync_download():
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': str(DOWNLOAD_DIR / '%(id)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'logger': None,
                'merge_output_format': 'mp4',
                'cookiefile': 'cookies.txt',
                'sleep_interval': 3,
                'extractor_retries': 3,
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
                'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
                'compat_opts': ['allow-unsafe-extractor-args'],
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                filename = ydl.prepare_filename(info).replace('.webm', '.mp4').replace('.mkv', '.mp4')
                if not os.path.exists(filename):
                    for f in DOWNLOAD_DIR.glob(f"{info['id']}*.mp4"):
                        filename = str(f)
                        break
                return {'filename': filename, 'info': info}
        return await self.run_in_executor(_sync_download)

download_manager = DownloadManager()

# ---------- متن پیام start ----------
START_TEXT = "🎵 **به ربات دانلود آهنگ و ویدیو خوش آمدید!**\n\n📌 **دستورات:**\n• `/song نام آهنگ` یا `/mp3 نام آهنگ` - دانلود آهنگ (mp3)\n• `/video نام ویدیو` یا `/mp4 نام ویدیو` - دانلود ویدیو\n\nمثال:\n`/song آرون افشار شب رویایی`\n`/video تایتانیک`\n\n🎧 ساخته شده با ❤️"

# ---------- تابع کمکی ----------
def get_query(message: Message) -> str:
    text = message.text or ""
    parts = text.split(maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else ""

# ---------- راه‌اندازی ربات ----------
bot = Robot(token=TOKEN)

@bot.on_message(commands=["start"])
async def start_handler(_: Robot, message: Message):
    await message.reply(START_TEXT)

# ---------- هندلر دانلود آهنگ ----------
@bot.on_message(commands=["song", "mp3"])
async def song_handler(_: Robot, message: Message):
    query = get_query(message)
    if not query:
        await message.reply("❗ لطفاً نام آهنگ را بعد از دستور وارد کنید.")
        return

    status_msg = await message.reply(f"🔎 **در حال جستجو:** `{query}` ...")
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        if not results:
            await status_msg.edit("❌ هیچ نتیجه‌ای یافت نشد.")
            return

        video_data = results[0]
        link = f"https://youtube.com{video_data['url_suffix']}"
        title = video_data["title"][:40]
        duration_str = video_data["duration"]
        thumbnail_url = video_data["thumbnails"][0]
        duration_sec = sum(int(x) * 60 ** i for i, x in enumerate(reversed(duration_str.split(':'))))  # تبدیل مدت زمان به ثانیه

        thumb_name = f"thumb_{title}.jpg"
        thumb_data = requests.get(thumbnail_url, allow_redirects=True)
        with open(thumb_name, 'wb') as f:
            f.write(thumb_data.content)

        await status_msg.edit("📀 **در حال دانلود و آماده‌سازی آهنگ...**")
        result = await asyncio.wait_for(download_manager.download_song(link), timeout=MAX_DOWNLOAD_TIMEOUT)
        filename = result['filename']
        info = result['info']

        with open(filename, 'rb') as audio_file:
            await message.reply_audio(
                audio=audio_file,
                caption="🎧 **دانلود شده توسط ربات**",
                title=info.get('title', title),
                performer="IR-BOTZ",
                duration=info.get('duration', duration_sec),
                thumb=open(thumb_name, 'rb')
            )

        await status_msg.delete()
        os.remove(filename)
        os.remove(thumb_name)

    except asyncio.TimeoutError:
        await status_msg.edit("❌ زمان دانلود به پایان رسید. لطفاً دوباره تلاش کنید.")
    except Exception as e:
        await status_msg.edit(f"❌ خطا در دانلود آهنگ:\n`{str(e)}`")
        print(f"Error in song: {e}")

# ---------- هندلر دانلود ویدیو ----------
@bot.on_message(commands=["video", "mp4", "vidddeo", "m67p4"])
async def video_handler(_: Robot, message: Message):
    query = get_query(message)
    if not query:
        await message.reply("❗ لطفاً نام ویدیو را بعد از دستور وارد کنید.")
        return

    status_msg = await message.reply(f"🔎 **در حال جستجوی ویدیو:** `{query}` ...")
    try:
        search = SearchVideos(query, offset=1, mode="dict", max_results=1)
        result = search.result()
        search_list = result["search_result"]
        if not search_list:
            await status_msg.edit("❌ هیچ ویدیویی یافت نشد.")
            return

        video_info = search_list[0]
        video_url = video_info["link"]
        title = video_info["title"]
        video_id = video_info["id"]
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

        thumb_name = f"thumb_{video_id}.jpg"
        wget.download(thumbnail_url, out=thumb_name)

        await status_msg.edit("📀 **در حال دانلود و آماده‌سازی ویدیو...**")
        result = await asyncio.wait_for(download_manager.download_video(video_url), timeout=MAX_DOWNLOAD_TIMEOUT)
        filename = result['filename']
        info = result['info']

        with open(filename, 'rb') as video_file, open(thumb_name, 'rb') as thumb_file:
            await message.reply_video(
                video=video_file,
                caption=f"🎬 **{title[:50]}**\nدرخواست شده توسط کاربر",
                duration=int(info.get('duration', 0)),
                width=info.get('width', 0),
                height=info.get('height', 0),
                thumb=thumb_file,
                supports_streaming=True
            )

        await status_msg.delete()
        os.remove(filename)
        os.remove(thumb_name)

    except asyncio.TimeoutError:
        await status_msg.edit("❌ زمان دانلود به پایان رسید. لطفاً دوباره تلاش کنید.")
    except Exception as e:
        await status_msg.edit(f"❌ خطا در دانلود ویدیو:\n`{str(e)}`")
        print(f"Error in video: {e}")

# ---------- اجرای ربات ----------
def main():
    print("🎬 ربات دانلود آهنگ و ویدیو در روبیکا راه‌اندازی شد...")
    bot.run()

if __name__ == "__main__":
    main()
