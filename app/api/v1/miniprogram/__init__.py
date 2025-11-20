from fastapi import APIRouter

from .miniprogram import router as miniprogram_router

__all__ = ["miniprogram_router"]
