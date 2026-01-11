from fastapi import FastAPI, Request, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, Response
from contextlib import asynccontextmanager
import logging
import os
import time
from datetime import datetime

from app.core.config import settings
from app.core.database import init_db, close_db, check_db_health
from app.core.redis_client import close_redis_client
from app.api.v1 import (
    auth,
    user,
    processing,
    credits,
    payment,
    history,
    admin,
    membership,
    batch_processing,
    agent_portal,
    notification,
)
from app.services.api_limiter import api_limiter


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(user.router, prefix="/user", tags=["用户"])
api_router.include_router(processing.router, prefix="/processing", tags=["图片处理"])
api_router.include_router(
    batch_processing.router, prefix="/processing", tags=["批量处理"]
)
api_router.include_router(credits.router, prefix="/credits", tags=["积分管理"])
api_router.include_router(payment.router, prefix="/payment", tags=["支付"])
api_router.include_router(history.router, prefix="/history", tags=["历史记录"])
api_router.include_router(admin.router, prefix="/admin", tags=["管理员"])
api_router.include_router(membership.router, prefix="/membership", tags=["会员管理"])
api_router.include_router(agent_portal.router, prefix="/agent", tags=["代理商"])
api_router.include_router(notification.router, prefix="", tags=["通知"])


# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level), format=settings.log_format
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("Starting LoomAI Backend...")

    # 初始化数据库
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # 初始化 Redis 限流器
    try:
        await api_limiter.initialize_all()
        logger.info("API limiters initialized")
    except Exception as e:
        logger.error("Failed to initialize API limiters: %s", e)
        raise

    # 确保上传目录存在
    os.makedirs(settings.upload_path, exist_ok=True)
    os.makedirs(f"{settings.upload_path}/originals", exist_ok=True)
    os.makedirs(f"{settings.upload_path}/results", exist_ok=True)

    yield

    # 关闭时执行
    logger.info("Shutting down LoomAI Backend...")
    close_db()
    try:
        await close_redis_client()
    except Exception:
        logger.warning("Closing Redis client failed", exc_info=True)


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="LoomAI - AI图案处理平台后端API",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 自定义静态文件处理器，确保SVG文件的MIME类型正确
class CustomStaticFiles(StaticFiles):
    async def __call__(self, scope, receive, send):
        path = self.get_path(scope)

        # 检查是否是SVG文件
        if path.endswith(".svg"):
            full_path = os.path.join(self.directory, path)
            if os.path.exists(full_path):
                logger.info(f"Serving SVG file: {full_path}")

                # 读取SVG文件内容
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # 创建响应并设置正确的MIME类型
                    response = Response(
                        content=content,
                        media_type="image/svg+xml",
                        headers={
                            "Cache-Control": "public, max-age=3600",
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Methods": "GET",
                            "Access-Control-Allow-Headers": "*",
                        },
                    )

                    await response(scope, receive, send)
                    return
                except Exception as e:
                    logger.error(f"Error serving SVG file {full_path}: {str(e)}")

        # 对于非SVG文件，使用默认处理
        return await super().__call__(scope, receive, send)


# 静态文件服务
app.mount("/files", CustomStaticFiles(directory=settings.upload_path), name="files")

# 包含API路由
app.include_router(api_router, prefix="/v1")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Welcome to LoomAI Backend API",
        "version": settings.app_version,
        "docs": "/docs"
        if settings.debug
        else "Documentation not available in production",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    db_healthy = check_db_health()

    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "version": settings.app_version,
        "timestamp": "2023-12-01T10:00:00Z",
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": f"HTTP{exc.status_code}",
                "message": exc.detail,
                "status_code": exc.status_code,
            },
            "timestamp": "2023-12-01T10:00:00Z",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "E009",
                "message": "服务器内部错误" if not settings.debug else str(exc),
                "details": "请联系技术支持" if not settings.debug else None,
            },
            "timestamp": "2023-12-01T10:00:00Z",
        },
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件"""
    start_time = time.time()
    # 健康检查不写请求日志，避免刷屏
    if request.url.path == "/health":
        return await call_next(request)

    logger.info(f"Request: {request.method} {request.url}")

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.3f}s")

    return response


if __name__ == "__main__":
    import uvicorn
    import time

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
