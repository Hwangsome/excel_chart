"""
模板渲染层：使用 Jinja2 将数据和 ECharts option 注入 HTML 模板。
"""

import json
import os
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from ..config import TEMPLATE_DIR, CHINESE_FONT_STACK


def render_dashboard(chart_options: dict[str, dict],
                     kpi_cards_rows: list[list[dict]],
                     report_month: int = 5,
                     report_year: int = 2026) -> str:
    """
    渲染完整的仪表盘 HTML 字符串。

    Args:
        chart_options: {"chart_01": {...}, ..., "chart_08": {...}}
        kpi_cards_rows: KPI 卡片行数据
        report_month: 报表月份
        report_year: 报表年份

    Returns:
        完整 HTML 字符串，可直接用浏览器打开或用 Playwright 截图
    """
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("dashboard.html")

    # 将 chart_options 序列化为 JSON，供 ECharts 初始化使用
    chart_options_json = json.dumps(chart_options, ensure_ascii=False, indent=2)

    html = template.render(
        chart_options_json=chart_options_json,
        kpi_cards_rows=kpi_cards_rows,
        report_month=report_month,
        report_year=report_year,
        gen_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        font_stack=CHINESE_FONT_STACK,
    )

    return html


def save_html(html: str, output_dir: str, month: int = 5, year: int = 2026):
    """将 HTML 保存到文件（便于调试）。"""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"dashboard_{year}年{month}月.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path
