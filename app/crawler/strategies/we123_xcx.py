import asyncio
import json
import random
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import httpx
from tortoise import connections

from app.log import logger

# 可运行目录
RUNTIME_DIR = Path("app_runtime/we123_xcx").resolve()
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = RUNTIME_DIR / "state.json"
XPATHS_FILE = RUNTIME_DIR / "xpaths.json"

# ODS 表（如与你现网不一致，可在部署前修改为实际表名/列名）
ODS_TABLE = "ods_wechat_mini_program"
ODS_UNIQUE_KEY = "src_id"  # 以来源 id 作为唯一键

DEFAULT_XPATHS = {
    "name": "//h1[contains(@class,'xcx')]/text()",
    "category": "//a[contains(@href,'/xcxcat/')]/text()",
    "tags": "//div[contains(@class,'tags')]//a/text()",
    "desc": "//div[contains(@class,'desc')]/text()",
    "icon_url": "//img[contains(@class,'logo')]/@src",
    "qrcode_url": "//img[contains(@alt,'小程序码')]/@src",
    "screenshot_urls": "//div[contains(@class,'screenshot') or contains(@class,'screenshots')]//img/@src",
    "developer": "//li[contains(.,'开发者')]/span/text()",
    "rating": "//span[contains(@class,'rating')]/text()",
    "hot_value": "//span[contains(@class,'hot')]/text()",
    "comment_count": "//span[contains(@class,'comment')]/text()",
    "version": "//li[contains(.,'版本')]/span/text()",
    "updated_at_src": "//li[contains(.,'更新')]/span/text()",
}


def _load_json_file(p: Path, default: Any) -> Any:
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save_json_file(p: Path, data: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@dataclass
class We123Config:
    start_id: int = 1
    loop: bool = False
    max_404_span: int = 500
    delay_sec: float = 3.0
    ua: Optional[str] = None
    proxy: Optional[str] = None


@dataclass
class We123Status:
    running: bool = False
    last_id: int = 0
    last_ok_id: int = 0
    consecutive_404: int = 0
    ok_count: int = 0
    not_found_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    started_at_ms: Optional[int] = None
    updated_at_ms: Optional[int] = None


class _We123Task:
    """we123 爬虫单例任务（顺序递增、断点续爬、写入 ODS）"""

    def __init__(self) -> None:
        self._task: Optional[asyncio.Task] = None
        self._cancel = asyncio.Event()
        self.cfg = We123Config()
        self.xpaths: Dict[str, str] = {}
        self.st = We123Status()
        # 断点状态文件
        self.state_file = STATE_FILE
        self.xpaths_file = XPATHS_FILE
        # http 预检（拿状态码，404 直接跳过）
        self._client: Optional[httpx.AsyncClient] = None

    async def _ensure_client(self):
        if self._client is None:
            headers = {"User-Agent": self.cfg.ua or self._default_ua()}
            self._client = httpx.AsyncClient(headers=headers, timeout=15)

    async def start(self, cfg: We123Config):
        if self._task and not self._task.done():
            raise RuntimeError("task already running")
        self.cfg = cfg
        self.xpaths = await self.get_xpaths()
        self._load_state()
        self._cancel = asyncio.Event()
        await self._ensure_client()
        self.st.running = True
        self.st.started_at_ms = int(time.time() * 1000)
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self):
        if self._task and not self._task.done():
            self._cancel.set()
            try:
                await asyncio.wait_for(self._task, timeout=10)
            except Exception:
                pass
        self.st.running = False
        await self._close_client()

    async def status(self) -> Dict[str, Any]:
        return asdict(self.st)

    async def get_xpaths(self) -> Dict[str, str]:
        x = _load_json_file(self.xpaths_file, DEFAULT_XPATHS)
        if not isinstance(x, dict):
            x = DEFAULT_XPATHS
        return x

    async def update_xpaths(self, x: Dict[str, str]):
        # 仅覆盖已有键，避免误删
        cur = await self.get_xpaths()
        cur.update({k: v for k, v in x.items() if isinstance(v, str) and v})
        _save_json_file(self.xpaths_file, cur)
        self.xpaths = cur

    async def _run_loop(self):
        from DrissionPage import ChromiumOptions, ChromiumPage  # 延迟导入，避免环境未装时报错

        co = ChromiumOptions().headless(True)
        if self.cfg.ua:
            co.set_user_agent(self.cfg.ua)
        if self.cfg.proxy:
            # 代理格式示例：http://user:pass@host:port 或 http://host:port
            co.set_proxy(self.cfg.proxy)
        page = ChromiumPage(co)
        try:
            cur_id = max(self.st.last_id or 0, self.cfg.start_id or 1)
            consecutive_404 = self.st.consecutive_404 or 0
            while not self._cancel.is_set():
                base_url = f"https://www.we123.com/xcx/{cur_id}/"
                # 先用 httpx 预检状态码（404 则不进浏览器）
                s = await self._head_status(base_url)
                if s == 404:
                    consecutive_404 += 1
                    self._on_not_found(cur_id, consecutive_404)
                    if consecutive_404 >= self.cfg.max_404_span:
                        if self.cfg.loop:
                            cur_id = 1
                            consecutive_404 = 0
                        else:
                            break
                        # 进入下一轮
                        await self._delay()
                        continue
                    cur_id += 1
                    await self._delay()
                    continue

                try:
                    page.get(base_url)
                    data = self._extract_with_xpaths(page, cur_id, base_url)
                    ok = await self._upsert_ods(data)
                    self._on_success(cur_id)
                except Exception as e:
                    logger.exception(f"[we123] parse or upsert error id={cur_id} err={e}")
                    self._on_error(str(e))
                finally:
                    cur_id += 1
                    await self._delay()
        finally:
            try:
                page.close()
            except Exception:
                pass
            self._persist_state()
            self.st.running = False

    async def _head_status(self, url: str) -> int:
        try:
            await self._ensure_client()
            assert self._client is not None
            resp = await self._client.get(url, follow_redirects=True)
            return resp.status_code
        except Exception:
            return 0

    async def _close_client(self):
        if self._client:
            try:
                await self._client.aclose()
            except Exception:
                pass
            self._client = None

    def _extract_with_xpaths(self, page, src_id: int, url: str) -> Dict[str, Any]:
        # 简易 xpath 提取工具，DrissionPage: page.eles(x, xpath=...) 或 page.eles(xp=...)
        def _text_list(xp: str) -> list[str]:
            try:
                eles = page.eles(xp=xp)
                vals = [e.text for e in eles if getattr(e, "text", None)]
                return [v.strip() for v in vals if v and v.strip()]
            except Exception:
                return []

        def _text_one(xp: str) -> Optional[str]:
            arr = _text_list(xp)
            return arr[0] if arr else None

        def _attr_list(xp: str) -> list[str]:
            try:
                eles = page.eles(xp=xp)
                out = []
                for e in eles:
                    # DrissionPage element 属性获取：e.attr("src")，用 eles(xp) 时需要注意接口
                    try:
                        v = e.attr("src") if "@src" in xp else e.attr("href")
                    except Exception:
                        v = None
                    if v and isinstance(v, str):
                        out.append(v)
                return out
            except Exception:
                return []

        x = self.xpaths
        name = _text_one(x.get("name", DEFAULT_XPATHS["name"]))
        category = _text_one(x.get("category", DEFAULT_XPATHS["category"]))
        tags = _text_list(x.get("tags", DEFAULT_XPATHS["tags"]))
        desc = _text_one(x.get("desc", DEFAULT_XPATHS["desc"]))
        icon_url = _text_one(x.get("icon_url", DEFAULT_XPATHS["icon_url"])) or None
        qrcode_url = _text_one(x.get("qrcode_url", DEFAULT_XPATHS["qrcode_url"])) or None
        screenshot_urls = _attr_list(x.get("screenshot_urls", DEFAULT_XPATHS["screenshot_urls"]))
        developer = _text_one(x.get("developer", DEFAULT_XPATHS["developer"]))
        rating = _text_one(x.get("rating", DEFAULT_XPATHS["rating"]))
        hot_value = _text_one(x.get("hot_value", DEFAULT_XPATHS["hot_value"]))
        comment_count = _text_one(x.get("comment_count", DEFAULT_XPATHS["comment_count"]))
        version = _text_one(x.get("version", DEFAULT_XPATHS["version"]))
        updated_at_src = _text_one(x.get("updated_at_src", DEFAULT_XPATHS["updated_at_src"]))

        def _to_int(s: Optional[str]) -> Optional[int]:
            if not s:
                return None
            try:
                return int("".join([ch for ch in s if ch.isdigit()]))
            except Exception:
                return None

        rec: Dict[str, Any] = {
            "src_id": src_id,
            "name": name,
            "category": category,
            "tags_json": json.dumps(tags, ensure_ascii=False) if tags else None,
            "desc": desc,
            "icon_url": icon_url,
            "qrcode_url": qrcode_url,
            "screenshot_urls_json": json.dumps(screenshot_urls, ensure_ascii=False) if screenshot_urls else None,
            "developer": developer,
            "rating": _to_int(rating),
            "hot_value": _to_int(hot_value),
            "comment_count": _to_int(comment_count),
            "version": version,
            "updated_at_src": updated_at_src,
            "detail_url": url,
            "ext_json": None,  # 可扩展保留原始块
        }
        return rec

    async def _upsert_ods(self, rec: Dict[str, Any]) -> bool:
        # 通过原生 SQL upsert；为避免与关键字冲突，对表名与列名加反引号
        cols = [
            "src_id",
            "name",
            "category",
            "tags_json",
            "desc",
            "icon_url",
            "qrcode_url",
            "screenshot_urls_json",
            "developer",
            "rating",
            "hot_value",
            "comment_count",
            "version",
            "updated_at_src",
            "detail_url",
            "ext_json",
        ]
        qcols = [f"`{c}`" for c in cols]
        placeholders = ",".join(["%s"] * len(cols))
        # MySQL 兼容写法，仍使用 VALUES(col)；如目标 MySQL >=8.0.20 不支持，可改为 INSERT ... AS new ... UPDATE col=new.col
        updates = ",".join([f"{qc}=VALUES({qc})" for qc, c in zip(qcols, cols) if c != ODS_UNIQUE_KEY])
        table = f"`{ODS_TABLE}`"
        sql = f"""
        INSERT INTO {table} ({','.join(qcols)})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {updates}
        """
        params = [rec.get(c) for c in cols]
        conn = connections.get("mysql")
        await conn.execute_query(sql, params)
        return True

    def _on_success(self, cur_id: int):
        self.st.last_id = cur_id
        self.st.last_ok_id = cur_id
        self.st.consecutive_404 = 0
        self.st.ok_count += 1
        self.st.updated_at_ms = int(time.time() * 1000)
        self._persist_state()

    def _on_not_found(self, cur_id: int, c404: int):
        self.st.last_id = cur_id
        self.st.consecutive_404 = c404
        self.st.not_found_count += 1
        self.st.updated_at_ms = int(time.time() * 1000)
        self._persist_state_lite()

    def _on_error(self, err: str):
        self.st.error_count += 1
        self.st.last_error = err[:400]
        self.st.updated_at_ms = int(time.time() * 1000)
        self._persist_state_lite()

    async def _delay(self):
        # 3s ± 0.5s 抖动
        d = max(0.0, (self.cfg.delay_sec or 3.0) + random.uniform(-0.5, 0.5))
        await asyncio.sleep(d)

    def _load_state(self):
        obj = _load_json_file(self.state_file, {})
        try:
            self.st.last_id = int(obj.get("last_id", 0))
            self.st.last_ok_id = int(obj.get("last_ok_id", 0))
            self.st.consecutive_404 = int(obj.get("consecutive_404", 0))
            self.st.ok_count = int(obj.get("ok_count", 0))
            self.st.not_found_count = int(obj.get("not_found_count", 0))
            self.st.error_count = int(obj.get("error_count", 0))
            self.st.updated_at_ms = int(obj.get("updated_at_ms")) if obj.get("updated_at_ms") else None
        except Exception:
            pass

    def _persist_state(self):
        _save_json_file(self.state_file, asdict(self.st))

    def _persist_state_lite(self):
        _save_json_file(
            self.state_file,
            {
                "last_id": self.st.last_id,
                "last_ok_id": self.st.last_ok_id,
                "consecutive_404": self.st.consecutive_404,
                "ok_count": self.st.ok_count,
                "not_found_count": self.st.not_found_count,
                "error_count": self.st.error_count,
                "updated_at_ms": self.st.updated_at_ms,
            },
        )

    @staticmethod
    def _default_ua() -> str:
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )


we123_task = _We123Task()
