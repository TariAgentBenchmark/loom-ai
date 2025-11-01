from pathlib import Path
from typing import Optional


def build_download_filename(
    original_name: Optional[str],
    fallback_extension: Optional[str] = None,
) -> str:
    """Return the standard download filename with an appropriate extension."""
    candidate = original_name or ""
    suffix = Path(candidate).suffix if candidate else ""

    if not suffix and fallback_extension:
        suffix = (
            fallback_extension
            if fallback_extension.startswith(".")
            else f".{fallback_extension}"
        )

    return f"tuyun{suffix}"

