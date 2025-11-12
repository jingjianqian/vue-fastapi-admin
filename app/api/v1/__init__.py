from fastapi import APIRouter

from app.core.dependency import DependPermission

from .apis import apis_router
from .auditlog import auditlog_router
from .base import base_router
from .depts import depts_router
from .menus import menus_router
from .roles import roles_router
from .users import users_router
from .wechat import wechat_router
from .wxapp import wxapp_router

v1_router = APIRouter()

v1_router.include_router(base_router, prefix="/base")
v1_router.include_router(users_router, prefix="/user", dependencies=[DependPermission])
v1_router.include_router(roles_router, prefix="/role", dependencies=[DependPermission])
v1_router.include_router(menus_router, prefix="/menu", dependencies=[DependPermission])
v1_router.include_router(apis_router, prefix="/api", dependencies=[DependPermission])
v1_router.include_router(depts_router, prefix="/dept", dependencies=[DependPermission])
v1_router.include_router(auditlog_router, prefix="/auditlog", dependencies=[DependPermission])
v1_router.include_router(wechat_router, prefix="/wechat", dependencies=[DependPermission])
# 爬虫脚本平台（脚本编写/运行/依赖管理）
from .crawler import crawler_router
v1_router.include_router(crawler_router, prefix="/crawler", dependencies=[DependPermission])
# wxapp 面向小程序端，GET 匿名可读，写接口内部做鉴权
v1_router.include_router(wxapp_router, prefix="/wxapp")
