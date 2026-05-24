import os
import asyncio
import threading
import http.server
import socketserver
import requests
from pathlib import Path
from youtube_search import YoutubeSearch
from yt_dlp import YoutubeDL
from rubka.asynco import Robot
from rubka.context import Message

# ---------- تنظیمات ----------
TOKEN = os.environ.get("BOT_TOKEN", "IIBGE0GTQVSBGRKBQTBZSPWHJAQPMTLFSHHSSGDRUFNOXKOUHEHCOLTOKQPDPOWY")
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# ---------- وب سرور داخلی برای Health Check ----------
class HealthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')
    def log_message(self, format, *args):
        pass

def run_health_server():
    with socketserver.TCPServer(("0.0.0.0", 8000), HealthHandler) as httpd:
        httpd.serve_forever()

def start_web_server():
    thread = threading.Thread(target=run_health_server, daemon=True)
    thread.start()
    print("✅ Health check server running on port 8000")

# ---------- تابع دانلود همگام (بدون تبدیل) ----------
def sync_download(link: str):
    """دانلود بهترین فرمت صوتی موجود (m4a یا opus) بدون هیچ تبدیلی"""
    ydl_opts = {
        'format': 'bestaudio/best',   # بهترین فرمت صوتی اصلی
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'logger': None,
        'cookiefile': 'cookies.txt',
        # حذف postprocessors => بدون تبدیل
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=True)
        filename = ydl.prepare_filename(info)
        # اگر فایل با پسوند غیرمنتظره بود، آن را پیدا کن
        if not os.path.exists(filename):
            for f in DOWNLOAD_DIR.glob(f"{info['title']}*"):
                filename = str(f)
                break
        return filename, info

# ---------- ربات ----------
bot = Robot(token=TOKEN)

@bot.on_message(commands=["start"])
async def start_handler(_: Robot, message: Message):
    await message.reply(
        "🎵 **ربات دانلود آهنگ (فوق سبک - بدون تبدیل)**\n\n"
        "📌 دستور: `/song نام آهنگ`\n"
        "مثال: `/song آرون افشار شب رویایی`\n\n"
        "⚡ سریع، کم مصرف، بدون قفل شدن"
    )

def get_query(message: Message) -> str:
    text = message.text or ""
    parts = text.split(maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else ""

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

        # تبدیل مدت زمان به ثانیه
        parts = list(map(int, duration_str.split(':')))
        if len(parts) == 1:
            duration_sec = parts[0]
        elif len(parts) == 2:
            duration_sec = parts[0]*60 + parts[1]
        else:
            duration_sec = parts[0]*3600 + parts[1]*60 + parts[2]

        # دانلود thumbnail
        thumb_name = f"thumb_{title}.jpg"
        thumb_data = requests.get(thumbnail_url, allow_redirects=True)
        with open(thumb_name, 'wb') as f:
            f.write(thumb_data.content)

        await status_msg.edit("📀 **در حال دانلود (بدون تبدیل، سرعت بالا)...**")

        # دانلود در thread جدا (جلوگیری از قفل شدن)
        filename, info = await asyncio.to_thread(sync_download, link)

        # ارسال فایل صوتی (فرمت اصلی)
        with open(filename, 'rb') as audio_file, open(thumb_name, 'rb') as thumb_file:
            await message.reply_audio(
                audio=audio_file,
                caption=f"🎧 {info.get('title', title)}",
                title=info.get('title', title),
                performer="YouTube",
                duration=info.get('duration', duration_sec),
                thumb=thumb_file
            )

        await status_msg.delete()
        # پاکسازی فایل‌ها
        os.remove(filename)
        os.remove(thumb_name)

    except Exception as e:
        await status_msg.edit(f"❌ خطا:\n`{str(e)}`")
        print(f"Error: {e}")

# ---------- اجرای اصلی ----------
def main():
    start_web_server()
    print("🎬 ربات دانلود آهنگ (بدون تبدیل) راه‌اندازی شد...")
    bot.run()

if __name__ == "__main__":
    main()
