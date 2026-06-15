"""
主控编排器：JSON 输入 → 提取 → 图表构建 → HTML渲染 → 截图输出。

使用方式：
  # JSON 文件（自动检测最新月份）
  cd excel_chart && python -m src.charting.main --json data.json

  # JSON 字符串
  python -m src.charting.main --json '{"output":[...]}'

  # Python API
  from excel_chart.src.charting import MonthlyReportGenerator
  gen = MonthlyReportGenerator(json_data)
  await gen.run()
"""

import argparse
import asyncio
import json as _json
import os
import sys
import logging

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_EXCEL_CHART_DIR = os.path.dirname(os.path.dirname(_THIS_DIR))
_PROJECT_ROOT = os.path.dirname(_EXCEL_CHART_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from excel_chart.src.config import OUTPUT_DIR, DEFAULT_YEAR
from .data_extractor import (
    extract_kpi_cards,
    extract_monthly_series,
    extract_category_sales,
    extract_channel_sales,
    detect_latest_month,
    extract_channel_from_monthly_row,
)
from .chart_data_builder import build_all_chart_options, build_kpi_cards_rows
from .template_renderer import render_dashboard, save_html
from .screenshot import screenshot_dashboard, screenshot_individual_charts
from .json_reader import parse_json_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class MonthlyReportGenerator:
    """月报图表生成器（仅支持 JSON 输入）"""

    def __init__(self, json_data, month: int = None, year: int = DEFAULT_YEAR):
        """
        Args:
            json_data: JSON 对象（dict）或 JSON 字符串，格式 {"output": [...]}
            month: 报表月份 1-12，None = 自动检测最新有数据的月份
            year: 报表年份
        """
        self.json_data = json_data
        self.month = month
        self.year = year

        self.raw_data = {}
        self.chart_options = {}
        self.kpi_data = {}
        self.kpi_cards_rows = []
        self.monthly_series = {}
        self.category_5m = []
        self.category_year = []
        self.channel_5m = []
        self.channel_year = []

    def load_data(self):
        """Step 1: 解析 JSON，自动检测月份"""
        logger.info("Reading JSON data...")

        parsed = parse_json_data(self.json_data)
        self.raw_data = {
            "monthly": parsed["monthly"],
            "category": parsed["category"],
            "channel": parsed["channel"],
        }

        if self.month is None:
            self.month = detect_latest_month(self.raw_data["monthly"])
            logger.info(f"  Auto-detected latest month: {self.month}")

        logger.info(f"  Monthly summary: {len(self.raw_data['monthly'])} rows")
        logger.info(f"  Category sales: {len(self.raw_data['category'])} rows")
        logger.info(f"  Channel sales: {len(self.raw_data['channel'])} rows")

    def extract_data(self):
        """Step 2: 提取图表数据"""
        logger.info("Extracting chart data...")

        self.kpi_data = extract_kpi_cards(self.raw_data["monthly"], self.month)
        logger.info(f"  KPI metrics: {len(self.kpi_data)} items")

        self.monthly_series = extract_monthly_series(self.raw_data["monthly"])

        self.category_5m = extract_category_sales(self.raw_data["category"], month=self.month)
        self.category_year = extract_category_sales(self.raw_data["category"], month=None)
        logger.info(f"  Month-{self.month} categories: {len(self.category_5m)}")
        logger.info(f"  Year categories: {len(self.category_year)}")

        # 渠道：优先 Sheet 2，销售额全空则 fallback 到 Sheet 0 U-X 列
        self.channel_5m = extract_channel_sales(self.raw_data["channel"], month=self.month)
        self.channel_year = extract_channel_sales(self.raw_data["channel"], month=None)

        if sum(r["sales"] for r in self.channel_5m) == 0:
            logger.info("  Channel data missing, fallback to Sheet 0 columns U-X...")
            self.channel_5m = extract_channel_from_monthly_row(self.raw_data["monthly"], month=self.month)
            self.channel_year = extract_channel_from_monthly_row(self.raw_data["monthly"], month=None)

        logger.info(f"  Month-{self.month} channels: {len(self.channel_5m)}")
        logger.info(f"  Year channels: {len(self.channel_year)}")

    def build_charts(self):
        """Step 3: 构建 ECharts option + KPI 卡片"""
        logger.info("Building chart options...")

        self.chart_options = build_all_chart_options(
            self.monthly_series, self.category_5m, self.category_year,
            self.channel_5m, self.channel_year,
        )
        logger.info(f"  Chart configs: {len(self.chart_options)}")

        self.kpi_cards_rows = build_kpi_cards_rows(self.kpi_data)
        logger.info(f"  KPI cards: {sum(len(r) for r in self.kpi_cards_rows)}")

    def render(self) -> str:
        """Step 4: 渲染 HTML"""
        logger.info("Rendering HTML dashboard...")
        html = render_dashboard(self.chart_options, self.kpi_cards_rows,
                                report_month=self.month, report_year=self.year)
        logger.info(f"  HTML size: {len(html):,} chars")
        return html

    async def generate_images(self, html: str, output_dir: str):
        """Step 5: 截图输出"""
        logger.info(f"Screenshot output to: {output_dir}")

        path = await screenshot_dashboard(html, output_dir, month=self.month, year=self.year)
        logger.info(f"  Full dashboard: {path}")

        paths = await screenshot_individual_charts(html, output_dir)
        logger.info(f"  Individual charts: {len(paths)} images")

        html_path = save_html(html, output_dir, month=self.month, year=self.year)
        logger.info(f"  HTML copy: {html_path}")

    async def run(self, output_dir: str = None) -> str:
        """一键执行全流程。"""
        if output_dir is None:
            output_dir = OUTPUT_DIR

        try:
            self.load_data()
        except Exception as e:
            logger.error(f"FAIL: Data loading error: {e}")
            raise

        print("\n" + "=" * 55)
        print(f"  Monthly Report Chart Generator")
        print(f"  Period: {self.year}-{self.month:02d}")
        print("=" * 55 + "\n")

        try:
            self.extract_data()
        except Exception as e:
            logger.error(f"FAIL: Data extraction error: {e}")
            raise
        try:
            self.build_charts()
        except Exception as e:
            logger.error(f"FAIL: Chart building error: {e}")
            raise
        try:
            html = self.render()
        except Exception as e:
            logger.error(f"FAIL: HTML rendering error: {e}")
            raise
        try:
            await self.generate_images(html, output_dir)
        except Exception as e:
            logger.error(f"FAIL: Screenshot error: {e}")
            raise

        print("\n" + "=" * 55)
        print(f"  [DONE] Report generation complete!")
        print(f"  Output: {output_dir}")
        print("=" * 55 + "\n")
        return output_dir


def _resolve_input(raw: str) -> dict:
    """解析 --json 参数：文件路径 或 JSON 字符串"""
    if os.path.isfile(raw):
        with open(raw, "r", encoding="utf-8") as f:
            return _json.load(f)
    try:
        return _json.loads(raw)
    except (_json.JSONDecodeError, ValueError):
        raise ValueError(
            f"Cannot parse --json input: '{raw[:100]}...'\n"
            f"Provide a valid JSON file path or JSON string."
        )


async def main():
    """CLI 入口"""
    parser = argparse.ArgumentParser(
        description="店铺运营月报图表生成工具 — JSON输入 + 自动检测最新月份",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python -m src.charting.main --json data.json
  python -m src.charting.main --json '{"output":[...]}'
  python -m src.charting.main --json data.json --month 6
        """
    )
    parser.add_argument("--json", required=True,
                        help="JSON 文件路径 或 JSON 字符串")
    parser.add_argument("--month", type=int, default=None,
                        help="报表月份 1-12（不指定则自动检测）")
    parser.add_argument("--year", type=int, default=DEFAULT_YEAR,
                        help=f"报表年份（默认: {DEFAULT_YEAR}）")
    parser.add_argument("--output", default=OUTPUT_DIR,
                        help="输出目录（默认: output/）")
    args = parser.parse_args()

    data = _resolve_input(args.json)
    gen = MonthlyReportGenerator(data, month=args.month, year=args.year)
    await gen.run(args.output)


if __name__ == "__main__":
    asyncio.run(main())
