"""API routers for the LoomAI backend."""

from fastapi import APIRouter

from .routes import router as base_router

api_router = APIRouter()
api_router.include_router(base_router, prefix="", tags=["root"])

__all__ = ["api_router"]
