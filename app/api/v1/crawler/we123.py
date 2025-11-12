from fastapi import APIRouter, Body, Query
from typing import Optional

from app.schemas.base import Success, Fail
from app.crawler.strategies import we123_task
from app.log import logger

router = APIRouter(tags=["we123-小程序采集"])


@router.post("/start", summary="启动 we123 采集任务")
async def start_task(
    body: dict = Body(..., example={
        "start_id": 1,
        "loop": False,
        "max_404_span": 500,
        "delay_sec": 3,
        "ua": None,
        "proxy": None,
    })
):
    try:
        cfg = we123_task.We123Config if hasattr(we123_task, 'We123Config') else None
    except Exception:
        cfg = None
    # 直接按 dict 构造
    from app.crawler.strategies.we123_xcx import We123Config
    conf = We123Config(
        start_id=int(body.get("start_id", 1) or 1),
        loop=bool(body.get("loop", False)),
        max_404_span=int(body.get("max_404_span", 500) or 500),
        delay_sec=float(body.get("delay_sec", 3) or 3),
        ua=body.get("ua"),
        proxy=body.get("proxy"),
    )
    try:
        await we123_task.start(conf)
        st = await we123_task.status()
        return Success(data={"running": True, "status": st})
    except RuntimeError as e:
        return Success(data={"running": True, "message": str(e)})
    except Exception as e:
        logger.exception("start we123 error")
        return Fail(code=500, msg=str(e))


@router.post("/stop", summary="停止 we123 采集任务")
async def stop_task():
    try:
        await we123_task.stop()
        st = await we123_task.status()
        return Success(data={"running": False, "status": st})
    except Exception as e:
        return Fail(code=500, msg=str(e))


@router.get("/status", summary="we123 采集任务状态")
async def task_status():
    st = await we123_task.status()
    return Success(data=st)


@router.get("/xpaths", summary="获取 we123 字段 XPath 配置")
async def xpaths_get():
    x = await we123_task.get_xpaths()
    return Success(data=x)


@router.post("/xpaths", summary="更新 we123 字段 XPath 配置")
async def xpaths_update(body: dict = Body(...)):
    await we123_task.update_xpaths(body or {})
    return Success(data={"ok": True})
