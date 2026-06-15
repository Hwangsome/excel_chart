"""
图表配置构建层：将结构化数据转为 ECharts option 字典。

每个 build_chart_XX_option() 返回一个可直接注入 HTML 模板的 ECharts option。
所有图表使用统一的配色方案和视觉风格。
"""

from ..config import COLORS, PIE_COLORS


def _base_bar_option(title: str, x_data: list, series: list,
                     y_axis_configs: list = None) -> dict:
    """构建柱状图/组合图的基础 option 模板。"""
    option = {
        "title": {
            "text": title,
            "left": "center",
            "textStyle": {"color": COLORS["primary"], "fontSize": 16,
                          "fontWeight": "bold"}
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross", "crossStyle": {"color": "#999"}}
        },
        "legend": {
            "data": [s["name"] for s in series],
            "bottom": 0,
            "textStyle": {"fontSize": 11}
        },
        "grid": {
            "left": "3%", "right": "4%", "bottom": "12%", "top": "18%",
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "data": x_data,
            "axisLabel": {"color": COLORS["text"], "fontSize": 11},
            "axisLine": {"lineStyle": {"color": COLORS["border"]}},
        },
        "yAxis": y_axis_configs or [
            {
                "type": "value",
                "nameTextStyle": {"color": COLORS["text_light"]},
                "axisLabel": {"color": COLORS["text_light"]},
                "splitLine": {"lineStyle": {"color": COLORS["border"]}},
            }
        ],
        "series": series,
    }
    return option


def build_chart_01_sales_trend(monthly_series: dict) -> dict:
    """
    图1：月度销售额与同比增长趋势（柱状图 + 双Y轴折线）

    主Y轴（柱）：销售额 (TWD)
    次Y轴（折线）：同比增长率
    """
    months = monthly_series["months"]
    sales = monthly_series["sales"]
    yoy = [round(v * 100, 1) for v in monthly_series["yoy_growth"]]  # 转为百分比

    return _base_bar_option(
        title="2026年销售额与同比增长趋势",
        x_data=months,
        series=[
            {
                "name": "销售额",
                "type": "bar",
                "data": sales,
                "itemStyle": {"color": COLORS["primary"], "borderRadius": [4, 4, 0, 0]},
                "barWidth": "45%",
                "label": {
                    "show": True,
                    "position": "top",
                    "fontSize": 10,
                    "formatter": "{c}",
                    "color": COLORS["text_light"],
                },
            },
            {
                "name": "同比增长率",
                "type": "line",
                "yAxisIndex": 1,
                "data": yoy,
                "lineStyle": {"color": COLORS["accent"], "width": 2.5},
                "itemStyle": {"color": COLORS["accent"]},
                "symbol": "circle",
                "symbolSize": 7,
                "label": {
                    "show": True,
                    "position": "top",
                    "fontSize": 10,
                    "formatter": "{c}%",
                    "color": COLORS["accent"],
                },
            },
        ],
        y_axis_configs=[
            {
                "type": "value",
                "name": "销售额 (TWD)",
                "nameTextStyle": {"color": COLORS["primary"], "fontSize": 11},
                "axisLabel": {
                    "formatter": "{value}",
                    "color": COLORS["primary"],
                },
                "splitLine": {"lineStyle": {"color": COLORS["border"]}},
            },
            {
                "type": "value",
                "name": "同比增长率 (%)",
                "nameTextStyle": {"color": COLORS["accent"], "fontSize": 11},
                "axisLabel": {
                    "formatter": "{value}%",
                    "color": COLORS["accent"],
                },
                "splitLine": {"show": False},
            },
        ],
    )


def build_chart_02_orders_conversion(monthly_series: dict) -> dict:
    """
    图2：订单数与转化率趋势（柱状图 + 双Y轴折线）

    主Y轴（柱）：订单总数
    次Y轴（折线）：转化率 (%)
    """
    months = monthly_series["months"]
    orders = monthly_series["order_count"]
    conversion = [round(v * 100, 2) for v in monthly_series["conversion_rate"]]

    return _base_bar_option(
        title="2026年订单数与转化率趋势",
        x_data=months,
        series=[
            {
                "name": "订单总数",
                "type": "bar",
                "data": orders,
                "itemStyle": {"color": COLORS["secondary"],
                              "borderRadius": [4, 4, 0, 0]},
                "barWidth": "45%",
                "label": {
                    "show": True,
                    "position": "top",
                    "fontSize": 10,
                    "color": COLORS["text_light"],
                },
            },
            {
                "name": "转化率",
                "type": "line",
                "yAxisIndex": 1,
                "data": conversion,
                "lineStyle": {"color": COLORS["accent"], "width": 2.5},
                "itemStyle": {"color": COLORS["accent"]},
                "symbol": "circle",
                "symbolSize": 7,
                "label": {
                    "show": True,
                    "position": "top",
                    "fontSize": 10,
                    "formatter": "{c}%",
                    "color": COLORS["accent"],
                },
            },
        ],
        y_axis_configs=[
            {
                "type": "value",
                "name": "订单总数 (单)",
                "nameTextStyle": {"color": COLORS["secondary"], "fontSize": 11},
                "axisLabel": {"color": COLORS["secondary"]},
                "splitLine": {"lineStyle": {"color": COLORS["border"]}},
            },
            {
                "type": "value",
                "name": "转化率 (%)",
                "nameTextStyle": {"color": COLORS["accent"], "fontSize": 11},
                "axisLabel": {"formatter": "{value}%", "color": COLORS["accent"]},
                "splitLine": {"show": False},
            },
        ],
    )


def build_chart_03_ad_roi(monthly_series: dict) -> dict:
    """
    图3：广告GMV、联盟GMV与ROI（分组柱状图 + 双Y轴折线）

    主Y轴（柱）：广告GMV、联盟GMV
    次Y轴（折线）：广告ROI、联盟ROI
    """
    months = monthly_series["months"]
    ad_gmv = monthly_series["ad_gmv"]
    alliance_gmv = monthly_series["alliance_gmv"]
    ad_roi = [round(v, 2) for v in monthly_series["ad_roi"]]
    alliance_roi = [round(v, 2) for v in monthly_series["alliance_roi"]]

    return _base_bar_option(
        title="2026年广告投放GMV与ROI趋势",
        x_data=months,
        series=[
            {
                "name": "虾皮广告GMV",
                "type": "bar",
                "data": ad_gmv,
                "itemStyle": {"color": COLORS["primary"],
                              "borderRadius": [4, 4, 0, 0]},
                "barGap": "10%",
                "barWidth": "35%",
                "label": {
                    "show": True,
                    "position": "top",
                    "fontSize": 10,
                    "formatter": "{c}",
                    "color": COLORS["text_light"],
                },
            },
            {
                "name": "联盟营销GMV",
                "type": "bar",
                "data": alliance_gmv,
                "itemStyle": {"color": COLORS["secondary"],
                              "borderRadius": [4, 4, 0, 0]},
                "barWidth": "35%",
            },
            {
                "name": "虾皮ROI",
                "type": "line",
                "yAxisIndex": 1,
                "data": ad_roi,
                "lineStyle": {"color": COLORS["warning"], "width": 2.5},
                "itemStyle": {"color": COLORS["warning"]},
                "symbol": "diamond",
                "symbolSize": 8,
            },
            {
                "name": "联盟ROI",
                "type": "line",
                "yAxisIndex": 1,
                "data": alliance_roi,
                "lineStyle": {"color": COLORS["success"], "width": 2.5},
                "itemStyle": {"color": COLORS["success"]},
                "symbol": "triangle",
                "symbolSize": 9,
            },
        ],
        y_axis_configs=[
            {
                "type": "value",
                "name": "GMV (TWD)",
                "nameTextStyle": {"color": COLORS["primary"], "fontSize": 11},
                "axisLabel": {"color": COLORS["primary"]},
                "splitLine": {"lineStyle": {"color": COLORS["border"]}},
            },
            {
                "type": "value",
                "name": "ROI",
                "nameTextStyle": {"color": COLORS["success"], "fontSize": 11},
                "axisLabel": {"color": COLORS["success"]},
                "splitLine": {"show": False},
            },
        ],
    )


def build_chart_04_followers(monthly_series: dict) -> dict:
    """
    图4：每月新增粉丝趋势（单柱状图）
    """
    months = monthly_series["months"]
    followers = monthly_series["new_followers"]

    return _base_bar_option(
        title="2026年每月新增粉丝数量",
        x_data=months,
        series=[
            {
                "name": "新增粉丝",
                "type": "bar",
                "data": followers,
                "itemStyle": {"color": COLORS["primary"],
                              "borderRadius": [4, 4, 0, 0]},
                "barWidth": "40%",
                "label": {
                    "show": True,
                    "position": "top",
                    "fontSize": 11,
                    "fontWeight": "bold",
                    "color": COLORS["primary"],
                },
            },
        ],
        y_axis_configs=[
            {
                "type": "value",
                "name": "粉丝数 (人)",
                "nameTextStyle": {"color": COLORS["text_light"], "fontSize": 11},
                "axisLabel": {"color": COLORS["text_light"]},
                "splitLine": {"lineStyle": {"color": COLORS["border"]}},
            },
        ],
    )


def _build_pie_option(title: str, data: list[dict],
                      name_field: str = "category",
                      value_field: str = "sales") -> dict:
    """
    构建饼图 option 的通用模板。

    Args:
        title: 图表标题
        data: [{"name_field": "xxx", "sales": NNN, "percentage": 0.XX}, ...]
        name_field: 名称字段名
        value_field: 值字段名
    """
    pie_data = []
    for i, item in enumerate(data):
        label = item.get(name_field, "")
        # 截断过长的标签
        if len(label) > 12:
            label = label[:10] + "..."

        pie_data.append({
            "value": round(item[value_field], 1),
            "name": label,
            "itemStyle": {"color": PIE_COLORS[i % len(PIE_COLORS)]},
        })

    return {
        "title": {
            "text": title,
            "left": "center",
            "textStyle": {"color": COLORS["primary"], "fontSize": 16,
                          "fontWeight": "bold"}
        },
        "tooltip": {
            "trigger": "item",
            "formatter": "{b}: {c} TWD ({d}%)",
        },
        "legend": {
            "orient": "vertical",
            "left": "left",
            "top": "middle",
            "type": "scroll",
            "textStyle": {"fontSize": 10},
        },
        "series": [
            {
                "type": "pie",
                "radius": ["40%", "70%"],  # 环形图
                "center": ["55%", "55%"],
                "avoidLabelOverlap": True,
                "itemStyle": {
                    "borderRadius": 4,
                    "borderColor": "#fff",
                    "borderWidth": 2,
                },
                "label": {
                    "formatter": "{d}%",
                    "fontSize": 10,
                    "color": COLORS["text"],
                },
                "emphasis": {
                    "label": {"fontSize": 14, "fontWeight": "bold"},
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.3)",
                    },
                },
                "data": pie_data,
            }
        ],
    }


def build_chart_05_category_5m(category_5m: list[dict]) -> dict:
    """图5：5月品类销售结构（环形饼图）"""
    return _build_pie_option("5月各品类销售占比", category_5m, "category", "sales")


def build_chart_06_category_year(category_year: list[dict]) -> dict:
    """图6：全年品类销售结构（环形饼图）"""
    return _build_pie_option("2026年各品类销售占比", category_year, "category", "sales")


def build_chart_07_channel_5m(channel_5m: list[dict]) -> dict:
    """图7：5月渠道销售结构（环形饼图）"""
    return _build_pie_option("5月各渠道GMV占比", channel_5m, "channel", "sales")


def build_chart_08_channel_year(channel_year: list[dict]) -> dict:
    """图8：全年渠道销售结构（环形饼图）"""
    return _build_pie_option("2026年各渠道GMV占比", channel_year, "channel", "sales")


def build_all_chart_options(monthly_series: dict,
                            category_5m: list[dict],
                            category_year: list[dict],
                            channel_5m: list[dict],
                            channel_year: list[dict]) -> dict[str, dict]:
    """
    构建所有 8 个图表的 ECharts option。

    Returns:
        {"chart_01": {...}, "chart_02": {...}, ..., "chart_08": {...}}
    """
    return {
        "chart_01": build_chart_01_sales_trend(monthly_series),
        "chart_02": build_chart_02_orders_conversion(monthly_series),
        "chart_03": build_chart_03_ad_roi(monthly_series),
        "chart_04": build_chart_04_followers(monthly_series),
        "chart_05": build_chart_05_category_5m(category_5m),
        "chart_06": build_chart_06_category_year(category_year),
        "chart_07": build_chart_07_channel_5m(channel_5m),
        "chart_08": build_chart_08_channel_year(channel_year),
    }


def build_kpi_cards_rows(kpi: dict) -> list[list[dict]]:
    """
    将 KPI 数据格式化为模板友好的卡片行结构。

    Returns:
        [
            [  # 第1行：核心指标
                {"label": "5月销售额", "value": "88,626", "unit": "TWD", "style": "primary"},
                ...
            ],
            [  # 第2行：广告指标
                ...
            ],
            [  # 第3行：运营指标
                ...
            ],
        ]
    """

    def fmt_num(v, decimals=0) -> str:
        """格式化数字，添加千分位逗号。"""
        if v is None:
            return "--"
        return f"{v:,.{decimals}f}"

    def fmt_pct(v) -> str:
        """格式化百分比。"""
        if v is None:
            return "--"
        return f"{round(v * 100, 1)}"

    def fmt_roi(v) -> str:
        """格式化ROI。"""
        if v is None:
            return "--"
        return f"{v:.2f}"

    # 第1行：核心经营指标
    row1 = [
        {"label": "5月销售额", "value": fmt_num(kpi.get("month_sales")),
         "unit": "TWD", "style": "primary"},
        {"label": "月同比增长率", "value": fmt_pct(kpi.get("yoy_growth")),
         "unit": "%", "style": "accent"},
        {"label": "目标达成率", "value": fmt_pct(kpi.get("target_achievement")),
         "unit": "%", "style": "secondary"},
        {"label": "订单总数", "value": fmt_num(kpi.get("order_count")),
         "unit": "单", "style": "primary"},
        {"label": "客单价", "value": fmt_num(kpi.get("avg_order_value"), 1),
         "unit": "TWD", "style": "secondary"},
    ]

    # 第2行：广告投放效果
    row2 = [
        {"label": "虾皮广告GMV", "value": fmt_num(kpi.get("ad_gmv"), 1),
         "unit": "TWD", "style": "primary"},
        {"label": "广告转化率", "value": fmt_pct(kpi.get("ad_conversion")),
         "unit": "%", "style": "secondary"},
        {"label": "广告ROI", "value": fmt_roi(kpi.get("ad_roi")),
         "unit": "", "style": "accent"},
        {"label": "广告花费", "value": fmt_num(kpi.get("ad_cost"), 1),
         "unit": "TWD", "style": "secondary"},
        {"label": "联盟GMV", "value": fmt_num(kpi.get("alliance_gmv"), 1),
         "unit": "TWD", "style": "primary"},
        {"label": "联盟转化率", "value": fmt_pct(kpi.get("alliance_conversion")),
         "unit": "%", "style": "secondary"},
        {"label": "联盟ROI", "value": fmt_roi(kpi.get("alliance_roi")),
         "unit": "", "style": "accent"},
        {"label": "达人佣金", "value": fmt_num(kpi.get("alliance_commission"), 1),
         "unit": "TWD", "style": "secondary"},
    ]

    # 第3行：运营效率指标
    row3 = [
        {"label": "推广费占比", "value": fmt_pct(kpi.get("promo_cost_ratio")),
         "unit": "%", "style": "accent"},
        {"label": "订单转化率", "value": fmt_pct(kpi.get("conversion_rate")),
         "unit": "%", "style": "secondary"},
        {"label": "回购率", "value": fmt_pct(kpi.get("repurchase_rate")),
         "unit": "%", "style": "secondary"},
        {"label": "退货率", "value": fmt_pct(kpi.get("refund_rate")),
         "unit": "%", "style": "secondary"},
        {"label": "加购率", "value": fmt_pct(kpi.get("add_cart_rate")),
         "unit": "%", "style": "secondary"},
        {"label": "新增粉丝", "value": fmt_num(kpi.get("new_followers")),
         "unit": "人", "style": "primary"},
        {"label": "退货金额", "value": fmt_num(kpi.get("refund_amount")),
         "unit": "TWD", "style": "secondary"},
    ]

    return [row1, row2, row3]
