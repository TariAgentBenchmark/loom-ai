from typing import Optional
from urllib.parse import urlparse, urlunparse

from app.core.config import settings


AI302_DEFAULT_FILE_HOST = "file.302.ai"


def rewrite_ai302_file_url(
    url: Optional[str],
    *,
    file_base_url: Optional[str] = None,
) -> Optional[str]:
    """Rewrite 302.AI file URLs to the configured domestic-accessible file host."""
    if not url or not isinstance(url, str):
        return url

    parsed = urlparse(url)
    if (parsed.hostname or "").lower() != AI302_DEFAULT_FILE_HOST:
        return url

    target_base = (
        file_base_url
        if file_base_url is not None
        else settings.ai302_file_base_url
    )
    target_base = (target_base or "").strip().rstrip("/")
    if not target_base:
        return url
    if "://" not in target_base:
        target_base = f"https://{target_base}"

    target = urlparse(target_base)
    if not target.scheme or not target.netloc:
        return url

    return urlunparse(
        (
            target.scheme,
            target.netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )
