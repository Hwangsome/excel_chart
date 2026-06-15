"""
JSON 数据读取层：解析用户提供的 JSON 输入，转换为统一 dict 格式。

输入 JSON 结构:
{
  "output": [
    { "values": [[header...], [row1...], ...], "displayValues": [[...], ...] },
    ...
  ]
}

9 个 Sheet 的顺序:
  0: 2026每月份销售情况汇总   → monthly
  1: 2026店铺运营概览         → (暂未使用)
  2: 2026各路径销售额汇总     → channel
  3: 2026商品指标             → (暂未使用)
  4: 2026流量总览             → (暂未使用)
  5: 2026广告概览             → (暂未使用)
  6: 2026各类目销售汇总       → category
  7: 每日报表                 → (暂未使用)
  8: 体现表                   → (不需要)

输出格式: 与 excel_reader.read_sheet_as_dicts() 完全一致
  → dict[str, list[dict]]
"""

from typing import Optional


def clean_value(value) -> Optional[float]:
    """
    清洗单元格值，与 excel_reader.clean_value() 行为一致。
    """
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value in ("", "-", "#DIV/0!", "#N/A", "#VALUE!", "#REF!", "#NAME?", "#NUM!"):
            return None
        try:
            return float(value)
        except ValueError:
            return value
    if isinstance(value, (int, float)):
        return value
    return None


def convert_values_to_dicts(values: list[list]) -> list[dict]:
    """
    将二维列表转换为 dict 列表（首行为表头）。

    Args:
        values: [[header1, header2, ...], [val1, val2, ...], ...]

    Returns:
        [{"header1": val1, "header2": val2, ...}, ...]
    """
    if not values or len(values) < 2:
        return []

    # 第一行作为表头
    header_row = values[0]
    # 构建表头：去重后缀避免同名列覆盖
    headers = []
    seen = {}
    for val in header_row:
        key = str(val) if val is not None else f"col_{len(headers)}"
        if key in seen:
            seen[key] += 1
            key = f"{key}_{seen[key]}"
        else:
            seen[key] = 0
        headers.append(key)

    # 遍历数据行构建 dict
    result = []
    for row in values[1:]:
        record = {}
        for i, val in enumerate(row):
            if i < len(headers):
                record[headers[i]] = clean_value(val)
        # 跳过全空行
        if any(v is not None for v in record.values()):
            result.append(record)

    return result


def parse_json_data(json_data) -> dict[str, list[dict]]:
    """
    解析 JSON 输入，返回各 sheet 的 dict 列表。

    Args:
        json_data: JSON 对象（dict）或 JSON 字符串

    Returns:
        {
            "monthly": [{...}, ...],     # Sheet 0: 月度汇总
            "category": [{...}, ...],    # Sheet 6: 类目销售
            "channel": [{...}, ...],     # Sheet 2: 渠道销售
            "raw_monthly_values": [[...], ...],  # Sheet 0 原始二维列表（备用）
        }
    """
    import json as _json

    # 支持 JSON 字符串输入
    if isinstance(json_data, str):
        json_data = _json.loads(json_data)

    output = json_data.get("output", [])
    if not output:
        raise ValueError("JSON 数据中缺少 'output' 字段，或 output 为空数组")

    # 至少需要 Sheet 0（月度汇总）
    if len(output) < 1:
        raise ValueError(f"JSON output 至少需要 1 个 Sheet，实际只有 {len(output)} 个")

    # Sheet 0: 月度汇总
    monthly_sheet = output[0]
    monthly_values = monthly_sheet.get("values", [])
    monthly = convert_values_to_dicts(monthly_values)

    # Sheet 6: 类目销售
    category = []
    if len(output) > 6:
        cat_values = output[6].get("values", [])
        category = convert_values_to_dicts(cat_values)

    # Sheet 2: 渠道销售（可能有列缺失）
    channel = []
    if len(output) > 2:
        chan_values = output[2].get("values", [])
        channel = convert_values_to_dicts(chan_values)

    return {
        "monthly": monthly,
        "category": category,
        "channel": channel,
        "raw_monthly_values": monthly_values,
    }
