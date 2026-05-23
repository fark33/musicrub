FROM python:3.11-slim

WORKDIR /app

# نصب وابستگی‌های سیستم، از جمله wget برای دانلود و ffmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# دانلود و تنظیم فایل باینری از پیش کامپایل شده PO Token Provider
# آدرس لینک برای پردازنده‌های 64 بیتی (x86_64) تنظیم شده است.
RUN wget -q https://github.com/jim60105/bgutil-ytdlp-pot-provider-rs/releases/latest/download/bgutil-pot-linux-x86_64 && \
    chmod +x bgutil-pot-linux-x86_64 && \
    mv bgutil-pot-linux-x86_64 /usr/local/bin/bgutil-pot

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p downloads

ENV PYTHONUNBUFFERED=1
CMD ["python", "bot.py"]
