from typing import Any, Dict, List, Optional


RESULT_PREVIEWS_METADATA_KEY = "resultPreviews"


def get_result_preview_urls(
    metadata: Optional[Dict[str, Any]],
    expected_count: Optional[int] = None,
) -> List[str]:
    """Return explicit preview refs stored for result files, preserving index order."""
    if not isinstance(metadata, dict):
        return [""] * expected_count if expected_count else []

    previews = metadata.get(RESULT_PREVIEWS_METADATA_KEY)
    raw_urls: Any = None
    if isinstance(previews, dict):
        raw_urls = previews.get("urls")
    elif isinstance(previews, (list, str)):
        raw_urls = previews

    if isinstance(raw_urls, str):
        urls = [url.strip() for url in raw_urls.split(",")]
    elif isinstance(raw_urls, list):
        urls = [str(url).strip() if url else "" for url in raw_urls]
    else:
        urls = []

    if expected_count is not None:
        if len(urls) < expected_count:
            urls.extend([""] * (expected_count - len(urls)))
        else:
            urls = urls[:expected_count]

    return urls


def with_result_previews(
    metadata: Optional[Dict[str, Any]],
    urls: List[str],
    filenames: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Return metadata with explicit result preview refs attached."""
    next_metadata = dict(metadata or {})
    preview_payload: Dict[str, Any] = {"urls": urls}
    if filenames is not None:
        preview_payload["filenames"] = filenames
    next_metadata[RESULT_PREVIEWS_METADATA_KEY] = preview_payload
    return next_metadata
