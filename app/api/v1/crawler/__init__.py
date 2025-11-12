from fastapi import APIRouter

from .scripts import router as scripts_router
from .we123 import router as we123_router

crawler_router = APIRouter()
# 现有脚本平台接口（无前缀，继承上层 /crawler）
crawler_router.include_router(scripts_router)
# we123 任务接口：/crawler/task/we123/*
crawler_router.include_router(we123_router, prefix="/task/we123")

__all__ = ["crawler_router"]
