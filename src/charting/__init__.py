"""
方案C：JSON → ECharts → 图表图片

架构：
  JSON → [json_reader] → 清洗数据 → [data_extractor] → 结构化数据
       → [chart_data_builder] → ECharts option
       → [template_renderer] → HTML Dashboard
       → [screenshot] → PNG

使用方式：
  cd excel_chart && python -m src.charting.main --json data.json
"""

from .main import MonthlyReportGenerator

__all__ = ["MonthlyReportGenerator"]
