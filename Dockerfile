FROM python:3.11-slim

WORKDIR /app

# نصب وابستگی‌های سیستمی + Deno (موتور جاوااسکریپت برای yt-dlp)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        wget \
        unzip \
        git \
        ca-certificates \
        curl \
        && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# نصب Deno (برای حل چالش‌های یوتیوب)
RUN curl -fsSL https://deno.land/install.sh | sh && \
    mv /root/.deno/bin/deno /usr/local/bin/deno

# نصب yt-dlp از طریق pip (بهترین روش، شامل تمام وابستگی‌ها)
RUN pip install --no-cache-dir --upgrade "yt-dlp[default]"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p downloads

ENV PYTHONUNBUFFERED=1
CMD ["python3", "bot.py"]
