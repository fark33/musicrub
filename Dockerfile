FROM python:3.11-slim

# متغیرهای محیطی برای Rust/Cargo
ENV PATH="/root/.cargo/bin:${PATH}"

# نصب وابستگی‌های سیستم، ffmpeg، curl، و ابزارهای Rust
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg curl build-essential pkg-config libssl-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    rustup update

WORKDIR /app

# کلون و نصب تولیدکننده توکن (bgutil-ytdlp-pot-provider-rs)
RUN git clone https://github.com/jim60105/bgutil-ytdlp-pot-provider-rs.git && \
    cd bgutil-ytdlp-pot-provider-rs && \
    cargo build --release && \
    cp target/release/bgutil-ytdlp-pot-provider-rs /usr/local/bin/ && \
    cd /app && rm -rf bgutil-ytdlp-pot-provider-rs

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p downloads

ENV PYTHONUNBUFFERED=1
CMD ["python", "bot.py"]
