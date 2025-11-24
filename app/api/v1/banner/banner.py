from fastapi import APIRouter, File, Form, Query, Request, UploadFile
from tortoise.expressions import Q

from app.schemas.base import Fail, Success, SuccessExtra
from app.models.wxapp_extra import Banner
from app.utils.file import save_upload_file
from app.settings.config import settings
from app.api.v1.wechat.wechat import _to_public_url
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Banner管理"])


@router.get("/list", summary="查看Banner列表")
async def list_banner(
    request: Request,
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    title: str | None = Query(None, description="标题(模糊)"),
):
    q = Q()
    if title:
        q &= Q(title__contains=title)
    
    total = await Banner.filter(q).count()
    offset = (page - 1) * page_size
    objs = await Banner.filter(q).offset(offset).limit(page_size).order_by("sort", "id")
    
    data = []
    for obj in objs:
        d = {
            "id": obj.id,
            "title": obj.title,
            "image_url": obj.image_url,
            "image_url_public": _to_public_url(obj.image_url, request),
            "app_id": obj.app_id,
            "jump_appid": obj.jump_appid,
            "jump_path": obj.jump_path,
            "sort": obj.sort,
            "is_online": obj.is_online,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }
        data.append(d)
    
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看单个Banner")
async def get_banner(id: int = Query(..., description="主键ID"), request: Request = None):
    obj = await Banner.filter(id=id).first()
    if not obj:
        return Fail(code=404, msg="Banner不存在")
    
    d = {
        "id": obj.id,
        "title": obj.title,
        "image_url": obj.image_url,
        "image_url_public": _to_public_url(obj.image_url, request),
        "app_id": obj.app_id,
        "jump_appid": obj.jump_appid,
        "jump_path": obj.jump_path,
        "sort": obj.sort,
        "is_online": obj.is_online,
    }
    return Success(data=d)


@router.post("/create", summary="创建Banner")
async def create_banner(
    title: str = Form(...),
    image_url: str = Form(...),
    app_id: int | None = Form(None),
    jump_appid: str | None = Form(None),
    jump_path: str | None = Form(None),
    sort: int = Form(0),
    is_online: bool = Form(True),
):
    obj = await Banner.create(
        title=title,
        image_url=image_url,
        app_id=app_id,
        jump_appid=jump_appid,
        jump_path=jump_path,
        sort=sort,
        is_online=is_online,
    )
    return Success(data={"id": obj.id}, msg="Created Successfully")


@router.post("/update", summary="更新Banner")
async def update_banner(
    id: int = Form(...),
    title: str = Form(...),
    image_url: str = Form(...),
    app_id: int | None = Form(None),
    jump_appid: str | None = Form(None),
    jump_path: str | None = Form(None),
    sort: int = Form(0),
    is_online: bool = Form(True),
):
    obj = await Banner.filter(id=id).first()
    if not obj:
        return Fail(code=404, msg="Banner不存在")
    
    obj.title = title
    obj.image_url = image_url
    obj.app_id = app_id
    obj.jump_appid = jump_appid
    obj.jump_path = jump_path
    obj.sort = sort
    obj.is_online = is_online
    await obj.save()
    
    return Success(msg="Updated Successfully")


@router.delete("/delete", summary="删除Banner")
async def delete_banner(id: int = Query(..., description="主键ID")):
    obj = await Banner.filter(id=id).first()
    if not obj:
        return Fail(code=404, msg="Banner不存在")
    
    await obj.delete()
    return Success(msg="Deleted Successfully")


@router.post("/upload", summary="上传Banner图片")
async def upload_banner_file(
    file: UploadFile = File(...),
    request: Request = None,
):
    """
    上传 Banner 图片
    
    - **file**: 图片文件（支持 png/jpg/jpeg/webp，最大 5MB）
    
    返回完整的 URL 地址和相对路径
    """
    try:
        # 保存文件到 banners 子目录
        rel_path = await save_upload_file(file, subdir="banners")
        
        # 构建完整 URL
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
            },
            msg="Upload Successfully"
        )
    except Exception as e:
        import traceback
        logger.error(f"Upload error: {str(e)}")
        logger.error(traceback.format_exc())
        return Fail(code=500, msg=f"上传失败: {str(e)}")
