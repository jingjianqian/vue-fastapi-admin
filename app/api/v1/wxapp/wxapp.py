from typing import Any, Optional, List

from fastapi import APIRouter, Depends, Query, Request
from tortoise.expressions import Q

from datetime import datetime, timedelta, timezone

from app.schemas.base import Success, Fail
from app.schemas.wxapp import (
    FavoritePin,
    FavoriteToggle,
    MpLogin,
    TrackEvent,
)
from app.core.dependency import DependAuth, DependAuthOptional
from app.models.wechat import WechatApp
from app.models.wxapp_extra import Category, Banner, Favorite, Event, WxUser
from app.api.v1.wechat.wechat import _to_public_url

# 认证与配置
import jwt
from app.settings import settings
from app.utils.wechat import code2session, validate_appid

# 模型
from app.models.admin import User

# 日志
import logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["小程序前台接口(wxapp)"])


@router.post("/auth/login", summary="小程序端登录（生产版：调用微信code2session + 自动注册葡萄用户）")
async def mp_login(body: MpLogin):
    """
    - 调用微信 code2session 获取 openid/session_key/unionid
    - 若不存在则创建用户（username/email 由 openid 派生，绑定 wx_openid/wx_unionid），并自动授予"葡萄用户"角色
    - 返回 JWT，前端以 header: token 传递
    """
    from app.models.admin import User, Role
    from app.utils.password import get_password_hash
    from app.utils.jwt_utils import create_access_token
    from app.schemas.login import JWTPayload

    # 校验appid（若提供）
    if body.appid and not validate_appid(body.appid):
        return Fail(code=400, msg="非法的appid")

    # 调用微信code2session（未配置appid/secret时内部自动走桩实现）
    try:
        wxres = await code2session(code=body.code, appid=body.appid)
    except Exception as e:
        logger.error(f"wxapp.auth.login code2session failed: {e}")
        return Fail(code=500, msg=f"微信登录失败: {e}")

    openid = wxres.get("openid") or ""
    unionid = wxres.get("unionid")
    if not openid:
        return Fail(code=500, msg="未获取到openid")

    # 用户查找/创建（优先通过 wx_openid 绑定）
    user = await User.filter(wx_openid=openid).first()
    if not user:
        # 兼容旧数据：尝试以 username 匹配历史规则
        user = await User.filter(username=("wx_" + openid)[:20]).first()
    if not user:
        username = ("wx_" + openid)[:20]
        email = f"{openid}@mini.local"
        user = await User.create(
            username=username,
            email=email,
            password=get_password_hash("123456"),
            is_active=True,
            is_superuser=False,
            wx_openid=openid,
            wx_unionid=unionid,
        )
    else:
        # 补全绑定信息
        updated = False
        if not getattr(user, "wx_openid", None):
            user.wx_openid = openid
            updated = True
        if unionid and not getattr(user, "wx_unionid", None):
            user.wx_unionid = unionid
            updated = True
        if updated:
            await user.save()

    # 确保"葡萄用户"角色存在并授予
    role_name = "葡萄用户"
    role = await Role.filter(name=role_name).first()
    if not role:
        role = await Role.create(name=role_name, desc="MiniProgram User")
    await user.roles.add(role)

    # 更新用户昵称/头像（如果提供）
    updated_profile = False
    if body.nickname and body.nickname != user.username:
        user.alias = body.nickname
        updated_profile = True
    if body.avatarUrl:
        user.avatar = body.avatarUrl
        updated_profile = True
    if updated_profile:
        await user.save()

    # 记录/更新 WxUser 档案
    try:
        wx_user = await WxUser.filter(wx_openid=openid).first()
        now = datetime.now(timezone.utc)
        if not wx_user:
            await WxUser.create(
                wx_openid=openid,
                wx_unionid=unionid,
                nickname=body.nickname,
                avatar_url=body.avatarUrl,
                last_login_at=now,
            )
        else:
            changed = False
            if body.nickname and body.nickname != wx_user.nickname:
                wx_user.nickname = body.nickname
                changed = True
            if body.avatarUrl and body.avatarUrl != wx_user.avatar_url:
                wx_user.avatar_url = body.avatarUrl
                changed = True
            wx_user.last_login_at = now
            if changed:
                await wx_user.save()
            else:
                # 即使未改动头像/昵称，也要刷新最后登录时间
                await wx_user.save()
    except Exception:
        pass

    # 签发 JWT（与 PC 端保持一致的格式）
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=JWTPayload(
            user_id=user.id,
            username=user.username,
            is_superuser=user.is_superuser,
            exp=expire,
        )
    )
    
    # 返回用户信息，包含昵称和头像
    user_info = {
        "id": user.id,
        "username": user.username,
        "nickname": user.alias or user.username,
        "avatar": user.avatar or (body.avatarUrl or ""),
        "is_superuser": user.is_superuser
    }
    
    return Success(data={
        "access_token": access_token, 
        "username": user.username,
        "user": user_info
    })


def _app_to_item(o: WechatApp, request: Request) -> dict:
    """将 WechatApp 模型转换为小程序使用的字典结构。

    为兼容数据库中存储相对路径的情况，这里会将 logo_url 转换为可直接访问的完整 URL。
    """
    return {
        "id": o.id,
        "appid": o.appid,
        "name": o.name,
        # 小程序端直接展示图标，需要完整可访问的 URL
        "icon": _to_public_url(o.logo_url, request),
        "desc": o.description or "",
        "category_id": o.category_id,
        "is_top": o.is_top,
        "jump_path": o.jump_path,
        "is_favorited": False,
        "is_pinned": False,
    }


@router.get("/home", summary="首页聚合（含分类/横幅/置顶；登录用户带收藏状态）")
async def home(
    request: Request,
    q: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: Optional[User] = DependAuthOptional,
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
    # 转换为前端使用的数据结构，并将图标路径转换为完整 URL
    items = [_app_to_item(o, request) for o in objs]

    # 若用户已登录，批量查询收藏状态
    if current_user:
        try:
            app_ids = [item["id"] for item in items]
            favs = await Favorite.filter(user_id=current_user.id, app_id__in=app_ids)
            fav_map = {f.app_id: f for f in favs}
            for item in items:
                fav = fav_map.get(item["id"])
                if fav:
                    item["is_favorited"] = True
                    item["is_pinned"] = bool(fav.is_pinned)
        except Exception:
            pass
    
    # 分类与横幅：表未迁移时容错
    try:
        cats = await Category.filter(is_online=True).order_by("sort", "id")
        # 分类图标也可能是相对路径，这里统一转换为完整 URL
        categories = [
            {
                "id": c.id,
                "name": c.name,
                "icon_url": _to_public_url(c.icon_url, request),
            }
            for c in cats
        ]
    except Exception:
        categories = []
    try:
        banners_qs = await Banner.filter(is_online=True).order_by("sort", "id")
        # Banner 图片同样转换为完整 URL
        banners = [
            {
                "id": b.id,
                "image_url": _to_public_url(b.image_url, request),
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
        top = [_app_to_item(o, request) for o in top_objs]
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
    request: Request,
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
    items = [_app_to_item(o, request) for o in objs]
    return Success(data={"list": items, "total": total, "page": page, "page_size": page_size})


@router.get("/auth/profile", summary="获取当前登录用户信息", dependencies=[DependAuth])
async def auth_profile(current_user=DependAuth):
    try:
        user: User = current_user
        profile = {
            "id": user.id,
            "username": user.username,
            "nickname": getattr(user, "alias", None) or user.username,
            "avatar": getattr(user, "avatar", "") or "",
            "is_superuser": user.is_superuser,
        }
        return Success(data=profile)
    except Exception as e:
        logger.error(f"wxapp.auth.profile error: {e}")
        return Fail(code=500, msg=str(e))


@router.get("/detail/{id}", summary="小程序详情")
async def wxapp_detail(id: int, request: Request, current_user: Optional[User] = DependAuthOptional):
    obj: Optional[WechatApp] = await WechatApp.filter(id=id, is_deleted=False).first()
    if not obj:
        return Fail(code=404, msg="小程序不存在")
    # 详情页同样使用完整 URL 图标
    item = _app_to_item(obj, request)
    # 追加扩展字段
    item.update({
        "desc": obj.description or "",
        # 小程序端展示二维码需要完整 URL
        "qrcode_url": _to_public_url(obj.qrcode_url, request),
        "version": obj.version or "",
        "publish_status": obj.publish_status.name if getattr(obj, "publish_status", None) else "",
    })

    # 登录态下追加收藏状态
    if current_user:
        try:
            fav = await Favorite.filter(user_id=current_user.id, app_id=obj.id).first()
            if fav:
                item["is_favorited"] = True
                item["is_pinned"] = bool(fav.is_pinned)
        except Exception:
            pass

    return Success(data=item)


@router.get("/categories", summary="分类列表")
async def categories(request: Request):
    try:
        cats = await Category.filter(is_online=True).order_by("sort", "id")
        # 分类图标也转换为完整 URL
        data = [
            {
                "id": c.id,
                "name": c.name,
                "icon_url": _to_public_url(c.icon_url, request),
            }
            for c in cats
        ]
        return Success(data=data)
    except Exception:
        # 表未迁移等情况下返回空数组
        return Success(data=[])


@router.get("/favorite/list", summary="我的收藏", dependencies=[DependAuth])
async def favorite_list(
    request: Request,
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
            item = _app_to_item(a, request)
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
async def get_qr(
    request: Request,
    id: Optional[int] = Query(None),
    appid: Optional[str] = Query(None),
):
    obj: Optional[WechatApp] = None
    if id is not None:
        obj = await WechatApp.filter(id=id).first()
    elif appid:
        obj = await WechatApp.filter(appid=appid).first()
    # 将数据库中的相对路径转换为完整可访问的 URL，供小程序直接展示/下载
    qr_raw = obj.qrcode_url if obj else ""
    qr_public = _to_public_url(qr_raw, request) if qr_raw else ""
    return Success(data={"qr_code_url": qr_public or ""})


@router.post("/track/event", summary="埋点事件上报")
async def track_event(body: TrackEvent, current_user=DependAuthOptional):
    try:
        # 如果用户已登录则记录user_id，否则为None
        user_id = current_user.id if current_user else None
        await Event.create(user_id=user_id, event=body.event, payload=body.payload or {})
        return Success(data={"ok": True})
    except Exception as e:
        # 表未迁移时容错
        logger.warning(f"wxapp.track.event write failed: {e}")
        return Success(data={"ok": True})
