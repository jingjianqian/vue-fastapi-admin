import shutil

from aerich import Command
from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from tortoise.expressions import Q

from app.api import api_router
from app.controllers.api import api_controller
from app.controllers.user import UserCreate, user_controller
from app.core.exceptions import (
    DoesNotExist,
    DoesNotExistHandle,
    HTTPException,
    HttpExcHandle,
    IntegrityError,
    IntegrityHandle,
    RequestValidationError,
    RequestValidationHandle,
    ResponseValidationError,
    ResponseValidationHandle,
)
from app.log import logger
from app.models.admin import Api, Menu, Role
from app.schemas.menus import MenuType
from app.settings.config import settings

from .middlewares import BackGroundTaskMiddleware, HttpAuditLogMiddleware


def make_middlewares():
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
            allow_methods=settings.CORS_ALLOW_METHODS,
            allow_headers=settings.CORS_ALLOW_HEADERS,
        ),
        Middleware(BackGroundTaskMiddleware),
        Middleware(
            HttpAuditLogMiddleware,
            methods=["GET", "POST", "PUT", "DELETE"],
            exclude_paths=[
                "/api/v1/base/access_token",
                "/docs",
                "/openapi.json",
            ],
        ),
    ]
    return middleware


def register_exceptions(app: FastAPI):
    app.add_exception_handler(DoesNotExist, DoesNotExistHandle)
    app.add_exception_handler(HTTPException, HttpExcHandle)
    app.add_exception_handler(IntegrityError, IntegrityHandle)
    app.add_exception_handler(RequestValidationError, RequestValidationHandle)
    app.add_exception_handler(ResponseValidationError, ResponseValidationHandle)


def register_routers(app: FastAPI, prefix: str = "/api"):
    app.include_router(api_router, prefix=prefix)


async def init_superuser():
    user = await user_controller.model.exists()
    if not user:
        await user_controller.create_user(
            UserCreate(
                username="admin",
                email="admin@admin.com",
                password="123456",
                is_active=True,
                is_superuser=True,
            )
        )


async def init_menus():
    menus = await Menu.exists()
    if not menus:
        parent_menu = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="系统管理",
            path="/system",
            order=1,
            parent_id=0,
            icon="carbon:gui-management",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/system/user",
        )
        children_menu = [
            Menu(
                menu_type=MenuType.MENU,
                name="用户管理",
                path="user",
                order=1,
                parent_id=parent_menu.id,
                icon="material-symbols:person-outline-rounded",
                is_hidden=False,
                component="/system/user",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="角色管理",
                path="role",
                order=2,
                parent_id=parent_menu.id,
                icon="carbon:user-role",
                is_hidden=False,
                component="/system/role",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="菜单管理",
                path="menu",
                order=3,
                parent_id=parent_menu.id,
                icon="material-symbols:list-alt-outline",
                is_hidden=False,
                component="/system/menu",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="API管理",
                path="api",
                order=4,
                parent_id=parent_menu.id,
                icon="ant-design:api-outlined",
                is_hidden=False,
                component="/system/api",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="部门管理",
                path="dept",
                order=5,
                parent_id=parent_menu.id,
                icon="mingcute:department-line",
                is_hidden=False,
                component="/system/dept",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="审计日志",
                path="auditlog",
                order=6,
                parent_id=parent_menu.id,
                icon="ph:clipboard-text-bold",
                is_hidden=False,
                component="/system/auditlog",
                keepalive=False,
            ),
            # 新增：小程序管理（默认仅在首次初始化时写入）
            Menu(
                menu_type=MenuType.MENU,
                name="小程序管理",
                path="wechat",
                order=7,
                parent_id=parent_menu.id,
                icon="mdi:wechat",
                is_hidden=False,
                component="/system/wechat",
                keepalive=False,
            ),
        ]
        await Menu.bulk_create(children_menu)
        await Menu.create(
            menu_type=MenuType.MENU,
            name="一级菜单",
            path="/top-menu",
            order=2,
            parent_id=0,
            icon="material-symbols:featured-play-list-outline",
            is_hidden=False,
            component="/top-menu",
            keepalive=False,
            redirect="",
        )

async def ensure_wechat_menu():
    # 刷新API，确保 /api/v1/wechat/* 被收集
    try:
        from app.controllers.api import api_controller
        await api_controller.refresh_api()
    except Exception:
        pass

    # 已存在则跳过
    exist = await Menu.filter(component="/system/wechat").exists()
    if exist:
        return
    # 找到系统管理父级
    parent = await Menu.filter(path="/system", parent_id=0).first()
    if not parent:
        parent = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="系统管理",
            path="/system",
            order=1,
            parent_id=0,
            icon="carbon:gui-management",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/system/user",
        )
    menu = await Menu.create(
        menu_type=MenuType.MENU,
        name="小程序管理",
        path="wechat",
        order=7,
        parent_id=parent.id,
        icon="mdi:wechat",
        is_hidden=False,
        component="/system/wechat",
        keepalive=False,
    )
    # 为常见角色附加该菜单（若存在）
    admin = await Role.filter(name="管理员").first()
    if admin:
        await admin.menus.add(menu)
    user = await Role.filter(name="普通用户").first()
    if user:
        await user.menus.add(menu)

    # 追加API权限：将 /api/v1/wechat/* 授权给管理员，普通用户仅读取
    from app.models.admin import Api as ApiModel

    wechat_apis = await ApiModel.filter(path__startswith="/api/v1/wechat").all()
    if admin and wechat_apis:
        await admin.apis.add(*wechat_apis)
    if user and wechat_apis:
        # 普通用户仅赋予 GET 接口权限
        user_readonly_apis = [api for api in wechat_apis if api.method in ("GET",)]
        if user_readonly_apis:
            await user.apis.add(*user_readonly_apis)


async def ensure_crawler_menu():
    # 刷新API，确保 /api/v1/crawler/* 被收集
    try:
        from app.controllers.api import api_controller
        await api_controller.refresh_api()
    except Exception:
        pass

    # 已存在则跳过
    exist = await Menu.filter(component="/system/crawler").exists()
    if exist:
        return
    # 找到系统管理父级
    parent = await Menu.filter(path="/system", parent_id=0).first()
    if not parent:
        parent = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="系统管理",
            path="/system",
            order=1,
            parent_id=0,
            icon="carbon:gui-management",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/system/user",
        )
    menu = await Menu.create(
        menu_type=MenuType.MENU,
        name="爬虫管理",
        path="crawler",
        order=8,
        parent_id=parent.id,
        icon="mdi:spider",
        is_hidden=False,
        component="/system/crawler",
        keepalive=False,
    )
    # 赋权给管理员角色
    admin = await Role.filter(name="管理员").first()
    if admin:
        await admin.menus.add(menu)

    # 追加API权限：将 /api/v1/crawler/* 授权给管理员
    from app.models.admin import Api as ApiModel
    crawler_apis = await ApiModel.filter(path__startswith="/api/v1/crawler").all()
    if admin and crawler_apis:
        await admin.apis.add(*crawler_apis)


async def init_apis():
    apis = await api_controller.model.exists()
    if not apis:
        await api_controller.refresh_api()


async def init_db():
    command = Command(tortoise_config=settings.TORTOISE_ORM)
    try:
        await command.init_db(safe=True)
    except FileExistsError:
        pass

    await command.init()
    try:
        await command.migrate()
    except AttributeError:
        logger.warning("unable to retrieve model history from database, model history will be created from scratch")
        shutil.rmtree("migrations")
        await command.init_db(safe=True)

    await command.upgrade(run_in_transaction=True)


async def init_roles():
    roles = await Role.exists()
    if not roles:
        admin_role = await Role.create(
            name="管理员",
            desc="管理员角色",
        )
        user_role = await Role.create(
            name="普通用户",
            desc="普通用户角色",
        )

        # 分配所有API给管理员角色
        all_apis = await Api.all()
        await admin_role.apis.add(*all_apis)
        # 分配所有菜单给管理员和普通用户
        all_menus = await Menu.all()
        await admin_role.menus.add(*all_menus)
        await user_role.menus.add(*all_menus)

        # 为普通用户分配基本API
        basic_apis = await Api.filter(Q(method__in=["GET"]) | Q(tags="基础模块"))
        await user_role.apis.add(*basic_apis)


async def init_data():
    await init_db()
    await init_superuser()
    await init_menus()
    await ensure_wechat_menu()
    await ensure_crawler_menu()
    await init_apis()
    await init_roles()
