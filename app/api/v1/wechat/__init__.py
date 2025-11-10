from fastapi import APIRouter

from .wechat import router as wechat_router

__all__ = ["wechat_router"]