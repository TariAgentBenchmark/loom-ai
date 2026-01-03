from typing import Optional

DEFAULT_USER_ERROR_MESSAGE = "服务器火爆，重试一下。"


def mask_task_error_message(
    message: Optional[str],
    code: Optional[str],
    *,
    is_admin: bool,
) -> str:
    if is_admin:
        return message or DEFAULT_USER_ERROR_MESSAGE

    if message:
        if "积分不足" in message:
            return "积分不足，请充值后再试"
        if code in {"API_ERROR", "SERVICE_ERROR", "P006"}:
            return DEFAULT_USER_ERROR_MESSAGE

        lowered = message.lower()
        if "traceback" in lowered or "调用栈" in message:
            return DEFAULT_USER_ERROR_MESSAGE
        if "下游api错误" in message or "服务内部错误" in message:
            return DEFAULT_USER_ERROR_MESSAGE
        if "runninghub" in lowered:
            return DEFAULT_USER_ERROR_MESSAGE

        return message

    return DEFAULT_USER_ERROR_MESSAGE
