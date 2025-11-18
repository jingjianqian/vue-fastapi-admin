from fastapi import APIRouter

from .v1 import v1_router
from .compat import compat_router

api_router = APIRouter()
# v1 routes under /api/v1
api_router.include_router(v1_router, prefix="/v1")
# compatibility routes directly under /api
api_router.include_router(compat_router)


__all__ = ["api_router"]
