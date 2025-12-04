# LoomAI Backend Dockerfile
FROM python:3.11-slim

LABEL maintainer="LoomAI Team <tech@loom-ai.com>"
LABEL description="LoomAI Backend API Server"

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装uv
RUN pip install --no-cache-dir uv

# 复制依赖文件并安装依赖
COPY pyproject.toml ./
COPY uv.lock ./
COPY README.md ./

# 安装Python依赖
RUN uv sync --frozen

# 复制项目文件
COPY . ./
RUN if [ -f env.example ]; then cp env.example .env; else cp .env.example .env; fi

# 创建必要目录
RUN mkdir -p uploads/originals uploads/results uploads/temp data

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=120s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 初始化数据库并启动服务（使用Gunicorn多进程）
CMD ["sh", "-c", "uv run init_db.py && gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w ${GUNICORN_WORKERS:-4} -b 0.0.0.0:8000 --timeout 120 --graceful-timeout 30 --keep-alive 30"]
