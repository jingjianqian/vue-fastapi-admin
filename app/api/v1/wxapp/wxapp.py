from typing import Any, Optional, List

from fastapi import APIRouter, Depends, Query
from tortoise.expressions import Q

from datetime import datetime, timedelta, timezone

from app.schemas.base import Success, Fail
from app.schemas.wxapp import (
    FavoritePin,
    FavoriteToggle,
    MpLogin,
    TrackEvent,
)
from app.core.dependency import DependAuth
from app.models.wechat import WechatApp
from app.models.wxapp_extra import Category, Banner, Favorite, Event

router = APIRouter(tags=["小程序前台接口(wxapp)"])


@router.post("/auth/login", summary="小程序端登录（code2session 桩 + 自动注册葡萄用户）")
async def mp_login(body: MpLogin):
    """
    - 将 code 稳定映射为 openid（桩实现），便于联调
    - 若不存在则创建用户（username/email 由 openid 派生），并自动授予“葡萄用户”角色
    - 返回 JWT，前端以 header: token 传递
    """
    from app.models.admin import User, Role
    from app.utils.password import get_password_hash
    from app.utils.jwt_utils import create_access_token
    from app.schemas.login import JWTPayload
    from app.settings import settings

    # 1) code2session 桩：hash code 为 openid
    import hashlib
    openid = hashlib.sha256(body.code.encode("utf-8")).hexdigest()[:20]

    # 2) 用户查找/创建（用户名长度 <=20，避免违反约束）
    prefix = "wx_"
    username = (prefix + openid)[:20]
    email = f"{openid}@mini.local"
    user = await User.filter(username=username).first()
    if not user:
        user = await User.create(
            username=username,
            email=email,
            password=get_password_hash("123456"),
            is_active=True,
            is_superuser=False,
        )
    # 3) 确保“葡萄用户”角色存在并授予
    role_name = "葡萄用户"
    role = await Role.filter(name=role_name).first()
    if not role:
        role = await Role.create(name=role_name, desc="MiniProgram User")
    await user.roles.add(role)

    # 4) 签发 JWT
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data=JWTPayload(
            user_id=user.id,
            username=user.username,
            is_superuser=user.is_superuser,
            exp=expire,
        )
    )
    user_out = {"id": user.id, "nickname": body.nickname or user.username, "avatar": body.avatarUrl or ""}
    return Success(data={"token": token, "user": user_out})


def _app_to_item(o: WechatApp) -> dict:
    return {
        "id": o.id,
        "appid": o.appid,
        "name": o.name,
        "icon": o.logo_url or "",
        "desc": o.description or "",
        "category_id": o.category_id,
        "is_top": o.is_top,
        "jump_path": o.jump_path,
        "is_favorited": False,
        "is_pinned": False,
    }


@router.get("/home", summary="首页聚合（最小实现，含分类/横幅占位）")
async def home(
    q: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    qexp = Q(is_deleted=False)
    if q:
        qexp &= Q(name__contains=q) | Q(appid__contains=q)
    if category_id:
        qexp &= Q(category_id=category_id)
    
    total = await WechatApp.filter(qexp).count()
    objs: List[WechatApp] = (
        await WechatApp.filter(qexp).offset((page - 1) * page_size).limit(page_size).order_by("id")
    )
    items = [_app_to_item(o) for o in objs]
    
    # 分类与横幅：表未迁移时容错
    try:
        cats = await Category.filter(is_online=True).order_by("sort", "id")
        categories = [{"id": c.id, "name": c.name, "icon_url": c.icon_url} for c in cats]
    except Exception:
        categories = []
    try:
        banners_qs = await Banner.filter(is_online=True).order_by("sort", "id")
        banners = [
            {
                "id": b.id,
                "image_url": b.image_url,
                "app_id": b.app_id,
                "jump_appid": b.jump_appid,
                "jump_path": b.jump_path,
                "sort": b.sort,
            }
            for b in banners_qs
        ]
    except Exception:
        banners = []
    
    # 置顶列表：后台置顶 is_top=True
    try:
        top_objs = await WechatApp.filter(is_deleted=False, is_top=True).order_by("id")
        top = [_app_to_item(o) for o in top_objs]
    except Exception:
        top = []
    
    return Success(
        data={
            "banners": banners,
            "top": top,
            "categories": categories,
            "list": items,
            "total": total,
        }
    )


@router.get("/list", summary="小程序列表（最小实现）")
async def wxapp_list(
    q: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    qexp = Q(is_deleted=False)
    if q:
        qexp &= Q(name__contains=q) | Q(appid__contains=q)
    if category_id:
        qexp &= Q(category_id=category_id)
    
    total = await WechatApp.filter(qexp).count()
    objs: List[WechatApp] = (
        await WechatApp.filter(qexp).offset((page - 1) * page_size).limit(page_size).order_by("id")
    )
    items = [_app_to_item(o) for o in objs]
    return Success(data={"list": items, "total": total, "page": page, "page_size": page_size})


@router.get("/categories", summary="分类列表")
async def categories():
    try:
        cats = await Category.filter(is_online=True).order_by("sort", "id")
        data = [{"id": c.id, "name": c.name, "icon_url": c.icon_url} for c in cats]
        return Success(data=data)
    except Exception:
        # 表未迁移等情况下返回空数组
        return Success(data=[])


@router.get("/favorite/list", summary="我的收藏", dependencies=[DependAuth])
async def favorite_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category_id: Optional[int] = Query(None),
    current_user=DependAuth,
):
    try:
        qexp = Q(user_id=current_user.id)
        favs = await Favorite.filter(qexp).offset((page - 1) * page_size).limit(page_size).order_by("-id")
        app_ids = [f.app_id for f in favs]
        apps = await WechatApp.filter(id__in=app_ids)
        app_map = {a.id: a for a in apps}
        items = []
        for f in favs:
            a = app_map.get(f.app_id)
            if not a:
                continue
            item = _app_to_item(a)
            item["is_favorited"] = True
            item["is_pinned"] = bool(f.is_pinned)
            items.append(item)
        has_more = len(items) == page_size
        return Success(data={"favorites": items, "current_page": page, "has_more": has_more})
    except Exception:
        return Success(data={"favorites": [], "current_page": page, "has_more": False})


@router.post("/favorite/toggle", summary="收藏/取消收藏", dependencies=[DependAuth])
async def favorite_toggle(body: FavoriteToggle, current_user=DependAuth):
    try:
        app = await WechatApp.filter(id=body.app_id, is_deleted=False).first()
        if not app:
            return Fail(code=400, msg="小程序不存在")
        fav = await Favorite.filter(user_id=current_user.id, app_id=body.app_id).first()
        if body.value:
            if not fav:
                await Favorite.create(user_id=current_user.id, app_id=body.app_id, is_pinned=False)
        else:
            if fav:
                await fav.delete()
        return Success(data={"ok": True})
    except Exception as e:
        return Fail(code=500, msg=str(e))


@router.post("/favorite/pin", summary="设为常用/取消常用", dependencies=[DependAuth])
async def favorite_pin(body: FavoritePin, current_user=DependAuth):
    try:
        fav = await Favorite.filter(user_id=current_user.id, app_id=body.app_id).first()
        if not fav and body.value:
            fav = await Favorite.create(user_id=current_user.id, app_id=body.app_id, is_pinned=True)
        elif fav:
            fav.is_pinned = bool(body.value)
            await fav.save()
        return Success(data={"ok": True})
    except Exception as e:
        return Fail(code=500, msg=str(e))


@router.get("/qr", summary="获取二维码URL（最小实现）")
async def get_qr(id: Optional[int] = Query(None), appid: Optional[str] = Query(None)):
    obj: Optional[WechatApp] = None
    if id is not None:
        obj = await WechatApp.filter(id=id).first()
    elif appid:
        obj = await WechatApp.filter(appid=appid).first()
    qr = obj.qrcode_url if obj else ""
    return Success(data={"qr_code_url": qr or ""})


@router.post("/track/event", summary="埋点事件上报")
async def track_event(body: TrackEvent, current_user=DependAuth):
    try:
        await Event.create(user_id=current_user.id, event=body.event, payload=body.payload or {})
        return Success(data={"ok": True})
    except Exception:
        # 表未迁移时容错
        return Success(data={"ok": True})
