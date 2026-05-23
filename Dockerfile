FROM python:3.11-slim

WORKDIR /app

# نصب ffmpeg برای پردازش فایل‌های صوتی
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ایجاد پوشه برای فایل‌های موقت
RUN mkdir -p downloads

CMD ["python", "bot.py"]
