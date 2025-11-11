from fastapi import APIRouter, File, Form, Query, Request, UploadFile
from tortoise.expressions import Q

from app.controllers.wechat import wechat_controller
from app.schemas.base import Fail, Success, SuccessExtra
from app.schemas.wechat import *
from app.utils.file import save_upload_file
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["小程序管理"])


@router.get("/list", summary="查看小程序列表")
async def list_wechat(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    name: str | None = Query(None, description="名称(模糊)"),
    appid: str | None = Query(None, description="AppID(模糊)"),
    publish_status: PublishStatus | None = Query(None, description="发布状态"),
    include_deleted: bool = Query(False, description="是否包含已删除记录"),
    only_deleted: bool = Query(False, description="仅显示已删除记录"),
):
    # 构建查询条件
    if only_deleted:
        q = Q(is_deleted=True)
    elif include_deleted:
        q = Q()  # 不过滤 is_deleted
    else:
        q = Q(is_deleted=False)  # 默认只显示未删除
    
    if name:
        q &= Q(name__contains=name)
    if appid:
        q &= Q(appid__contains=appid)
    if publish_status:
        q &= Q(publish_status=publish_status)
    # 默认按 ID 正序排序，满足“按数字大小排序”的需求
    total, objs = await wechat_controller.list(page=page, page_size=page_size, search=q, order=["id"])
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


@router.post("/upload", summary="上传文件")
async def upload_wechat_file(
    file: UploadFile = File(...),
    kind: str | None = Form(None),
):
    """
    上传小程序 Logo 或二维码图片
    
    - **file**: 图片文件（支持 png/jpg/jpeg/webp，最大 5MB）
    - **kind**: 文件类型，可选 logo 或 qrcode，用于分类存储
    
    返回完整的 URL 地址，可直接用于页面展示
    """
    try:
        # 验证 kind 参数
        subdir = kind if kind in {"logo", "qrcode"} else ""
        
        # 保存文件，返回相对路径
        rel_path = await save_upload_file(file, subdir=subdir)
        
        # 构建完整 URL（使用固定的 base URL）
        full_url = f"http://localhost:9999/static/{rel_path}"
        
        return Success(
            data={
                "url": full_url,
                "path": rel_path,
                "filename": file.filename,
                "kind": kind or "image",
            },
            msg="Upload Successfully"
        )
    except Exception as e:
        import traceback
        logger.error(f"Upload error: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"Upload error: {str(e)}")
        print(traceback.format_exc())
        return Fail(code=500, msg=f"上传失败: {str(e)}")


@router.post("/restore", summary="恢复小程序")
async def restore_wechat(body: WechatRestore):
    """
    恢复已删除的小程序记录
    
    将 is_deleted 标记设置为 False，记录重新出现在默认列表中
    """
    obj = await wechat_controller.restore(id=body.id)
    return Success(data=await obj.to_dict(), msg="Restored Successfully")
