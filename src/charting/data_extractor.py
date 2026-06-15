"""
数据提取层：从清洗后的工作表数据中，按图表维度提取所需数据。

每个 extract_xxx() 函数对应一个图表或一组 KPI 的数据提取。
输出结构化的 dict/list，供 chart_data_builder 直接使用。
"""

from typing import Optional

from ..config import DEFAULT_MONTH
from .excel_reader import safe_float


def detect_latest_month(monthly_data: list[dict]) -> int:
    """
    从月度汇总表中自动检测有数据的最新月份。

    遍历所有行，找到 "月销售额" > 0 且月份数字最大的那个月。
    如果没有任何月份有数据，fallback 到 DEFAULT_MONTH。

    Args:
        monthly_data: read_sheet_as_dicts() 或 json_reader 返回的月度汇总数据

    Returns:
        月份数字 (1-12)
    """
    latest_month = None

    for row in monthly_data:
        month_str = str(row.get("月份", "")).strip()
        if not month_str.endswith("月"):
            continue

        try:
            month_num = int(month_str.replace("月", ""))
        except ValueError:
            continue

        sales_val = row.get("月销售额")
        sales = safe_float(sales_val) if sales_val not in (None, "", 0) else 0

        if sales > 0 and (latest_month is None or month_num > latest_month):
            latest_month = month_num

    return latest_month if latest_month is not None else DEFAULT_MONTH


def extract_channel_from_monthly_row(
    monthly_data: list[dict],
    month: Optional[int] = None,
) -> list[dict]:
    """
    从月度汇总表（Sheet 0）的渠道列（U-X）中提取渠道销售额。

    这是 extract_channel_sales() 的替代数据源，
    适用于 Sheet "2026各路径销售额汇总" 中销售额列缺失的情况。

    Sheet 0 的 4 个渠道列:
      - 來自商品卡的銷售額 (Col U)
      - 來自直播的銷售額 (Col V)
      - 來自短影音的銷售額 (Col W)
      - 來自蝦皮聯盟行銷的銷售額 (Col X)

    Args:
        monthly_data: Sheet 0 的 dict 列表
        month: 筛选月份，None 表示全年汇总（所有月份求和）

    Returns:
        [{"channel": "來自商品卡的銷售額", "sales": 77897, "percentage": 0.879}, ...]
        按 sales 降序排列
    """
    CHANNEL_NAMES = [
        "來自商品卡的銷售額",
        "來自直播的銷售額",
        "來自短影音的銷售額",
        "來自蝦皮聯盟行銷的銷售額",
    ]

    target_month = f"{month}月" if month else None

    agg = {name: 0.0 for name in CHANNEL_NAMES}

    for row in monthly_data:
        if target_month is not None:
            month_val = str(row.get("月份", "")).strip()
            if month_val != target_month:
                continue

        for name in CHANNEL_NAMES:
            agg[name] += safe_float(row.get(name))

    result = [
        {"channel": name, "sales": sales, "percentage": 0.0}
        for name, sales in agg.items()
        if sales > 0
    ]

    result.sort(key=lambda x: x["sales"], reverse=True)

    total = sum(r["sales"] for r in result)
    if total > 0:
        for r in result:
            r["percentage"] = round(r["sales"] / total, 4)

    return result


def extract_kpi_cards(monthly_data: list[dict], month: int = 5) -> dict:
    """
    从月度汇总表中提取指定月份的 KPI 卡片数据。

    Args:
        monthly_data: read_sheet_as_dicts() 返回的月度汇总数据
        month: 目标月份 (1-12)

    Returns:
        {
            "month_sales": 88626,           # 月销售额 (TWD)
            "yoy_growth": 2.976,            # 月同比增长率
            "target_achievement": 0.5908,   # 目标达成率
            "order_count": 221,             # 月订单总数
            "avg_order_value": 401.02,      # 客单价 (TWD)
            "refund_amount": 1019,          # 退货金额 (TWD)
            "new_followers": 315,           # 新增粉丝数
            "conversion_rate": 0.0114,      # 订单转化率
            "repurchase_rate": 0.0384,      # 回购率
            "refund_rate": 0.00905,         # 退货率
            "add_cart_rate": 0.0512,        # 加购率
            "promo_cost_ratio": 0.2157,     # 推广费占比
            "ad_gmv": 68601.35,             # 虾皮广告GMV
            "ad_conversion": 0.054,         # 虾皮广告转化率
            "ad_roi": 4.1625,               # 虾皮广告ROI
            "ad_cost": 16480.71,            # 虾皮广告花费
            "alliance_gmv": 8818,           # 联盟GMV
            "alliance_conversion": 0.4581,  # 联盟转化率
            "alliance_roi": 39.8644,        # 联盟ROI
            "alliance_commission": 221.2,   # 联盟达人佣金
        }
    """
    target_month_str = f"{month}月"
    row = None
    for r in monthly_data:
        month_val = str(r.get("月份", "")).strip()
        if month_val == target_month_str:
            row = r
            break

    if row is None:
        raise ValueError(
            f"月度汇总表中未找到 '{target_month_str}' 的数据行"
        )

    return {
        "month_sales": safe_float(row.get("月銷售額")),
        "yoy_growth": safe_float(row.get("月同比銷售額增长率")),
        "target_achievement": safe_float(row.get("目标达成率")),
        "order_count": int(safe_float(row.get("月訂單總數"))),
        "avg_order_value": safe_float(row.get("客单价")),
        "refund_amount": safe_float(row.get("退貨金额")),
        "new_followers": int(safe_float(row.get("新的粉絲數"))),
        "conversion_rate": safe_float(row.get("訂單轉換率")),
        "repurchase_rate": safe_float(row.get("回購率")),
        "refund_rate": safe_float(row.get("退货率")),
        "add_cart_rate": safe_float(row.get("加购率")),
        "promo_cost_ratio": safe_float(row.get("推广费用总占比")),
        "ad_gmv": safe_float(row.get("广告GMV")),
        "ad_conversion": safe_float(row.get("广告轉換率")),
        "ad_roi": safe_float(row.get("投入產出比")),
        "ad_cost": safe_float(row.get("广告花费")),
        "alliance_gmv": safe_float(row.get("联盟GMV")),
        "alliance_conversion": safe_float(row.get("联盟转化率")),
        "alliance_roi": safe_float(row.get("投入產出比_1")),  # 联盟ROI列
        "alliance_commission": safe_float(row.get("达人佣金")),
    }


def extract_monthly_series(monthly_data: list[dict]) -> dict:
    """
    从月度汇总表提取所有月份的序列数据。

    Returns:
        {
            "months": ["1月", ..., "12月"],
            "sales": [0, 0, 0, 22288, 88626, ...],           # 月销售额
            "yoy_growth": [...],                               # 月同比增长率
            "order_count": [...],                              # 月订单总数
            "conversion_rate": [...],                          # 订单转化率
            "avg_order_value": [...],                          # 客单价
            "ad_gmv": [...],                                   # 虾皮广告GMV
            "alliance_gmv": [...],                             # 联盟GMV
            "ad_roi": [...],                                   # 虾皮广告ROI
            "alliance_roi": [...],                             # 联盟ROI
            "new_followers": [...],                            # 新增粉丝
        }
    """
    months = [f"{i}月" for i in range(1, 13)]
    result = {
        "months": months,
        "sales": [0.0] * 12,
        "yoy_growth": [0.0] * 12,
        "order_count": [0] * 12,
        "conversion_rate": [0.0] * 12,
        "avg_order_value": [0.0] * 12,
        "ad_gmv": [0.0] * 12,
        "alliance_gmv": [0.0] * 12,
        "ad_roi": [0.0] * 12,
        "alliance_roi": [0.0] * 12,
        "new_followers": [0] * 12,
    }

    # 构建月份到索引的映射
    for row in monthly_data:
        month_str = str(row.get("月份", "")).strip()
        if month_str in months:
            idx = months.index(month_str)
            result["sales"][idx] = safe_float(row.get("月銷售額"))
            result["yoy_growth"][idx] = safe_float(row.get("月同比銷售額增长率"))
            result["order_count"][idx] = int(safe_float(row.get("月訂單總數")))
            result["conversion_rate"][idx] = safe_float(row.get("訂單轉換率"))
            result["avg_order_value"][idx] = safe_float(row.get("客单价"))
            result["ad_gmv"][idx] = safe_float(row.get("广告GMV"))
            result["alliance_gmv"][idx] = safe_float(row.get("联盟GMV"))
            result["ad_roi"][idx] = safe_float(row.get("投入產出比"))
            result["alliance_roi"][idx] = safe_float(row.get("投入產出比_1"))
            result["new_followers"][idx] = int(safe_float(row.get("新的粉絲數")))

    return result


def extract_category_sales(category_data: list[dict],
                           month: Optional[int] = None) -> list[dict]:
    """
    从类目销售汇总表提取数据。

    Args:
        category_data: 类目销售汇总的 dict 列表
        month: 筛选月份，None 表示全年汇总

    Returns:
        [{"category": "日用品", "sales": 40683, "percentage": 0.4766}, ...]
        按 sales 降序排列
    """
    target_month = f"{month}月" if month else None

    # 聚合数据
    agg = {}
    for row in category_data:
        if target_month is not None:
            month_val = str(row.get("月份", "")).strip()
            if month_val != target_month:
                continue

        cat = row.get("子分類")
        if cat is None or str(cat).strip() == "":
            continue

        cat = str(cat).strip()
        sales = safe_float(row.get("銷售 (TWD)"))
        percentage = safe_float(row.get("銷售額百分比"))

        if cat in agg:
            agg[cat]["sales"] += sales
            agg[cat]["percentage"] += percentage
        else:
            agg[cat] = {"category": cat, "sales": sales, "percentage": percentage}

    result = list(agg.values())

    # 过滤掉销售额为0的类目
    result = [r for r in result if r["sales"] > 0]

    # 按销售额降序排列
    result.sort(key=lambda x: x["sales"], reverse=True)

    # 重新计算占比（确保准确性）
    total = sum(r["sales"] for r in result)
    if total > 0:
        for r in result:
            r["percentage"] = round(r["sales"] / total, 4)

    return result


def extract_channel_sales(channel_data: list[dict],
                          month: Optional[int] = None) -> list[dict]:
    """
    从各路径销售额汇总表提取数据。

    Args:
        channel_data: 渠道销售汇总的 dict 列表
        month: 筛选月份，None 表示全年汇总

    Returns:
        [{"channel": "來自商品卡的銷售額", "sales": 77897, "percentage": 0.879}, ...]
        按 sales 降序排列
    """
    target_month = f"{month}月" if month else None

    agg = {}
    for row in channel_data:
        if target_month is not None:
            month_val = str(row.get("月份", "")).strip()
            if month_val != target_month:
                continue

        channel = row.get("分类")
        if channel is None or str(channel).strip() == "":
            continue

        channel = str(channel).strip()
        sales = safe_float(row.get("销售额"))

        if channel in agg:
            agg[channel]["sales"] += sales
        else:
            agg[channel] = {"channel": channel, "sales": sales, "percentage": 0.0}

    result = list(agg.values())

    # 过滤销售额为0的渠道
    result = [r for r in result if r["sales"] > 0]

    # 按销售额降序排列
    result.sort(key=lambda x: x["sales"], reverse=True)

    # 计算占比
    total = sum(r["sales"] for r in result)
    if total > 0:
        for r in result:
            r["percentage"] = round(r["sales"] / total, 4)

    return result
