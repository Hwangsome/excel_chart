"""
全局配置：颜色体系、路径、报表参数
匹配原Excel体现表的视觉风格
"""

import os

# 加载 .env 文件（本地开发 / Docker 部署均支持）
try:
    from dotenv import load_dotenv
    _ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(_ENV_PATH):
        load_dotenv(_ENV_PATH)
except ImportError:
    pass

# ============ 路径配置 ============
# __file__ = excel_chart/src/config.py → BASE_DIR = excel_chart/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMPLATE_DIR = os.path.join(BASE_DIR, "src", "templates")

# ============ 颜色体系（匹配原体现表） ============
COLORS = {
    "primary": "#17324D",       # 深蓝主色 — 标题、KPI 卡片左边框、柱状图主色
    "secondary": "#2F6F9F",     # 中蓝辅色 — 次要指标、第二柱状图
    "accent": "#DC473E",        # 红色强调 — 折线图、告警指标
    "success": "#27AE60",       # 绿色 — 正向指标（ROI>1 等）
    "warning": "#F39C12",       # 橙色 — 联盟ROI折线
    "light_bg": "#F5F7FA",      # 浅灰背景
    "card_bg": "#FFFFFF",       # KPI 卡片底色
    "text": "#333333",          # 正文颜色
    "text_light": "#666666",    # 次要文字
    "border": "#E8E8E8",        # 边框颜色
}

# ECharts 饼图多分类色系（10色）
PIE_COLORS = [
    "#17324D", "#2F6F9F", "#DC473E", "#27AE60",
    "#F39C12", "#3498DB", "#9B59B6", "#1ABC9C",
    "#E67E22", "#95A5A6",
]

# ============ 截图配置 ============
SCREENSHOT = {
    "width": 1200,
    "chart_height": 400,
    "dashboard_width": 1200,
    "device_scale_factor": 2.0,   # 2x Retina 清晰度
    "timeout_ms": 30000,          # 页面加载超时
    "max_retries": 3,             # 浏览器启动重试次数
}

# ============ 报表默认参数 ============
DEFAULT_MONTH = 5
DEFAULT_YEAR = 2026

# ============ 阿里云 OSS 配置（通过环境变量注入） ============
import os as _os
OSS_CONFIG = {
    "endpoint": _os.getenv("OSS_ENDPOINT", "oss-cn-hangzhou.aliyuncs.com"),
    "bucket": _os.getenv("OSS_BUCKET", ""),
    "access_key_id": _os.getenv("OSS_ACCESS_KEY_ID", ""),
    "access_key_secret": _os.getenv("OSS_ACCESS_KEY_SECRET", ""),
    "domain": _os.getenv("OSS_DOMAIN", ""),  # 自定义域名/CDN域名，为空则用默认
}

# ============ 中文字体栈 ============
CHINESE_FONT_STACK = (
    '"Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", '
    '"Noto Sans CJK SC", "WenQuanYi Micro Hei", sans-serif'
)

# ============ Sheet 0（月度汇总）中渠道列索引（0-based） ============
CHANNEL_COLS_MONTHLY = {
    "來自商品卡的銷售額": 20,
    "來自直播的銷售額": 21,
    "來自短影音的銷售額": 22,
    "來自蝦皮聯盟行銷的銷售額": 23,
}
