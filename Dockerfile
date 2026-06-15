FROM python:3.13-slim

WORKDIR /app

# 系统依赖：Chromium 运行所需 + 中文字体
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-cjk \
    fonts-wqy-microhei \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright Chromium
RUN playwright install chromium && playwright install-deps chromium

# 应用代码
COPY . .

# 输出目录
RUN mkdir -p output

EXPOSE 8080

ENV OSS_ENDPOINT=""
ENV OSS_BUCKET=""
ENV OSS_ACCESS_KEY_ID=""
ENV OSS_ACCESS_KEY_SECRET=""
ENV OSS_DOMAIN=""

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
