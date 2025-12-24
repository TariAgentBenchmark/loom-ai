"""AI客户端异常类"""
import json
from typing import Any, Callable, Dict, Optional

import httpx


class AIClientException(Exception):
    """AI客户端异常基类，包含API响应详情"""

    def __init__(
        self,
        message: str,
        api_name: str = None,
        status_code: int = None,
        response_body: Any = None,
        request_data: Dict = None,
    ):
        super().__init__(message)
        self.message = message
        self.api_name = api_name
        self.status_code = status_code
        self.response_body = response_body
        self.request_data = request_data

    def get_detailed_error(self, truncate_large_fields: bool = True) -> str:
        """获取详细错误信息，包含API响应"""
        parts = [f"错误信息: {self.message}"]

        if self.api_name:
            parts.append(f"API服务: {self.api_name}")

        if self.status_code:
            parts.append(f"HTTP状态码: {self.status_code}")

        if self.response_body is not None:
            response_str = self._format_response(
                self.response_body, truncate_large_fields
            )
            parts.append(f"API响应内容:\n{response_str}")

        if self.request_data:
            request_str = self._format_response(
                self.request_data, truncate_large_fields
            )
            parts.append(f"请求参数:\n{request_str}")

        return "\n\n".join(parts)

    def _format_response(self, data: Any, truncate: bool = True) -> str:
        """格式化响应数据，处理大字段"""
        try:
            if isinstance(data, (dict, list)):
                if truncate:
                    data = self._truncate_large_fields(data)
                return json.dumps(data, ensure_ascii=False, indent=2)
            elif isinstance(data, str):
                if truncate and len(data) > 1000:
                    return data[:1000] + f"\n...(已截断，总长度: {len(data)} 字符)"
                return data
            else:
                return str(data)
        except Exception:
            return str(data)

    def _truncate_large_fields(self, data: Any, max_length: int = 500) -> Any:
        """截断大字段（如base64图片）"""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if isinstance(value, str) and len(value) > max_length:
                    # 检测可能是base64或大文本
                    if self._is_likely_base64(value) or self._is_likely_large_data(
                        key
                    ):
                        result[key] = f"<已截断: {len(value)} 字符, 前100字符: {value[:100]}...>"
                    else:
                        result[key] = (
                            value[:max_length]
                            + f"...<已截断，总长度: {len(value)} 字符>"
                        )
                elif isinstance(value, (dict, list)):
                    result[key] = self._truncate_large_fields(value, max_length)
                else:
                    result[key] = value
            return result
        elif isinstance(data, list):
            return [self._truncate_large_fields(item, max_length) for item in data]
        else:
            return data

    def _is_likely_base64(self, value: str) -> bool:
        """判断是否可能是base64编码"""
        if len(value) < 100:
            return False
        # 简单检测：长度大于100且包含base64常见字符
        import re

        return bool(re.match(r"^[A-Za-z0-9+/=]+$", value[:100]))

    def _is_likely_large_data(self, key: str) -> bool:
        """根据字段名判断是否是大数据字段"""
        large_data_keys = [
            "image",
            "base64",
            "data",
            "content",
            "file",
            "buffer",
            "binary",
        ]
        key_lower = key.lower()
        return any(keyword in key_lower for keyword in large_data_keys)


async def safe_http_request(
    api_name: str,
    request_func: Callable,
    request_data: Dict = None,
    error_message_prefix: str = None,
) -> Any:
    """
    安全的HTTP请求包装器，自动捕获并转换为AIClientException

    Args:
        api_name: API服务名称（如"GQCH", "Meitu"）
        request_func: 执行HTTP请求的异步函数
        request_data: 请求参数（用于错误日志）
        error_message_prefix: 错误消息前缀

    Returns:
        请求函数的返回值

    Raises:
        AIClientException: 包含详细错误信息的异常
    """
    try:
        return await request_func()
    except httpx.HTTPStatusError as e:
        raise AIClientException(
            message=f"{error_message_prefix or api_name} HTTP错误: {e.response.status_code}",
            api_name=api_name,
            status_code=e.response.status_code,
            response_body=e.response.text,
            request_data=request_data,
        ) from e
    except httpx.TimeoutException as e:
        raise AIClientException(
            message=f"{error_message_prefix or api_name} 请求超时",
            api_name=api_name,
            request_data=request_data,
        ) from e
    except httpx.RequestError as e:
        raise AIClientException(
            message=f"{error_message_prefix or api_name} 网络请求失败: {str(e)}",
            api_name=api_name,
            request_data=request_data,
        ) from e
    except AIClientException:
        raise
    except Exception as e:
        raise AIClientException(
            message=f"{error_message_prefix or api_name} 未知错误: {str(e)}",
            api_name=api_name,
            request_data=request_data,
        ) from e
