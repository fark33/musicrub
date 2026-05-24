FROM python:3.11-slim

WORKDIR /app

# نصب وابستگی‌های سیستمی + Deno (برای حل چالش‌های جاوااسکریپتی یوتیوب)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        wget \
        git \
        ca-certificates \
        curl \
        && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# نصب Deno (موتور جاوااسکریپت مورد نیاز yt-dlp)
RUN curl -fsSL https://deno.land/install.sh | sh && \
    mv /root/.deno/bin/deno /usr/local/bin/deno

# نصب yt-dlp با تمام قابلیت‌ها (شامل حل po_token)
RUN pip install --no-cache-dir --upgrade "yt-dlp[default]"

# کپی فایل نیازمندی‌ها و نصب پکیج‌های پایتون
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی بقیه کدها
COPY . .

# ایجاد پوشه دانلود
RUN mkdir -p downloads

ENV PYTHONUNBUFFERED=1
CMD ["python3", "bot.py"]
