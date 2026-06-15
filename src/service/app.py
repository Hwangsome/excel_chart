"""
店铺运营月报图表生成服务 — FastAPI

POST /generate  接收 JSON 数据，生成 8 图表 + KPI 仪表盘，上传到阿里云 OSS，返回 URL

启动:
  uvicorn src.service.app:app --host 0.0.0.0 --port 8080

环境变量 / .env:
  OSS_ENDPOINT            阿里云 OSS endpoint
  OSS_BUCKET              OSS bucket 名称
  OSS_ACCESS_KEY_ID       AccessKey
  OSS_ACCESS_KEY_SECRET   SecretKey
  OSS_DOMAIN              自定义域名（可选）
"""

import asyncio
import logging
import os
import tempfile
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..config import OUTPUT_DIR, OSS_CONFIG
from ..charting.main import MonthlyReportGenerator

# ── 日志 ────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("chart-service")

# ── FastAPI ─────────────────────────────────────────
app = FastAPI(
    title="店铺运营月报图表生成服务",
    description="接收 Shopee 运营 JSON 数据，生成 ECharts 仪表盘截图并上传到阿里云 OSS",
    version="2.0.0",
)

# ── OSS 客户端（懒加载） ─────────────────────────────
_oss_bucket = None


def _get_oss_bucket():
    """获取 OSS Bucket 对象（单例，首次调用时初始化）"""
    global _oss_bucket
    if _oss_bucket is not None:
        return _oss_bucket

    if not OSS_CONFIG["bucket"] or not OSS_CONFIG["access_key_id"]:
        raise HTTPException(
            status_code=500,
            detail="OSS 未配置。请设置环境变量: OSS_BUCKET / OSS_ACCESS_KEY_ID / OSS_ACCESS_KEY_SECRET",
        )

    import oss2
    auth = oss2.Auth(OSS_CONFIG["access_key_id"], OSS_CONFIG["access_key_secret"])
    _oss_bucket = oss2.Bucket(auth, OSS_CONFIG["endpoint"], OSS_CONFIG["bucket"])
    logger.info(f"OSS connected: {OSS_CONFIG['bucket']} @ {OSS_CONFIG['endpoint']}")
    return _oss_bucket


def _oss_url(oss_key: str) -> str:
    """构建 OSS 文件访问 URL"""
    domain = OSS_CONFIG.get("domain")
    if domain:
        return f"https://{domain}/{oss_key}"
    return f"https://{OSS_CONFIG['bucket']}.{OSS_CONFIG['endpoint']}/{oss_key}"


def _upload_pngs(local_dir: str, prefix: str) -> dict[str, str]:
    """将目录下所有 PNG 上传到 OSS，返回 {name: url}"""
    bucket = _get_oss_bucket()
    urls = {}
    for fname in os.listdir(local_dir):
        if fname.endswith(".png"):
            local_path = os.path.join(local_dir, fname)
            oss_key = f"{prefix}/{fname}"
            bucket.put_object_from_file(oss_key, local_path)
            urls[fname.replace(".png", "")] = _oss_url(oss_key)
            logger.info(f"  Uploaded: {oss_key}")
    return urls


# ── 请求/响应模型 ───────────────────────────────────

class GenerateRequest(BaseModel):
    data: dict = Field(..., description="JSON 数据，格式 {\"output\": [...]}")
    month: int | None = Field(None, description="报表月份 1-12，不传则自动检测")
    year: int = Field(2026, description="报表年份")
    upload_to_oss: bool = Field(True, description="是否上传到 OSS（False 则返回本地路径）")


class GenerateResponse(BaseModel):
    success: bool
    month: int
    year: int
    dashboard_url: str = ""
    charts: list[dict] = []
    kpi: dict = {}
    oss_prefix: str = ""
    elapsed_seconds: float = 0


# ── API ─────────────────────────────────────────────

@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/oss/status")
async def oss_status():
    """检查 OSS 配置状态"""
    configured = bool(OSS_CONFIG["bucket"] and OSS_CONFIG["access_key_id"])
    return {
        "configured": configured,
        "bucket": OSS_CONFIG["bucket"] or "(not set)",
        "endpoint": OSS_CONFIG["endpoint"],
        "domain": OSS_CONFIG.get("domain") or "(using default)",
    }


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """
    生成月报图表 → 截图 → 上传 OSS

    接收 Shopee 运营数据 JSON（9 个 Sheet），自动检测最新月份，
    生成 8 张图表 + 1 张完整仪表盘，上传到阿里云 OSS，返回访问 URL。
    """
    t0 = datetime.now()

    # 1. 生成图表
    logger.info(f"Generating report: month={req.month or 'auto'}, year={req.year}")
    gen = MonthlyReportGenerator(
        json_data=req.data,
        month=req.month,
        year=req.year,
    )

    try:
        gen.load_data()
        gen.extract_data()
        gen.build_charts()
        html = gen.render()
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise HTTPException(status_code=400, detail=f"数据处理失败: {e}")

    # 2. 截图到临时目录
    tmpdir = tempfile.mkdtemp(prefix="chart_")
    try:
        await gen.generate_images(html, tmpdir)
    except Exception as e:
        logger.error(f"Screenshot error: {e}")
        raise HTTPException(status_code=500, detail=f"截图失败: {e}")

    # 3. 上传 OSS
    tz = timezone(timedelta(hours=8))  # Asia/Shanghai
    today = datetime.now(tz).strftime("%Y-%m-%d")
    prefix = f"reports/{gen.year}/{gen.month:02d}/{today}/{uuid.uuid4().hex[:8]}"

    if req.upload_to_oss:
        try:
            urls = _upload_pngs(tmpdir, prefix)
        except Exception as e:
            logger.error(f"OSS upload error: {e}")
            raise HTTPException(status_code=500, detail=f"OSS 上传失败: {e}")
    else:
        urls = {
            fname.replace(".png", ""): os.path.join(tmpdir, fname)
            for fname in os.listdir(tmpdir) if fname.endswith(".png")
        }

    # 4. 组装响应
    dashboard_url = ""
    charts = []
    for key, url in sorted(urls.items()):
        if key.startswith("dashboard"):
            dashboard_url = url
        else:
            cid = key[:8]
            charts.append({
                "id": cid,
                "title": _CHART_TITLES.get(cid, cid),
                "url": url,
            })

    elapsed = (datetime.now() - t0).total_seconds()
    logger.info(f"Done: month={gen.month}, charts={len(charts)}, elapsed={elapsed:.1f}s")

    return GenerateResponse(
        success=True,
        month=gen.month,
        year=gen.year,
        dashboard_url=dashboard_url,
        charts=charts,
        kpi=gen.kpi_data,
        oss_prefix=prefix if req.upload_to_oss else "",
        elapsed_seconds=round(elapsed, 1),
    )


# ── 图表标题映射 ────────────────────────────────────
_CHART_TITLES = {
    "chart_01": "月度销售额与同比增长趋势",
    "chart_02": "订单数与转化率趋势",
    "chart_03": "广告投放GMV与ROI趋势",
    "chart_04": "每月新增粉丝数量",
    "chart_05": "当月各品类销售占比",
    "chart_06": "全年各品类销售占比",
    "chart_07": "当月各渠道GMV占比",
    "chart_08": "全年各渠道GMV占比",
    "dashboard": "完整仪表盘",
}


# ── 入口 ────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.service.app:app", host="0.0.0.0", port=8080, reload=True)
