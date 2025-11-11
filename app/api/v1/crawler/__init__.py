from fastapi import APIRouter

from .crawler import router as crawler_router

__all__ = ["crawler_router"]