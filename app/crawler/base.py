from __future__ import annotations

from typing import Any, Dict, Tuple


class CrawlerBase:
    """爬虫基类，定义统一接口"""

    source: str = ""

    async def fetch_one(self, item_id: int) -> Tuple[str, Dict[str, Any]]:
        """抓取单个条目
        返回 (status, data)
        - status: ok | 404 | error
        - data: 提取后的 dict（status=ok 时），或 {"error": str}（status=error 时）
        """
        raise NotImplementedError