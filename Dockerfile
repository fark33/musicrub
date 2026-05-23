FROM ghcr.io/jim60105/docker-yt-dlp:latest-pot

WORKDIR /app

# نصب پایتون و pip در کنار yt-dlp آماده
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p downloads

ENV PYTHONUNBUFFERED=1
CMD ["python3", "bot.py"]
