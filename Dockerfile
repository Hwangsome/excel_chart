FROM python:3.13-slim

WORKDIR /app

# 系统依赖：Chromium 运行所需 + 中文字体
# 使用阿里云镜像加速 apt（国内网络环境 deb.debian.org 极慢）
RUN sed -i 's|http://deb.debian.org/debian|http://mirrors.aliyun.com/debian|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
    fonts-wqy-microhei \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖（使用阿里云 PyPI 镜像加速）
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r requirements.txt

# 安装 Playwright Chromium（使用 npmmirror 镜像加速）
ENV PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/
RUN playwright install chromium

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

CMD ["uvicorn", "src.service.app:app", "--host", "0.0.0.0", "--port", "8080"]
