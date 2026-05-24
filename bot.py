import os
import asyncio
import requests
import wget
from pathlib import Path
from youtube_search import YoutubeSearch
from youtubesearchpython import SearchVideos
from yt_dlp import YoutubeDL
from rubka.asynco import Robot
from rubka.context import Message

# ---------- تنظیمات ----------
TOKEN = "IIBGE0GTQVSBGRKBQTBZSPWHJAQPMTLFSHHSSGDRUFNOXKOUHEHCOLTOKQPDPOWY"
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# ---------- متن پیام start ----------
START_TEXT = (
    "🎵 **به ربات دانلود آهنگ و ویدیو خوش آمدید!**\n\n"
    "📌 **دستورات:**\n"
    "• `/song نام آهنگ` یا `/mp3 نام آهنگ` - دانلود آهنگ (mp4/m4a)\n"
    "• `/video نام ویدیو` یا `/mp4 نام ویدیو` - دانلود ویدیو\n\n"
    "مثال:\n"
    "`/song آرون افشار شب رویایی`\n"
    "`/video تایتانیک`\n\n"
    "🎧 ساخته شده با ❤️"
)

# ---------- تابع کمکی برای استخراج متن پس از دستور ----------
def get_query(message: Message) -> str:
    text = message.text or ""
    parts = text.split(maxsplit=1)
    if len(parts) > 1:
        return parts[1].strip()
    return ""

# ---------- توابع همگام (Synchronous) برای دانلود واقعی (اجرا در thread جدا) ----------
def sync_download_song(link: str, title: str, thumb_name: str, duration_sec: int):
    """دانلود آهنگ (اجرا در thread مجزا)"""
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio',
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'cookiefile': 'cookies.txt',
        'sleep_interval': 3,
        'extractor_retries': 3,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=True)
        filename = ydl.prepare_filename(info).replace('.webm', '.m4a').replace('.opus', '.m4a')
        if not os.path.exists(filename):
            for f in DOWNLOAD_DIR.glob(f"{info['title']}*"):
                filename = str(f)
                break
        return {'filename': filename, 'title': info.get('title', title), 'duration': info.get('duration', duration_sec)}

def sync_download_video(video_url: str, thumb_name: str):
    """دانلود ویدیو (اجرا در thread مجزا)"""
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': str(DOWNLOAD_DIR / '%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
        'cookiefile': 'cookies.txt',
        'sleep_interval': 3,
        'extractor_retries': 3,
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        filename = ydl.prepare_filename(info).replace('.webm', '.mp4').replace('.mkv', '.mp4')
        if not os.path.exists(filename):
            for f in DOWNLOAD_DIR.glob(f"{info['id']}*.mp4"):
                filename = str(f)
                break
        return {'filename': filename, 'info': info}

# ---------- هندلر استارت ----------
bot = Robot(token=TOKEN)

@bot.on_message(commands=["start"])
async def start_handler(_: Robot, message: Message):
    await message.reply(START_TEXT)

# ---------- هندلر دانلود آهنگ ----------
@bot.on_message(commands=["song", "mp3"])
async def song_handler(_: Robot, message: Message):
    query = get_query(message)
    if not query:
        await message.reply("❗ لطفاً نام آهنگ را بعد از دستور وارد کنید.\nمثال: `/song آرون افشار شب رویایی`")
        return

    status_msg = await message.reply(f"🔎 **در حال جستجو:** `{query}` ...")
    try:
        # جستجو در یوتیوب
        results = YoutubeSearch(query, max_results=1).to_dict()
        if not results:
            await status_msg.edit("❌ هیچ نتیجه‌ای یافت نشد.")
            return

        video_data = results[0]
        link = f"https://youtube.com{video_data['url_suffix']}"
        title = video_data["title"][:40]
        duration_str = video_data["duration"]
        thumbnail_url = video_data["thumbnails"][0]

        # محاسبه مدت زمان به ثانیه
        duration_sec = 0
        parts = duration_str.split(':')
        if len(parts) == 3:
            duration_sec = int(parts[0])*3600 + int(parts[1])*60 + int(parts[2])
        elif len(parts) == 2:
            duration_sec = int(parts[0])*60 + int(parts[1])
        else:
            duration_sec = int(parts[0])

        # دانلود thumbnail
        thumb_name = f"thumb_{title}.jpg"
        thumb_data = requests.get(thumbnail_url, allow_redirects=True)
        with open(thumb_name, 'wb') as f:
            f.write(thumb_data.content)

        await status_msg.edit("📀 **در حال دانلود و آماده‌سازی آهنگ...**")

        # اجرای دانلود در یک thread جدا (برای جلوگیری از قفل شدن ربات)
        result = await asyncio.to_thread(sync_download_song, link, title, thumb_name, duration_sec)
        filename = result['filename']
        # title و duration از result گرفته شود (اختیاری)

        # ارسال فایل صوتی به روبیکا
        caption = "🎧 **دانلود شده توسط ربات**"
        with open(filename, 'rb') as audio_file:
            await message.reply_audio(
                audio=audio_file,
                caption=caption,
                title=title,
                performer="IR-BOTZ",
                duration=duration_sec,
                thumb=open(thumb_name, 'rb')
            )

        await status_msg.delete()
        # پاکسازی فایل‌ها
        os.remove(filename)
        os.remove(thumb_name)

    except Exception as e:
        await status_msg.edit(f"❌ خطا در دانلود آهنگ:\n`{str(e)}`")
        print(f"Error in song: {e}")

# ---------- هندلر دانلود ویدیو ----------
@bot.on_message(commands=["video", "mp4", "vidddeo", "m67p4"])
async def video_handler(_: Robot, message: Message):
    query = get_query(message)
    if not query:
        await message.reply("❗ لطفاً نام ویدیو را بعد از دستور وارد کنید.\nمثال: `/video تایتانیک`")
        return

    status_msg = await message.reply(f"🔎 **در حال جستجوی ویدیو:** `{query}` ...")
    try:
        # جستجو با youtubesearchpython
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

        # دانلود thumbnail
        thumb_name = f"thumb_{video_id}.jpg"
        wget.download(thumbnail_url, out=thumb_name)

        await status_msg.edit("📀 **در حال دانلود و آماده‌سازی ویدیو...**")

        # اجرای دانلود در thread جدا
        result = await asyncio.to_thread(sync_download_video, video_url, thumb_name)
        filename = result['filename']
        info = result['info']

        # ارسال ویدیو به روبیکا
        caption = f"🎬 **{title[:50]}**\nدرخواست شده توسط کاربر"
        with open(filename, 'rb') as video_file, open(thumb_name, 'rb') as thumb_file:
            await message.reply_video(
                video=video_file,
                caption=caption,
                duration=int(info.get('duration', 0)),
                width=info.get('width', 0),
                height=info.get('height', 0),
                thumb=thumb_file,
                supports_streaming=True
            )

        await status_msg.delete()
        # پاکسازی فایل‌ها
        os.remove(filename)
        os.remove(thumb_name)

    except Exception as e:
        await status_msg.edit(f"❌ خطا در دانلود ویدیو:\n`{str(e)}`")
        print(f"Error in video: {e}")

# ---------- وب سرور داخلی برای Health Check در Koyeb ----------
try:
    from flask import Flask
    from threading import Thread

    web_app = Flask(__name__)

    @web_app.route('/')
    def health_check():
        return "OK", 200

    def run_web_server():
        port = int(os.environ.get('PORT', 8000))
        web_app.run(host='0.0.0.0', port=port)

    def start_web_server():
        server = Thread(target=run_web_server)
        server.daemon = True
        server.start()
        print("✅ وب سرور داخلی برای health check راه‌اندازی شد.")
except ImportError:
    print("⚠️ Flask نصب نیست، وب سرور health check راه‌اندازی نشد.")
    def start_web_server():
        pass

# ---------- اجرای ربات ----------
def main():
    print("🎬 ربات دانلود آهنگ و ویدیو در روبیکا راه‌اندازی شد...")
    start_web_server()   # اجرای وب سرور در background
    bot.run()

if __name__ == "__main__":
    main()
