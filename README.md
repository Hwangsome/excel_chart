# 店铺运营月报图表生成服务

接收 Shopee 运营 JSON 数据，生成 **8 张高清图表 + KPI 仪表盘**，上传到阿里云 OSS，返回访问 URL。可作为 Dify 代码节点的下游服务调用。

---

## 目录结构

```
excel_chart/
├── requirements.txt          # 服务依赖
├── Dockerfile                # Docker 部署
├── README.md
├── data/
│   └── input.json            # 测试数据
├── src/
│   ├── config.py             # 全局配置（颜色、路径、OSS、截图参数）
│   ├── charting/
│   │   ├── __init__.py
│   │   ├── json_reader.py    # JSON 解析 + 数据清洗
│   │   ├── data_extractor.py # 图表数据提取 + 自动检测月份 + 渠道 fallback
│   │   ├── chart_data_builder.py # 构建 8 个 ECharts option + KPI 卡片
│   │   ├── template_renderer.py  # Jinja2 渲染 HTML
│   │   ├── screenshot.py     # Playwright 截图
│   │   └── main.py           # 主控编排
│   ├── service/
│   │   ├── __init__.py
│   │   └── app.py            # FastAPI 服务入口
│   └── templates/
│       └── dashboard.html    # ECharts 仪表盘 HTML 模板
└── output/                   # 本地输出（服务模式下使用临时目录）
```

---

## 技术架构

```
POST /generate
  │
  ▼
JSON → [json_reader] → [data_extractor] → [chart_data_builder]
  │                                            │
  │                                     ECharts option dict
  │                                            │
  │                                     [template_renderer]
  │                                            │
  │                                     HTML Dashboard
  │                                            │
  │                                     [screenshot]
  │                                            │
  │                                     9 张 PNG (临时目录)
  │                                            │
  ▼                                            ▼
阿里云 OSS ←──────────────────────────────────┘
  │
  ▼
Response: { dashboard_url, charts: [...], kpi: {...} }
```

---

## 快速开始

### 环境要求

- Python 3.10+
- Playwright Chromium 浏览器
- 中文字体（Linux 需安装 `fonts-noto-cjk`）

### 1. 安装

```bash
cd excel_chart
pip install -r requirements.txt
playwright install chromium
```

### 2. 配置 OSS 环境变量

```bash
export OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
export OSS_BUCKET=your-bucket-name
export OSS_ACCESS_KEY_ID=LTAI5txxxxxxxx
export OSS_ACCESS_KEY_SECRET=xxxxxxxxxxxxxxxx
export OSS_DOMAIN=cdn.example.com        # 可选，自定义域名
```

### 3. 启动服务

```bash
uvicorn src.service.app:app --host 0.0.0.0 --port 8080 --reload
```

### 4. 调用

```bash
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{"data": {"output": [...]}, "month": null}'
```

---

## API 接口

### `GET /health`

健康检查。

```json
{"status": "ok", "timestamp": "2026-06-15T12:00:00"}
```

### `GET /oss/status`

检查 OSS 配置状态。

```json
{"configured": true, "bucket": "my-bucket", "endpoint": "oss-cn-hangzhou.aliyuncs.com"}
```

### `POST /generate`

生成月报图表 → 截图 → 上传 OSS。

**Request:**

```json
{
  "data": {"output": [...]},
  "month": null,
  "year": 2026,
  "upload_to_oss": true
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `data` | object | ✅ | JSON 数据，格式 `{"output": [Sheet0, Sheet1, ...]}` |
| `month` | int/null | | 报表月份 1-12，`null` 自动检测最新数据月份 |
| `year` | int | | 报表年份，默认 2026 |
| `upload_to_oss` | bool | | 是否上传 OSS。`false` 返回本地路径（调试用） |

**Response:**

```json
{
  "success": true,
  "month": 5,
  "year": 2026,
  "dashboard_url": "https://oss.example.com/reports/2026/05/2026-06-15/abc12345/dashboard_2026年5月.png",
  "charts": [
    {"id": "chart_01", "title": "月度销售额与同比增长趋势", "url": "https://..."},
    {"id": "chart_02", "title": "订单数与转化率趋势", "url": "https://..."},
    {"id": "chart_03", "title": "广告投放GMV与ROI趋势", "url": "https://..."},
    {"id": "chart_04", "title": "每月新增粉丝数量", "url": "https://..."},
    {"id": "chart_05", "title": "当月各品类销售占比", "url": "https://..."},
    {"id": "chart_06", "title": "全年各品类销售占比", "url": "https://..."},
    {"id": "chart_07", "title": "当月各渠道GMV占比", "url": "https://..."},
    {"id": "chart_08", "title": "全年各渠道GMV占比", "url": "https://..."}
  ],
  "kpi": {
    "month_sales": 88626,
    "yoy_growth": 2.98,
    "target_achievement": 0.59,
    "order_count": 221,
    "avg_order_value": 401,
    "new_followers": 315,
    "conversion_rate": 0.011,
    "ad_gmv": 68601.35,
    "ad_roi": 4.2,
    "alliance_gmv": 8818,
    "alliance_roi": 39.9,
    ...
  },
  "oss_prefix": "reports/2026/05/2026-06-15/abc12345",
  "elapsed_seconds": 9.8
}
```

---

## Docker 部署

```bash
docker build -t chart-service .

docker run -p 8080:8080 \
  -e OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com \
  -e OSS_BUCKET=your-bucket \
  -e OSS_ACCESS_KEY_ID=xxx \
  -e OSS_ACCESS_KEY_SECRET=xxx \
  -e OSS_DOMAIN=cdn.example.com \
  chart-service
```

---

## Dify 集成

```
┌─ Dify 工作流 ────────────────────────┐
│                                       │
│  [Code 节点]                          │
│   组装请求 JSON                        │
│   output = {"data": {...}}            │
│       │                               │
│       ▼                               │
│  [HTTP Request 节点]                  │
│   POST https://chart-service/generate │
│   Body: {{Code节点.output}}           │
│       │                               │
│       ▼                               │
│  [Answer 节点]                        │
│   用 OSS URL 拼 Markdown              │
│   ![图表]({{dashboard_url}})          │
│   → 推送到钉钉                         │
└───────────────────────────────────────┘
```

---

## 资源清单与权限申请

部署本服务需要以下云资源，请按清单逐项申请开通。

### 1. 阿里云 OSS（对象存储）

**用途**：存储生成的仪表盘 PNG 图片，提供公网访问 URL 供钉钉/Dify 使用。

| 申请项 | 说明 |
|--------|------|
| **产品** | 阿里云 对象存储 OSS |
| **Bucket 名称** | 自定义，如 `shopee-monthly-report` |
| **地域** | 建议 `华东1（杭州）`，与 ECS/Dify 同地域以降低延迟 |
| **存储类型** | 标准存储 |
| **读写权限** | **公共读**（图片需公网可访问）或 **私有**（通过签名 URL 访问） |

#### 申请步骤

1. 登录 [阿里云控制台](https://oss.console.aliyun.com/)
2. 点击 **Bucket 列表** → **创建 Bucket**
3. 填写 Bucket 名称，选择地域，存储类型选「标准存储」
4. 读写权限选「**公共读**」
   > ⚠️ 若担心数据安全，可选「私有」+ 开启 CDN 签名鉴权，但需额外配置
5. 点击确定，完成创建

#### 费用估算

| 计费项 | 量级（月） | 单价 | 月费 |
|--------|:---------:|------|:-----:|
| 存储容量 | ~3 MB/天 × 30 = 90 MB | ¥0.12/GB | < ¥0.01 |
| 外网流出流量 | ~3 MB/天 × 30 = 90 MB | ¥0.25-0.50/GB | < ¥0.05 |
| Put 请求 | ~10 次/天 × 30 = 300 次 | ¥0.01/万次 | < ¥0.01 |
| **合计** | | | **< ¥1/月** |

> 费用极低，按量计费即可，无需购买资源包。

---

### 2. RAM 访问控制（AccessKey）

**用途**：服务通过 AccessKey 上传图片到 OSS。

| 申请项 | 说明 |
|--------|------|
| **产品** | 阿里云 RAM 访问控制 |
| **账号类型** | **子账号（RAM 用户）**，不要使用主账号 |
| **授权策略** | `AliyunOSSFullAccess` 或自定义最小权限策略 |
| **需要保存** | AccessKey ID + AccessKey Secret（仅创建时显示一次） |

#### 申请步骤

1. 登录 [RAM 控制台](https://ram.console.aliyun.com/)
2. **用户** → **创建用户** → 填写登录名称，勾选「OpenAPI 调用访问」
3. 创建成功后，**立即保存 AccessKey ID 和 Secret**（关闭后不可找回）
4. **授权** → 添加权限 → 选择 `AliyunOSSFullAccess`
   > 或创建最小权限自定义策略（仅允许上传到指定 Bucket）：

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["oss:PutObject", "oss:GetObject"],
      "Resource": "acs:oss:*:*:shopee-monthly-report/reports/*"
    }
  ]
}
```

---

### 3. ECS / Docker 运行环境

**用途**：部署图表生成服务容器。

| 方案 | 配置建议 | 月费 |
|------|----------|:---:|
| 阿里云 ECS | 2核4G，系统盘 40GB，CentOS 7+ / Ubuntu 20.04+ | ~¥100-200 |
| 与 Dify 共用 | 将 Docker 容器部署在 Dify 同一台 ECS 上 | ¥0（复用） |
| 本地 Windows | 开发测试用，无需额外费用 | ¥0 |

#### ECS 申请步骤

1. [ECS 控制台](https://ecs.console.aliyun.com/) → 创建实例
2. 计费方式选「按量付费」，地域与 OSS 同地域
3. 镜像选 Ubuntu 20.04 或 CentOS 7.9
4. 规格选 2 vCPU / 4 GiB（Chromium 运行时需要足够内存）
5. 安全组开放 **8080** 端口（服务端口）
6. 创建后 SSH 登录，安装 Docker

---

### 4. 钉钉机器人 Webhook（可选）

**用途**：将生成的图表 URL 自动推送到钉钉群。

| 申请项 | 说明 |
|--------|------|
| **产品** | 钉钉自定义机器人 |
| **安全设置** | 建议开启「加签」或「IP 白名单」 |
| **需要保存** | Webhook URL + 加签密钥 |

#### 申请步骤

1. 钉钉群 → 群设置 → 智能群助手 → 添加机器人
2. 选择「自定义机器人」，填写名称
3. 安全设置勾选「加签」，保存密钥
4. 复制 Webhook URL

---

### 5. 资源清单汇总

| 序号 | 资源 | 用途 | 必需 | 获取方式 |
|:---:|------|------|:---:|----------|
| 1 | OSS Bucket | 存储图表图片 | ✅ | 阿里云控制台创建 |
| 2 | RAM AccessKey | 服务上传到 OSS | ✅ | RAM 控制台创建子账号 |
| 3 | ECS / Docker 主机 | 运行图表服务 | ✅ | 新建或复用 Dify 主机 |
| 4 | 钉钉 Webhook | 自动推送消息 | 可选 | 钉钉群设置 |
| 5 | OSS 自定义域名 + CDN | 加速图片访问 | 可选 | OSS 控制台 + CDN 控制台 |

### 申请后的配置清单

将以下信息填入部署环境变量：

```bash
# 必填 — OSS
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com    # 对应 Bucket 地域
OSS_BUCKET=shopee-monthly-report             # Bucket 名称
OSS_ACCESS_KEY_ID=LTAI5txxxxxxxx             # RAM 子账号 AK
OSS_ACCESS_KEY_SECRET=xxxxxxxxxxxxxxxx       # RAM 子账号 SK

# 可选 — CDN 加速域名
OSS_DOMAIN=cdn.example.com

# 可选 — 钉钉推送
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
DINGTALK_SECRET=SECxxx
```

---

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OSS_ENDPOINT` | OSS endpoint | `oss-cn-hangzhou.aliyuncs.com` |
| `OSS_BUCKET` | OSS bucket 名称 | (空) |
| `OSS_ACCESS_KEY_ID` | AccessKey ID | (空) |
| `OSS_ACCESS_KEY_SECRET` | AccessKey Secret | (空) |
| `OSS_DOMAIN` | CDN/自定义域名 | (空，使用默认 OSS URL) |

### 视觉配置

编辑 `src/config.py` 可自定义颜色、截图参数：

```python
COLORS = {
    "primary": "#17324D",
    "accent": "#DC473E",
    ...
}
SCREENSHOT = {"device_scale_factor": 2.0, "timeout_ms": 30000}
```

---

## 8 个图表

| 编号 | 标题 | 类型 |
|:---:|---|:---:|
| chart_01 | 月度销售额与同比增长趋势 | 柱 + 折线 双Y轴 |
| chart_02 | 订单数与转化率趋势 | 柱 + 折线 双Y轴 |
| chart_03 | 广告投放 GMV 与 ROI 趋势 | 分组柱 + 双折线 双Y轴 |
| chart_04 | 每月新增粉丝数量 | 柱状图 |
| chart_05 | 当月各品类销售占比 | 环形饼图 |
| chart_06 | 全年各品类销售占比 | 环形饼图 |
| chart_07 | 当月各渠道 GMV 占比 | 环形饼图 |
| chart_08 | 全年各渠道 GMV 占比 | 环形饼图 |

### 20 张 KPI 指标卡

- **核心经营**：月销售额 / 同比增长率 / 目标达成率 / 订单总数 / 客单价
- **广告投放**：虾皮广告GMV / 转化率 / ROI / 花费 / 联盟GMV / 转化率 / ROI / 佣金
- **运营效率**：推广费占比 / 订单转化率 / 回购率 / 退货率 / 加购率 / 新增粉丝 / 退货金额

---

## JSON 输入格式

```json
{
  "output": [
    {"values": [["年份","月份","月销售额",...], [2026,"5月",88626,...]]},
    {"values": [...]},
    ...
  ]
}
```

最少需要 3 个 Sheet 有数据（按 `output` 数组索引）：

| 索引 | 内容 | 用途 |
|:---:|------|------|
| 0 | 月度汇总 | 图1/2/3/4 + KPI |
| 2 | 渠道销售 | 图7/8（缺销售额列则从 Sheet 0 fallback） |
| 6 | 类目销售 | 图5/6 |

---

## 模块说明

| 模块 | 职责 |
|------|------|
| `src/service/app.py` | FastAPI 服务、OSS 上传、响应组装 |
| `json_reader.py` | JSON 解析，`values` 二维数组 → `list[dict]` |
| `data_extractor.py` | 提取图表数据、**自动检测最新月份**、渠道 fallback |
| `chart_data_builder.py` | 构建 ECharts option + KPI 卡片格式化 |
| `template_renderer.py` | Jinja2 渲染 HTML |
| `screenshot.py` | Playwright 截图 |
| `main.py` | 主控编排（CLI 模式） |

---

## License

Internal Use Only
