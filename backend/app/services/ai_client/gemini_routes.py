"""Execute a snapshotted admin route; never select another provider on failure."""

from app.services.ai_client.exceptions import AIClientException
from app.services.ai_model_route_service import (
    AI_MODEL_ROUTES_OPTION_KEY,
    AIModelRouteService,
)


def has_route(options, route_key):
    return route_key in ((options or {}).get(AI_MODEL_ROUTES_OPTION_KEY) or {})


def client_for_provider(owner, provider):
    from app.services.ai_client.apyi_gemini_client import ApyiGeminiClient
    from app.services.ai_client.haoee_gemini_client import HaoeeGeminiClient
    from app.services.ai_client.krapi_gemini_client import KrapiGeminiClient
    from app.services.ai_client.tuzi_gemini_client import TuziGeminiClient

    attr, factory = {
        "apyi": ("apyi_gemini_client", ApyiGeminiClient),
        "tuzi": ("tuzi_gemini_client", TuziGeminiClient),
        "haoee": ("haoee_gemini_client", HaoeeGeminiClient),
        "krapi": ("krapi_gemini_client", KrapiGeminiClient),
    }[provider]
    existing = getattr(owner, attr, None)
    return existing if existing is not None else factory()


async def generate_routed_image(owner, images, prompt, options, route_key):
    route = AIModelRouteService.resolve_runtime_from_options(options, route_key)
    if route["provider"] == "seedream":
        raise ValueError("Seedream must use its durable asynchronous task client")
    client = client_for_provider(owner, route["provider"])
    ratio = (options or {}).get("aspect_ratio")
    ratio = None if ratio == "auto" else ratio
    width, height = (options or {}).get("width"), (options or {}).get("height")
    if (width or height) and route["provider"] != "apyi":
        raise ValueError("所选线路不支持显式宽高，请选择图片比例或Apyi线路")
    if ratio and ratio not in client.SUPPORTED_ASPECT_RATIOS:
        raise ValueError("所选线路不支持该图片比例")
    if route["resolution"] == "NATIVE":
        result = await client.process_image(
            images[0],
            prompt,
            "image/png",
            aspect_ratio=ratio,
            width=(options or {}).get("width"),
            height=(options or {}).get("height"),
        )
    elif len(images) == 1 and not (width and height):
        result = await client.generate_image_preview(
            images[0],
            prompt,
            "image/png",
            aspect_ratio=ratio,
            resolution=route["resolution"],
            model_name=route["api_model"],
        )
    elif route["provider"] in {"apyi", "krapi"}:
        kwargs = {
            "aspect_ratio": ratio,
            "resolution": route["resolution"],
            "model_name": route["api_model"],
        }
        if route["provider"] == "apyi":
            kwargs.update(
                width=(options or {}).get("width"), height=(options or {}).get("height")
            )
        result = await client.generate_image_preview_multi(
            images, prompt, "image/png", **kwargs
        )
    else:
        # Tuzi/Haoee use the same Gemini parts protocol but have no multi-image
        # convenience method. Keep their endpoint mapping and imageSize spelling.
        model = route["api_model"]
        if route["provider"] == "haoee":
            client._ensure_credentials()
            model = client._resolve_endpoint_model(model)
        parts = [{"text": prompt}] + [
            {
                "inline_data": {
                    "mime_type": "image/png",
                    "data": client._image_to_base64(raw, "PNG"),
                }
            }
            for raw in images
        ]
        config = {"imageSize": route["resolution"]}
        if ratio and ratio != "auto":
            if ratio not in client.SUPPORTED_ASPECT_RATIOS:
                raise ValueError("所选线路不支持该图片比例")
            config["aspectRatio"] = ratio
        result = await client._make_request(
            "POST",
            f"/v1beta/models/{model}:generateContent",
            {
                "contents": [{"parts": parts}],
                "generationConfig": {
                    "responseModalities": ["IMAGE"],
                    "imageConfig": config,
                },
            },
        )
    url = client._extract_image_url(result)
    if not isinstance(url, str) or not url.strip():
        raise AIClientException("所选线路未返回有效图片", api_name=route["provider"])
    return url.strip()
