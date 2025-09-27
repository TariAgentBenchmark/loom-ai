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

## Suggested dev workflow

- Keep frontend and backend running in separate terminals during development.
- Use `frontend/.gitignore` and `backend/.gitignore` to keep environment-specific files isolated.
- Add new shared assets or infrastructure scripts at the repo root and document expectations here.
