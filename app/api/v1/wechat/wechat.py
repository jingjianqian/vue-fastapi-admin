from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.controllers.wechat import wechat_controller
from app.schemas.base import Fail, Success, SuccessExtra
from app.schemas.wechat import *

router = APIRouter()


@router.get("/list", summary="查看小程序列表")
async def list_wechat(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    name: str | None = Query(None, description="名称(模糊)"),
    appid: str | None = Query(None, description="AppID(模糊)"),
    publish_status: PublishStatus | None = Query(None, description="发布状态"),
):
    q = Q(is_deleted=False)
    if name:
        q &= Q(name__contains=name)
    if appid:
        q &= Q(appid__contains=appid)
    if publish_status:
        q &= Q(publish_status=publish_status)
    total, objs = await wechat_controller.list(page=page, page_size=page_size, search=q, order=["-updated_at", "id"])
    data = [await o.to_dict() for o in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看小程序")
async def get_wechat(id: int = Query(..., description="主键ID")):
    obj = await wechat_controller.get(id=id)
    return Success(data=await obj.to_dict())


@router.post("/create", summary="创建小程序")
async def create_wechat(body: WechatCreate):
    if await wechat_controller.get_by_appid(body.appid):
        return Fail(code=400, msg="该 AppID 已存在")
    await wechat_controller.create(body)
    return Success(msg="Created Successfully")


@router.post("/update", summary="更新小程序")
async def update_wechat(body: WechatUpdate):
    if body.appid is not None:
        exists = await wechat_controller.model.filter(appid=body.appid).exclude(id=body.id).exists()
        if exists:
            return Fail(code=400, msg="该 AppID 已存在")
    await wechat_controller.update(id=body.id, obj_in=body)
    return Success(msg="Updated Successfully")


@router.delete("/delete", summary="删除小程序")
async def delete_wechat(id: int = Query(..., description="主键ID")):
    # 逻辑删除以避免误删
    obj = await wechat_controller.get(id=id)
    obj.is_deleted = True
    await obj.save()
    return Success(msg="Deleted Successfully")


@router.post("/update_logo", summary="更新小程序Logo")
async def update_logo(body: WechatUpdateLogo):
    await wechat_controller.set_logo(body.id, body.logo_url)
    return Success(msg="Updated Successfully")


@router.post("/update_qrcode", summary="更新小程序二维码")
async def update_qrcode(body: WechatUpdateQrcode):
    await wechat_controller.set_qrcode(body.id, body.qrcode_url)
    return Success(msg="Updated Successfully")


@router.post("/update_status", summary="更新发布状态")
async def update_status(body: WechatUpdateStatus):
    await wechat_controller.set_status(body.id, body.publish_status)
    return Success(msg="Updated Successfully")