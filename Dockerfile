FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی فایل‌های ربات
COPY bot.py .
COPY responses.py .

# متغیر محیطی برای توکن (در زمان اجرا مقداردهی کن)
ENV BOT_TOKEN=""

CMD ["python", "-u", "bot.py"]
