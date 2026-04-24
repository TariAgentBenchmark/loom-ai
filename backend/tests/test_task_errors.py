from app.services.ai_client.exceptions import SIMILARITY_REJECTED_MESSAGE
from app.utils.task_errors import mask_task_error_message


def test_mask_task_error_message_preserves_known_model_rejections():
    message = (
        "[下游API错误]\n\n"
        f"错误信息: {SIMILARITY_REJECTED_MESSAGE}\n\n"
        "API服务: apyi_openai"
    )

    assert mask_task_error_message(
        message,
        "API_ERROR",
        is_admin=False,
    ) == SIMILARITY_REJECTED_MESSAGE
