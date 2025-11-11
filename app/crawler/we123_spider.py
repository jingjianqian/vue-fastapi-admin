from __future__ import annotations

import asyncio
from typing import Any, Dict, Tuple

from .base import CrawlerBase
from app.log import logger


class We123MiniProgramSpider(CrawlerBase):
    source = "we123_miniprogram"

    def __init__(self, headless: bool = True, proxy: str | None = None) -> None:
        self._headless = headless
        self._proxy = proxy

    async def fetch_one(self, item_id: int) -> Tuple[str, Dict[str, Any]]:
        """使用 DrissionPage 抓取 we123.com/xcx/<id>/ 页面
        尽量健壮地提取部分字段，解析失败时返回 error；页面不存在返回 404
        """
        url = f"https://www.we123.com/xcx/{item_id}/"
        logger.debug(f"[we123] fetch start id={item_id} url={url} headless={self._headless} proxy={(self._proxy or '')}")

        # DrissionPage 是阻塞 API，这里放在线程池以免阻塞事件循环
        loop = asyncio.get_event_loop()
        try:
            status, result = await loop.run_in_executor(None, self._blocking_fetch, url, item_id)
            return status, result
        except Exception as e:
            return "error", {"error": str(e)}

    # ----- blocking section (runs in threadpool) -----
    def _blocking_fetch(self, url: str, item_id: int) -> Tuple[str, Dict[str, Any]]:
        html: str | None = None
        try:
            try:
                from DrissionPage import ChromiumPage, ChromiumOptions  # type: ignore
            except Exception as e:  # 未安装或环境异常
                raise RuntimeError(
                    "缺少 drissionpage 依赖，请在后端环境安装: pip install drissionpage"
                ) from e

            co = ChromiumOptions().headless(self._headless)
            # 代理设置（尽力而为，不同版本 API 可能不同）
            if self._proxy:
                try:
                    co.set_proxy(self._proxy)  # e.g. http://host:port
                except Exception:
                    pass
            page = ChromiumPage(co)
            try:
                page.get(url)
                title = page.title or ""
                # 简易 404 判定：根据标题或文案
                if any(x in title for x in ["404", "Not Found"]):
                    logger.debug(f"[we123] 404 id={item_id} title='{title}'")
                    return "404", {"error": "not found", "url": url}
                html = page.html
                logger.debug(f"[we123] got html id={item_id} title='{title}' len={len(html or '')}")
            finally:
                # 释放资源
                try:
                    page.close()
                except Exception:
                    pass

            data = self._parse_html(item_id, html or "")
            summary = {k: data.get(k) for k in ("name", "appid", "qrcode_url", "category", "developer")}
            logger.debug(f"[we123] parsed id={item_id} summary={summary}")
            if not data.get("name") and not data.get("appid") and not data.get("qrcode_url"):
                # 视为解析失败，但保留 raw_html 供排查
                logger.debug(f"[we123] parse failed id={item_id}")
                return "error", {"error": "parse failed", "raw_html": html or "", "url": url}
            return "ok", {**data, "raw_html": html or "", "url": url}
        except RuntimeError as e:
            # 透传可预期错误
            raise e
        except Exception as e:
            return "error", {"error": f"{type(e).__name__}: {e}", "raw_html": html or "", "url": url}

    def _parse_html(self, item_id: int, html: str) -> Dict[str, Any]:
        # 为避免额外依赖，仅用简单字符串与非常宽松的提取。若有 bs4 可进一步增强
        data: Dict[str, Any] = {"we123_id": item_id}
        try:
            from bs4 import BeautifulSoup  # type: ignore

            soup = BeautifulSoup(html, "html.parser")
            # 名称：优先 h1，其次 .title
            name = None
            h1 = soup.select_one("h1")
            if h1 and h1.get_text(strip=True):
                name = h1.get_text(strip=True)
            if not name:
                t = soup.select_one(".title, .xcx-title, .app-title")
                if t:
                    name = t.get_text(strip=True)
            data["name"] = name

            # 图标：常见类名
            icon_url = None
            icon = soup.select_one("img.logo, img.app-logo, .logo img, .app-logo img")
            if icon and icon.get("src"):
                icon_url = icon.get("src")
            if not icon_url:
                # 兜底：取第一张较小图片
                img = soup.select_one("img")
                if img and img.get("src"):
                    icon_url = img.get("src")
            data["logo_url"] = icon_url

            # 二维码：尝试匹配含 qr / qrcode 的图片
            qr_url = None
            for img in soup.find_all("img"):
                src = (img.get("src") or "") + (img.get("data-src") or "")
                if any(k in src.lower() for k in ["qr", "qrcode", "ewm", "erweima"]):
                    qr_url = img.get("src") or img.get("data-src")
                    break
            data["qrcode_url"] = qr_url

            # AppID：页面可能包含 “AppID” 文案
            appid = None
            for tag in soup.find_all(["div", "span", "li", "p"]):
                txt = tag.get_text(" ", strip=True)
                if "AppID" in txt or "appid" in txt.lower():
                    # 简单抽取冒号后的内容
                    parts = txt.replace("：", ":").split(":")
                    if len(parts) >= 2:
                        cand = parts[-1].strip()
                        if len(cand) >= 8:  # 粗略校验
                            appid = cand
                            break
            data["appid"] = appid

            # 描述：抓取 meta[name=description] 或首段落
            desc = None
            meta = soup.select_one('meta[name="description"]')
            if meta and meta.get("content"):
                desc = meta.get("content")
            if not desc:
                p = soup.select_one("p, .desc, .app-desc")
                if p:
                    desc = p.get_text(" ", strip=True)[:500]
            data["description"] = desc

            # 分类/开发者：弱匹配
            category = None
            developer = None
            for tag in soup.find_all(["li", "div", "span"]):
                txt = tag.get_text(" ", strip=True)
                if ("分类" in txt or "类别" in txt) and not category:
                    parts = txt.replace("：", ":").split(":")
                    if len(parts) >= 2:
                        category = parts[-1].strip()
                if any(k in txt for k in ["开发者", "主体", "公司", "运营者"]) and not developer:
                    parts = txt.replace("：", ":").split(":")
                    if len(parts) >= 2:
                        developer = parts[-1].strip()
            data["category"] = category
            data["developer"] = developer

        except Exception:
            # 解析失败不抛出，交由上层处理
            pass

        return data