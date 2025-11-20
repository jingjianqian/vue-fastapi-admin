import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from tortoise import Tortoise

from app.core.exceptions import SettingNotFound
from app.core.init_app import (
    init_data,
    make_middlewares,
    register_exceptions,
    register_routers,
)

try:
    from app.settings.config import settings
except ImportError:
    raise SettingNotFound("Can not import settings")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_data()
    yield
    await Tortoise.close_connections()


def create_app() -> FastAPI:
    # Create static and upload directories
    os.makedirs(settings.STATIC_DIR, exist_ok=True)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    app = FastAPI(
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.VERSION,
        openapi_url="/openapi.json",
        middleware=make_middlewares(),
        lifespan=lifespan,
    )
    
    # Mount static files（使用配置的前缀，默认 /static）
    static_prefix = getattr(settings, "STATIC_URL_PREFIX", "/static") or "/static"
    if not static_prefix.startswith("/"):
        static_prefix = "/" + static_prefix
    static_prefix = static_prefix.rstrip("/")
    app.mount(static_prefix, StaticFiles(directory=settings.STATIC_DIR), name="static")
    
    register_exceptions(app)
    register_routers(app, prefix="/api")
    return app


app = create_app()
