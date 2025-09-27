from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="Root status message")
async def read_root() -> dict[str, str]:
    """Return a friendly message to confirm the API is running."""
    return {"message": "LoomAI backend is up"}


@router.get("/health", summary="Simple health probe")
async def health_check() -> dict[str, str]:
    """Basic endpoint that can be used for readiness/liveness probes."""
    return {"status": "ok"}
