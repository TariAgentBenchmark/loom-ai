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
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# 复制项目文件
COPY pyproject.toml ./
COPY app/ ./app/
COPY env.example ./.env

# 安装Python依赖
RUN uv venv && \
    uv pip install -e .

# 创建必要目录
RUN mkdir -p uploads/originals uploads/results uploads/temp

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
