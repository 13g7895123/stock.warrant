FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# 安裝 uv
RUN pip install --no-cache-dir uv

# 複製專案檔案
COPY pyproject.toml uv.lock ./
COPY scraper.py run.py ./
COPY config.json config.example.json ./
COPY linebot/ ./linebot/

# 安裝 Python 依賴
RUN uv sync --frozen

# 安裝 Playwright 瀏覽器
RUN uv run playwright install chromium
RUN uv run playwright install-deps chromium

# 暴露 Flask 端口
EXPOSE 5000

# 設定環境變數
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=5000

# 啟動 LINE Bot
CMD ["uv", "run", "python", "-m", "linebot.bot"]
