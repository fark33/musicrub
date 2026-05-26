FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی تمام فایل‌ها
COPY bot.py .
COPY responses.py .
COPY question.py .

CMD ["python", "-u", "bot.py"]
