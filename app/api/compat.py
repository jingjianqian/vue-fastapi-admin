from fastapi import APIRouter, Request

from app.core.dependency import AuthControl
from app.schemas.base import Success, Fail
from app.models.admin import User

compat_router = APIRouter(tags=["兼容接口"])


@compat_router.get("/genPersonalInfo", summary="兼容旧版个人信息接口")
async def gen_personal_info(request: Request):
    try:
        # 支持多种传法：token 头、Authorization: Bearer xxx、query 参数 token
        token = request.headers.get("token") or request.query_params.get("token")
        if not token:
            auth = request.headers.get("authorization") or request.headers.get("Authorization")
            if auth:
                parts = auth.split()
                if len(parts) == 2 and parts[0].lower() == "bearer":
                    token = parts[1]
                else:
                    token = parts[-1]
        if not token:
            return Fail(code=401, msg="缺少token")
        user: User = await AuthControl.is_authed(token)  # 直接调用鉴权方法
        data = {
            "id": user.id,
            "username": user.username,
            "alias": user.alias or user.username,
            "email": user.email,
            "avatar": "https://avatars.githubusercontent.com/u/54677442?v=4",
            "is_superuser": user.is_superuser,
        }
        return Success(data=data)
    except Exception as e:
        return Fail(code=500, msg=str(e))
