from fastapi import APIRouter, File, Form, Query, Request, UploadFile, Header, HTTPException
from fastapi.responses import RedirectResponse
from tortoise.expressions import Q

from app.controllers.wechat import wechat_controller
from app.schemas.base import Fail, Success, SuccessExtra
from app.schemas.wechat import *
from app.utils.file import save_upload_file
from app.settings.config import settings
from app.models.miniprogram import Miniprogram, MiniprogramScreenshot
from app.models.wechat import WechatApp
from app.models.wxapp_extra import Event
import logging
import os
import re
import requests
from urllib.parse import urlparse, quote

logger = logging.getLogger(__name__)

router = APIRouter(tags=["小程序管理"])


def _public_base(request: Request) -> str:
    """获取用于拼接静态资源的基准域名/前缀。
    优先使用配置项 STATIC_PUBLIC_BASE_URL；未配置则使用当前请求域名。
    """
    return (settings.STATIC_PUBLIC_BASE_URL or str(request.base_url).rstrip("/"))


def _normalize_prefix(prefix: str | None) -> str:
    p = prefix or "/static"
    if not p.startswith("/"):
        p = "/" + p
    return p.rstrip("/")


def _to_public_url(path: str | None, request: Request) -> str:
    """将存储的路径转换为可直接在浏览器访问的URL。
    - 已是 http(s) 开头则直接返回
    - 相对路径（uploads/... 或 static/uploads/...）拼接为 {base}{STATIC_URL_PREFIX}/{rel}
    """
    if not path:
        return ""
    p = (path or "").replace("\\", "/").strip()
    if p.startswith("http://") or p.startswith("https://"):
        return p
    if p.startswith("static/"):
        p = p[len("static/"):]
    # 仅允许 uploads/wechat 开头，避免越权访问
    if not (p.startswith("uploads/") or p.startswith("uploads/wechat/")):
        return ""
    base = _public_base(request)
    prefix = _normalize_prefix(settings.STATIC_URL_PREFIX)
    return f"{base}{prefix}/{p.lstrip('/')}"


def _to_tracked_url(path: str | None, request: Request, *, app_id: int | None = None, kind: str = "image") -> str:
    """生成带统计跳转的URL，不改变原有资源路径。"""
    if not path:
        return ""
    base = str(request.base_url).rstrip("/")
    qp = f"path={quote(path)}"
    if app_id is not None:
        qp += f"&app_id={app_id}"
    if kind:
        qp += f"&kind={quote(kind)}"
    return f"{base}/api/v1/wechat/image/preview?{qp}"


@router.get("/image/preview", summary="图片预览跳转（带统计）")
async def image_preview(
    request: Request,
    path: str = Query(..., description="数据库存储的路径，可为相对路径或完整URL"),
    app_id: int | None = Query(None, description="关联小程序ID"),
    kind: str = Query("image", description="图片类型：logo/qrcode/image 等")
):
    """将相对/存储路径转换为静态资源URL并重定向，同时记录一次访问事件。"""
    try:
        public_url = _to_public_url(path, request)
        if not public_url:
            raise HTTPException(status_code=400, detail="非法的图片路径")
        # 记录事件（不阻塞主流程）
        try:
            await Event.create(
                user_id=None,
                event="image_view",
                payload={
                    "module": "wechat",
                    "app_id": app_id,
                    "kind": kind,
                    "path": path,
                    "public": public_url,
                    "ip": request.client.host if request and request.client else None,
                    "ua": request.headers.get("User-Agent"),
                    "referer": request.headers.get("Referer"),
                }
            )
        except Exception:
            pass
        return RedirectResponse(url=public_url, status_code=302)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"image_preview error: {e}")
        raise HTTPException(status_code=500, detail="图片预览失败")


@router.get("/list", summary="查看小程序列表")
async def list_wechat(
    request: Request,
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

    # 为浏览器展示增加可直接访问的URL与统计URL（不改变原有字段）
    for d in data:
        rel_logo = d.get("logo_url")
        rel_qr = d.get("qrcode_url")
        d["logo_url_public"] = _to_public_url(rel_logo, request)
        d["qrcode_url_public"] = _to_public_url(rel_qr, request)
        d["logo_url_tracked"] = _to_tracked_url(rel_logo, request, app_id=d.get("id"), kind="logo")
        d["qrcode_url_tracked"] = _to_tracked_url(rel_qr, request, app_id=d.get("id"), kind="qrcode")

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看小程序")
async def get_wechat(id: int = Query(..., description="主键ID"), request: Request = None):
    obj = await wechat_controller.get(id=id)
    d = await obj.to_dict()
    # 附加可展示URL与统计URL
    d["logo_url_public"] = _to_public_url(d.get("logo_url"), request)
    d["qrcode_url_public"] = _to_public_url(d.get("qrcode_url"), request)
    d["logo_url_tracked"] = _to_tracked_url(d.get("logo_url"), request, app_id=d.get("id"), kind="logo")
    d["qrcode_url_tracked"] = _to_tracked_url(d.get("qrcode_url"), request, app_id=d.get("id"), kind="qrcode")
    return Success(data=d)


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
    request: Request = None,
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
        
        # 构建完整 URL（优先使用配置的公共域名；否则使用当前请求域名）
        base = (settings.STATIC_PUBLIC_BASE_URL or str(request.base_url).rstrip("/"))
        prefix = settings.STATIC_URL_PREFIX or "/static"
        if not prefix.startswith("/"):
            prefix = "/" + prefix
        prefix = prefix.rstrip("/")
        full_url = f"{base}{prefix}/{rel_path}"
        
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


