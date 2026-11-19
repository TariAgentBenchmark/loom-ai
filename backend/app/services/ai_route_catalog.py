"""Additional admin-only routes. No credentials or public task API overrides."""

from copy import deepcopy

PROMPT_EDIT_2K_ROUTE = "prompt_edit.model1.2k"
PROMPT_EDIT_4K_ROUTE = "prompt_edit.model1.4k"
PROMPT_EDIT_PRO_ROUTE = "prompt_edit.pro.2k"
COMBINED_DETAIL_ROUTE = "extract_pattern.combined.detail"
DENOISE_ROUTE = "denoise.4k"
FLAT_TO_3D_ROUTE = "flat_to_3d.2k"
YARN_ROUTE = "embroidery.yarn.2k"
SEAMLESS_ROUTE = "seamless.image"
GENERAL2_ROUTE = "extract_pattern.general_2"
VECTOR_ROUTE = "vectorize.provider"
UPSCALE_ROUTE = "upscale.standard"


def extend_route_catalog(catalog):
    template = catalog["extract_pattern.combined.general_2"]["providers"]

    def gemini(label, resolution, default_model, *, seedream=False, native=False):
        providers = deepcopy(template)
        for provider in providers.values():
            provider["models"] = [
                m for m in provider["models"] if m["resolution"] == resolution
            ]
            preferred = next(
                (m for m in provider["models"] if m["value"] == default_model),
                provider["models"][0],
            )
            provider["default_model"] = preferred["value"]
        if native:
            providers["apyi"]["models"].insert(
                0,
                {
                    "value": "gemini-2.5-flash-image",
                    "api_model": "gemini-2.5-flash-image",
                    "resolution": "NATIVE",
                },
            )
            providers["apyi"]["default_model"] = "gemini-2.5-flash-image"
        if seedream:
            providers["seedream"] = {
                "label": "Seedream",
                "client": "seedream",
                "models": [
                    {"value": "seedream", "api_model": "seedream", "resolution": "2K"}
                ],
                "default_model": "seedream",
                "description": "异步任务接口，当前实测2K；不支持作为4K线路。",
            }
        return {
            "label": label,
            "description": "仅后台手动切换，与原功能共用参数；只影响新任务，不改变积分。改图的单张/双参考图/批量使用同一配置。",
            "default_provider": "seedream" if seedream else "apyi",
            "providers": providers,
        }

    for key, label, resolution, model in [
        (
            PROMPT_EDIT_2K_ROUTE,
            "用嘴改图 / 模型1 / 2K",
            "2K",
            "gemini-3.1-flash-image-preview-2k",
        ),
        (
            PROMPT_EDIT_4K_ROUTE,
            "用嘴改图 / 模型1 / 4K",
            "4K",
            "gemini-3-pro-image-preview-4k",
        ),
        (DENOISE_ROUTE, "布纹去噪 / 4K", "4K", "gemini-3-pro-image-preview-4k"),
        (FLAT_TO_3D_ROUTE, "平面转3D / 2K", "2K", "gemini-3.1-flash-image-preview-2k"),
        (YARN_ROUTE, "刺绣 / 毛线效果 / 2K", "2K", "gemini-3.1-flash-image-preview-2k"),
        (
            GENERAL2_ROUTE,
            "提取花型 / 旧通用Gemini分支 / 4K",
            "4K",
            "gemini-3-pro-image-preview-4k",
        ),
    ]:
        catalog[key] = gemini(label, resolution, model)
    catalog[PROMPT_EDIT_PRO_ROUTE] = gemini(
        "用嘴改图 / 模型pro / 2K",
        "2K",
        "gemini-3.1-flash-image-preview-2k",
        seedream=True,
    )
    catalog[COMBINED_DETAIL_ROUTE] = gemini(
        "综合模型 / 原普通香蕉（现Seedream）分支",
        "2K",
        "gemini-3.1-flash-image-preview-2k",
        seedream=True,
    )
    catalog[SEAMLESS_ROUTE] = gemini(
        "四方连续转换", "2K", "gemini-3.1-flash-image-preview-2k", native=True
    )

    def option(label, client, model="current"):
        return {
            "label": label,
            "client": client,
            "models": [{"value": model, "api_model": model, "resolution": "NATIVE"}],
            "default_model": model,
        }

    catalog[VECTOR_ROUTE] = {
        "label": "矢量化 / EPS、SVG",
        "description": "明确选择ZFY、A8或WebAPI时只调用该线路，不自动切换；原配置保留已有行为。",
        "default_provider": "current",
        "providers": {
            "current": option("原配置（保持既有行为）", "vector_current"),
            "zfy": option("ZFY / add_task", "zfy_vectorizer"),
            "a8": option("A8 / zfyai-api-key", "a8_vectorizer"),
            "webapi": option("WebAPI / mm.kknc", "vector_webapi"),
        },
    }
    catalog[UPSCALE_ROUTE] = {
        "label": "高清 / 普通高清",
        "description": "不改变前台引擎选项及其计费；选择后仅替换执行线路，4K超清不受此项影响。",
        "default_provider": "current",
        "providers": {
            "current": option("原配置（保持前台引擎）", "upscale_current"),
            "runninghub_vr2": option("RunningHub VR2", "runninghub"),
            "meitu_v2": option("美图超清V2", "meitu"),
        },
    }

    # These have no interchangeable, already-integrated second provider.
    for key, label, provider, client, description in [
        (
            "extract_pattern.general_1",
            "提取花型 / 通用四图",
            "runninghub",
            "runninghub",
            "专用RunningHub四图工作流，无兼容备用线路。",
        ),
        (
            "extract_pattern.positioning",
            "提取花型 / 定位",
            "runninghub",
            "runninghub",
            "专用RunningHub定位工作流，无兼容备用线路。",
        ),
        (
            "extract_pattern.denim",
            "提取花型 / 牛仔",
            "apyi",
            "apyi_openai",
            "GPT Image 2.5专用双图流程，无已接入的同能力备用线路。",
        ),
        (
            "extract_pattern.fine",
            "提取花型 / 烫画",
            "apyi",
            "apyi_openai",
            "GPT专用双图流程，无已接入的同能力备用线路。",
        ),
        (
            "extract_pattern.gpt",
            "综合模型、综合T2 / GPT分支",
            "tuzi",
            "tuzi_openai",
            "仅已接入Tuzi；保留已有VIP→标准兜底，本次不新增自动切换。",
        ),
        (
            "extract_pattern.runninghub",
            "综合模型 / RunningHub分支",
            "runninghub",
            "runninghub",
            "专用RunningHub工作流，无兼容备用线路。",
        ),
        (
            "seamless_loop",
            "接循环",
            "runninghub",
            "runninghub",
            "含方向/贴合度的专用工作流，无兼容备用线路。",
        ),
        (
            "expand_image",
            "扩图",
            "runninghub",
            "runninghub",
            "含四边扩展参数的专用工作流，无兼容备用线路。",
        ),
        (
            "remove_watermark",
            "去水印",
            "runninghub",
            "runninghub",
            "专用去水印工作流，无兼容备用线路。",
        ),
        (
            "similar_image",
            "相似图",
            "runninghub",
            "runninghub",
            "专用相似图工作流，无兼容备用线路。",
        ),
        (
            "embroidery.stitch",
            "刺绣 / 刺绣效果",
            "runninghub",
            "runninghub",
            "专用刺绣工作流，无兼容备用线路。",
        ),
        (
            "upscale.4k",
            "高清 / 4K超清",
            "runninghub",
            "runninghub",
            "专用4K工作流，不能用2K生成接口替代。",
        ),
    ]:
        catalog[key] = {
            "label": label,
            "description": description,
            "read_only": True,
            "default_provider": provider,
            "providers": {provider: option(provider, client)},
        }


def task_route_keys(task_type, options):
    """Only dispatch routes actually consumed by this task, never user-supplied keys."""
    if task_type == "prompt_edit":
        mode = str(options.get("model") or "new").strip().lower().replace("-", "_")
        if mode == "seedream_pro":
            return [PROMPT_EDIT_PRO_ROUTE]
        return [
            PROMPT_EDIT_4K_ROUTE
            if mode
            in {
                "pro_4k",
                "pro4k",
                "banana_pro_4k",
                "nano_banana_pro_4k",
                "gemini_3_pro_4k",
                "gemini_3_pro_image_preview_4k",
            }
            else PROMPT_EDIT_2K_ROUTE
        ]
    if task_type == "extract_pattern":
        kind = (
            str(options.get("pattern_type") or "general_1")
            .strip()
            .lower()
            .replace("-", "_")
        )
        if kind in {"combined", "composite"}:
            return ["extract_pattern.combined.general_2", COMBINED_DETAIL_ROUTE]
        if kind in {"combined_t2", "composite_t2", "compositet2", "t2"}:
            return ["extract_pattern.combined_t2.gemini"]
        if kind in {"general_2", "general2"}:
            return [GENERAL2_ROUTE]
        return []
    if task_type == "embroidery":
        return (
            [YARN_ROUTE]
            if str(options.get("embroidery_mode") or "embroidery").strip().lower()
            in {"yarn", "wool", "woolen"}
            else []
        )
    if task_type == "upscale":
        return (
            []
            if str(options.get("engine") or "").strip().lower() == "runninghub_4k_ultra"
            else [UPSCALE_ROUTE]
        )
    key = {
        "denoise": DENOISE_ROUTE,
        "flat_to_3d": FLAT_TO_3D_ROUTE,
        "seamless": SEAMLESS_ROUTE,
        "vectorize": VECTOR_ROUTE,
    }.get(task_type)
    return [key] if key else []
