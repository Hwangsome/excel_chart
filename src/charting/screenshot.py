"""
截图工具层：使用 Playwright 将 HTML 渲染为 PNG。

支持：
  - 全页仪表盘截图（dashboard.png）
  - 单个图表元素截图（chart_01.png ~ chart_08.png）
  - 2x Retina 高清输出
  - 自动重试、超时控制
"""

import asyncio
import os
import sys
from pathlib import Path

from ..config import SCREENSHOT


async def _ensure_browser():
    """确保 Playwright 浏览器已安装，否则给出清晰的安装指引。"""
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            await browser.close()
            return
    except Exception as e:
        error_msg = str(e)
        if "Executable doesn't exist" in error_msg or "not found" in error_msg.lower():
            print("\n" + "=" * 60)
            print("  [WARN] Playwright Chromium browser not installed")
            print("  Please run: playwright install chromium")
            print("=" * 60 + "\n")
            sys.exit(1)
        raise


async def html_to_png(html_content: str, output_path: str,
                      width: int = None, full_page: bool = True,
                      device_scale_factor: float = None,
                      timeout_ms: int = None) -> str:
    """
    将 HTML 字符串渲染为 PNG 图片。

    Args:
        html_content: 完整的 HTML 字符串
        output_path: 输出 PNG 文件路径
        width: 视口宽度，默认使用全局配置
        full_page: 是否截图整个页面（True=长页面全截）
        device_scale_factor: 设备缩放比（2.0=Retina清晰度）
        timeout_ms: 页面加载超时（毫秒）

    Returns:
        输出文件的绝对路径
    """
    if width is None:
        width = SCREENSHOT["dashboard_width"]
    if device_scale_factor is None:
        device_scale_factor = SCREENSHOT["device_scale_factor"]
    if timeout_ms is None:
        timeout_ms = SCREENSHOT["timeout_ms"]

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    max_retries = SCREENSHOT["max_retries"]
    last_error = None

    for attempt in range(max_retries):
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--font-render-hinting=none",
                    ]
                )

                context = await browser.new_context(
                    viewport={"width": width, "height": 800},
                    device_scale_factor=device_scale_factor,
                    locale="zh-CN",
                )
                page = await context.new_page()

                await page.set_content(html_content, wait_until="networkidle",
                                       timeout=timeout_ms)

                # 等待 ECharts 动画完成
                await page.wait_for_timeout(1500)

                # 截图
                await page.screenshot(
                    path=output_path,
                    full_page=full_page,
                    type="png",
                )

                await browser.close()
                return os.path.abspath(output_path)

        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                print(f"  [RETRY] Screenshot attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(2)
            else:
                raise RuntimeError(
                    f"截图失败（已重试 {max_retries} 次）: {last_error}"
                ) from last_error


async def screenshot_dashboard(html_content: str, output_dir: str,
                               month: int = 5, year: int = 2026) -> str:
    """
    截取完整仪表盘全页截图。

    Returns:
        输出文件路径
    """
    filename = f"dashboard_{year}年{month}月.png"
    output_path = os.path.join(output_dir, filename)

    return await html_to_png(
        html_content,
        output_path,
        width=SCREENSHOT["dashboard_width"],
        full_page=True,
    )


async def screenshot_individual_charts(html_content: str,
                                       output_dir: str,
                                       chart_ids: list[str] = None,
                                       width: int = 600) -> list[str]:
    """
    对每个图表单独截图（使用 Playwright element screenshot）。

    Args:
        html_content: 完整 HTML
        output_dir: 输出目录
        chart_ids: 要截图的图表元素 ID 列表
        width: 单个图表截图宽度

    Returns:
        输出文件路径列表
    """
    if chart_ids is None:
        chart_ids = [f"chart_{i:02d}" for i in range(1, 9)]

    os.makedirs(output_dir, exist_ok=True)
    output_paths = []

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("[WARN] Playwright not installed, cannot screenshot individual charts.")
        print("      Run: pip install playwright && playwright install chromium")
        return []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )

        context = await browser.new_context(
            viewport={"width": SCREENSHOT["dashboard_width"], "height": 800},
            device_scale_factor=SCREENSHOT["device_scale_factor"],
            locale="zh-CN",
        )
        page = await context.new_page()

        await page.set_content(html_content, wait_until="networkidle",
                               timeout=SCREENSHOT["timeout_ms"])

        # 等待 ECharts 渲染完成
        await page.wait_for_timeout(1500)

        for chart_id in chart_ids:
            try:
                element = page.locator(f"#{chart_id}")
                if await element.count() > 0:
                    output_path = os.path.join(output_dir, f"{chart_id}.png")
                    await element.screenshot(path=output_path, type="png")
                    output_paths.append(os.path.abspath(output_path))
                    print(f"  [OK] {chart_id}.png")
                else:
                    print(f"  [SKIP] Element #{chart_id} not found")
            except Exception as e:
                print(f"  [FAIL] {chart_id}: {e}")

        await browser.close()

    return output_paths
