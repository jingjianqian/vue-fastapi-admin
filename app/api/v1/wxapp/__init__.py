from fastapi import APIRouter

from .wxapp import router as wxapp_router

__all__ = ["wxapp_router"]
