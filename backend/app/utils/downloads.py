from pathlib import Path
from typing import Optional


def detect_extension_from_content(content: bytes) -> Optional[str]:
    """Infer a download extension from common file signatures."""
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if content.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if content.startswith(b"GIF87a") or content.startswith(b"GIF89a"):
        return "gif"
    if content.startswith(b"BM"):
        return "bmp"
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "webp"

    head = content[:512].lstrip().lower()
    if head.startswith(b"<?xml") or head.startswith(b"<svg"):
        return "svg"
    if head.startswith(b"%!ps"):
        return "eps"
    if head.startswith(b"%pdf"):
        return "pdf"

    return None


def normalize_filename_for_content(filename: str, content: bytes) -> str:
    """Return filename with an extension that matches the actual file bytes."""
    detected_ext = detect_extension_from_content(content)
    if not detected_ext:
        return filename

    candidate = filename or f"tuyun.{detected_ext}"
    suffix = Path(candidate).suffix
    current_ext = suffix[1:].lower() if suffix else ""
    if current_ext == detected_ext or (
        current_ext == "jpeg" and detected_ext == "jpg"
    ):
        return candidate

    if suffix:
        return f"{candidate[:-len(suffix)]}.{detected_ext}"
    return f"{candidate}.{detected_ext}"


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
