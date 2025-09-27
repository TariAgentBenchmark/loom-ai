from fastapi import FastAPI

from .api import api_router
from .core.config import settings

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.include_router(api_router)


@app.get("/version", summary="Return application metadata")
async def get_version() -> dict[str, str]:
    """Expose the running version and environment for quick inspection."""
    return {
        "name": settings.app_name,
        "environment": settings.environment,
        "version": settings.app_version,
    }


def run() -> None:
    """Run the FastAPI application using uvicorn."""
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":  # pragma: no cover - convenience entrypoint
    run()
