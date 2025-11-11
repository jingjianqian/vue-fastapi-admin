from __future__ import annotations

from fastapi import APIRouter, Body, Query

from app.schemas.base import Success, Fail, SuccessExtra
from app.schemas.crawler import (
    CreateTaskIn,
    StartStopIn,
    TaskUpdateIn,
    SyncOdsIn,
)
from app.crawler import CrawlerManager
from app.models.crawler import CrawlerTask
from app.controllers.crawler_sync import sync_ods_to_wechat

router = APIRouter(tags=["爬虫管理"])


@router.post("/task/create", summary="创建爬虫任务")
async def create_task(body: CreateTaskIn):
    try:
        obj = await CrawlerManager.create_task(
            name=body.name,
            source=body.source,
            start_id=body.start_id or 1,
            is_loop=body.is_loop or False,
            max_consecutive_404=body.max_consecutive_404 or 500,
            created_by=None,
        )
        # 额外设置运行参数
        await CrawlerTask.filter(id=obj.id).update(
            concurrency=body.concurrency or 1,
            delay_ms=body.delay_ms or 0,
            max_retries=body.max_retries or 1,
            proxy=body.proxy,
        )
        return Success(data={"id": obj.id})
    except Exception as e:
        return Fail(code=500, msg=str(e))


@router.post("/task/start", summary="启动任务")
async def start_task(body: StartStopIn):
    status = await CrawlerManager.start(body.id)
    if status == "started" or status == "already_running":
        return Success(data={"status": status})
    return Fail(code=404, msg="任务不存在")


@router.post("/task/stop", summary="停止任务")
async def stop_task(body: StartStopIn):
    status = await CrawlerManager.stop(body.id)
    if status in ("stopping", "not_found"):
        return Success(data={"status": status})
    return Fail(code=500, msg="停止失败")


@router.get("/task/status", summary="查看任务状态")
async def task_status(id: int = Query(...)):
    data = await CrawlerManager.status(id)
    if not data:
        return Fail(code=404, msg="任务不存在")
    return Success(data=data)


@router.post("/ods/sync_to_wechat", summary="ODS -> 小程序管理 同步")
async def ods_sync_to_wechat(body: SyncOdsIn):
    try:
        created, updated, skipped = await sync_ods_to_wechat(
            only_new=body.only_new,
            overwrite=body.overwrite,
            include_no_appid=body.include_no_appid,
            limit=body.limit,
        )
        return Success(data={"created": created, "updated": updated, "skipped": skipped})
    except Exception as e:
        return Fail(code=500, msg=str(e))


@router.get("/task/list", summary="任务列表")
async def task_list(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100)):
    total = await CrawlerTask.all().count()
    objs = await CrawlerTask.all().order_by("-id").offset((page - 1) * page_size).limit(page_size)
    data = [await o.to_dict() for o in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post("/task/update", summary="更新任务配置")
async def task_update(body: TaskUpdateIn):
    obj = await CrawlerTask.filter(id=body.id).first()
    if not obj:
        return Fail(code=404, msg="任务不存在")
    # 不允许运行中修改并发等核心参数（简单起见）
    if obj.status == "running":
        return Fail(code=400, msg="任务运行中，暂停后再修改")
    updates = {}
    for f in ["is_loop", "max_consecutive_404", "concurrency", "delay_ms", "max_retries", "proxy"]:
        val = getattr(body, f)
        if val is not None:
            updates[f] = val
    if updates:
        await CrawlerTask.filter(id=obj.id).update(**updates)
    return Success(data={"ok": True})
