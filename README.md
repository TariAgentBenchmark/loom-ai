# LoomAI Monorepo

A starter monorepo with a decoupled web frontend and API backend.

- `frontend/` — [Next.js](https://nextjs.org/) 14 + Tailwind CSS UI.
- `backend/` — [FastAPI](https://fastapi.tiangolo.com/) service managed with [uv](https://github.com/astral-sh/uv).

## Prerequisites

- Node.js 18+ (recommended to install via nvm or fnm)
- pnpm, npm, or yarn (choose your package manager)
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) for backend dependency management

## Frontend quickstart

```bash
cd frontend
npm install          # or pnpm install / yarn install
npm run dev          # http://localhost:3000
```

Tailwind CSS is pre-configured. Global styles live in `src/app/globals.css` and the App Router is used by default.

## Backend quickstart

```bash
cd backend
uv venv
source .venv/bin/activate
uv sync                            # install dependencies into the venv
uv run uvicorn app.main:app --reload
```

The service exposes:

- `GET /` — sanity response
- `GET /health` — health probe
- `GET /version` — app metadata

Run tests with `uv run pytest`.

## Docker deployment

### Quick start with Docker Compose

```bash
# 使用远程镜像启动（默认）
docker-compose up -d

# 或者使用本地构建启动
docker-compose --profile local up -d
```

This will start:
- Frontend (Next.js) on port 3000
- Backend (FastAPI) on port 8000
- Redis on port 6379

### Docker Compose Profiles

项目支持多种启动方式：

```bash
# 使用远程镜像（生产环境）
docker-compose --profile production up -d

# 使用本地构建（开发环境）
docker-compose --profile local up -d

# 默认启动（使用远程镜像）
docker-compose up -d
```

### 环境变量配置

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，设置镜像标签和其他配置
# IMAGE_TAG=latest  # 使用最新版本
# IMAGE_TAG=v1.0.0  # 使用特定版本
```

### Individual Docker builds

```bash
# Build frontend
docker build -t loomai:latest ./frontend

# Build backend
docker build -t loomai-backend:latest ./backend
```

## GitHub Actions CI/CD

This project includes automated Docker builds and deployments via GitHub Actions. See [docs/github-actions.md](docs/github-actions.md) for detailed configuration and usage instructions.

### Automatic builds

- **Main branch**: Builds and pushes `:latest` tags
- **Pull requests**: Builds `:dev-{pr_number}` tags (build only, no push)
- **Tags**: Builds and pushes versioned tags (e.g., `:v1.0.0`)
- **Manual trigger**: Custom tag builds

### Required secrets

Configure these in your repository settings:
- `ALIYUN_CR_USERNAME`: 阿里云容器镜像服务用户名
- `ALIYUN_CR_PASSWORD`: 阿里云容器镜像服务密码

## Suggested dev workflow

- Keep frontend and backend running in separate terminals during development.
- Use `frontend/.gitignore` and `backend/.gitignore` to keep environment-specific files isolated.
- Add new shared assets or infrastructure scripts at the repo root and document expectations here.
