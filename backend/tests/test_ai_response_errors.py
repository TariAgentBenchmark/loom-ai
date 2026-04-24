import pytest

from app.services.ai_client.base_client import BaseAIClient
from app.services.ai_client.exceptions import (
    AIClientException,
    MODEL_BLOCKED_MESSAGE,
    SIMILARITY_REJECTED_MESSAGE,
)


def test_extract_image_urls_raises_clear_similarity_rejection():
    client = BaseAIClient(api_name="apyi_openai")

    response = {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "非常抱歉，生成的图片可能违反了关于与第三方内容相似性的防护限制。如果你认为此判断有误，请重试或修改提示语。",
                },
                "finish_reason": "stop",
            }
        ],
    }

    with pytest.raises(AIClientException, match=SIMILARITY_REJECTED_MESSAGE):
        client._extract_image_urls(response)


def test_extract_image_url_raises_clear_gemini_block_message():
    client = BaseAIClient(api_name="apyi_gemini")

    response = {
        "promptFeedback": {"blockReason": "OTHER"},
        "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 0},
        "modelVersion": "gemini-3-pro-image-preview",
    }

    with pytest.raises(AIClientException, match=MODEL_BLOCKED_MESSAGE):
        client._extract_image_url(response)
