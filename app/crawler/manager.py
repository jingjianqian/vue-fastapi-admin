from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Dict, Optional

from app.log import logger
from app.models.crawler import CrawlerTask, OdsWe123MiniProgram
from .we123_spider import We123MiniProgramSpider


class CrawlerManager:
    """简单的任务管理器（进程内），以 asyncio.create_task 方式运行"""

    _running: Dict[int, asyncio.Task] = {}
    _spiders = {
        "we123_miniprogram": We123MiniProgramSpider(headless=True),
    }

    @classmethod
    async def create_task(
        cls,
        name: str,
        source: str,
        start_id: int = 1,
        is_loop: bool = False,
        max_consecutive_404: int = 500,
        created_by: Optional[int] = None,
    ) -> CrawlerTask:
        obj = await CrawlerTask.create(
            name=name,
            source=source,
            start_id=max(1, start_id),
            next_id=max(1, start_id),
            is_loop=bool(is_loop),
            max_consecutive_404=max(1, max_consecutive_404),
            status="idle",
            created_by=created_by,
        )
        return obj

    @classmethod
    def get_spider(cls, source: str):
        sp = cls._spiders.get(source)
        if not sp:
            raise ValueError(f"未知的 source: {source}")
        return sp

    @classmethod
    async def start(cls, task_id: int) -> str:
        # 防重复启动
        if task_id in cls._running and not cls._running[task_id].done():
            return "already_running"

        task = await CrawlerTask.filter(id=task_id).first()
        if not task:
            return "not_found"
        if task.status == "running":
            return "already_running"

        # 实例化 spider（按需更新代理）
        base_spider = cls.get_spider(task.source)
        if isinstance(base_spider, We123MiniProgramSpider):
            spider = We123MiniProgramSpider(headless=True, proxy=task.proxy)
        else:
            spider = base_spider

        async def runner():
            try:
                await CrawlerTask.filter(id=task_id).update(status="running", last_error=None, last_run_at=datetime.now())
                logger.info(f"[crawler] start task_id={task_id} source={task.source} start_id={task.start_id} conc={task.concurrency} delay_ms={task.delay_ms} retries={task.max_retries} loop={task.is_loop} th404={task.max_consecutive_404} proxy={(task.proxy or '')}")
                consecutive_404 = task.consecutive_404 or 0
                next_id = task.next_id or task.start_id or 1
                while True:
                    # 支持外部停止
                    latest = await CrawlerTask.filter(id=task_id).first()
                    if not latest or latest.status == "stopped":
                        await CrawlerTask.filter(id=task_id).update(status="stopped")
                        break

                    # 读取最新并发/延迟/重试配置
                    concurrency = max(1, latest.concurrency or 1)
                    delay_ms = max(0, latest.delay_ms or 0)
                    max_retries = max(1, latest.max_retries or 1)

                    ids = list(range(next_id, next_id + concurrency))
                    logger.debug(f"[crawler] task={task_id} batch ids={ids} conc={concurrency} delay_ms={delay_ms} retries={max_retries}")

                    async def fetch_with_retry(xid: int):
                        last = ("error", {"error": "unknown"})
                        for _ in range(max_retries):
                            status, result = await spider.fetch_one(xid)
                            last = (status, result)
                            if status != "error":
                                break
                        return last

                    results = await asyncio.gather(*(fetch_with_retry(x) for x in ids))

                    # 按 ID 顺序处理，维持正确的连续 404 统计
                    for xid, (status, result) in zip(ids, results):
                        if status == "ok":
                            logger.debug(f"[crawler] ok id={xid} appid={result.get('appid')} name={result.get('name')}")
                            data = {
                                "we123_id": xid,
                                "name": result.get("name"),
                                "appid": result.get("appid"),
                                "logo_url": result.get("logo_url"),
                                "qrcode_url": result.get("qrcode_url"),
                                "description": result.get("description"),
                                "category": result.get("category"),
                                "developer": result.get("developer"),
                                "raw_html": result.get("raw_html"),
                                "raw_data": {k: v for k, v in result.items() if k not in {"raw_html"}},
                                "fetch_status": "ok",
                                "fetch_error": None,
                            }
                            exist = await OdsWe123MiniProgram.filter(we123_id=xid).first()
                            if exist:
                                for k, v in data.items():
                                    setattr(exist, k, v)
                                await exist.save()
                            else:
                                await OdsWe123MiniProgram.create(**data)
                            consecutive_404 = 0
                        elif status == "404":
                            logger.debug(f"[crawler] 404 id={xid}")
                            consecutive_404 += 1
                        else:
                            logger.debug(f"[crawler] error id={xid} err={result.get('error')}")
                            await OdsWe123MiniProgram.update_or_create(
                                defaults={
                                    "raw_html": result.get("raw_html"),
                                    "raw_data": {k: v for k, v in result.items() if k not in {"raw_html"}},
                                    "fetch_status": "error",
                                    "fetch_error": result.get("error"),
                                },
                                we123_id=xid,
                            )
                        # 更新最新进度（以 xid 为准）
                        await CrawlerTask.filter(id=task_id).update(
                            next_id=xid + 1, consecutive_404=consecutive_404, last_run_at=datetime.now()
                        )

                        # 终止条件：连续 404 达阈值
                        latest = await CrawlerTask.filter(id=task_id).first()
                        if consecutive_404 >= (latest.max_consecutive_404 or 500):
                            if latest.is_loop:
                                logger.info(f"[crawler] loop restart task_id={task_id} after {consecutive_404} consecutive 404, reset to 1")
                                consecutive_404 = 0
                                next_id = 1
                                await CrawlerTask.filter(id=task_id).update(next_id=next_id, consecutive_404=0)
                                break  # 跳出本批次，继续下一轮
                            else:
                                logger.info(f"[crawler] finished task_id={task_id} after {consecutive_404} consecutive 404")
                                await CrawlerTask.filter(id=task_id).update(status="finished")
                                return

                    # 正常推进到下一批次
                    next_id += concurrency
                    if delay_ms > 0:
                        await asyncio.sleep(delay_ms / 1000)
            except Exception as e:
                logger.exception(f"[crawler] task {task_id} failed: {e}")
                await CrawlerTask.filter(id=task_id).update(status="error", last_error=str(e))

        t = asyncio.create_task(runner(), name=f"crawler-{task_id}")
        cls._running[task_id] = t
        return "started"

    @classmethod
    async def stop(cls, task_id: int) -> str:
        # 标记状态，runner 将读取后退出
        updated = await CrawlerTask.filter(id=task_id).update(status="stopped")
        if updated:
            return "stopping"
        return "not_found"

    @classmethod
    async def status(cls, task_id: int) -> Optional[dict]:
        task = await CrawlerTask.filter(id=task_id).first()
        if not task:
            return None
        return {
            "id": task.id,
            "name": task.name,
            "source": task.source,
            "status": task.status,
            "next_id": task.next_id,
            "start_id": task.start_id,
            "consecutive_404": task.consecutive_404,
            "max_consecutive_404": task.max_consecutive_404,
            "is_loop": task.is_loop,
            "last_run_at": task.last_run_at.isoformat() if task.last_run_at else None,
            "last_error": task.last_error,
        }