import asyncio
import logging
import mimetypes
import time
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.services.api_limiter import api_limiter
from app.services.ai_client.exceptions import AIClientException


class RunningHubClient:
    """Client for interacting with RunningHub workflow OpenAPI."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        workflow_id: Optional[str] = None,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.api_key = (api_key or settings.runninghub_api_key).strip()
        self.workflow_id = (
            workflow_id or settings.runninghub_workflow_id_positioning
        ).strip()
        self.base_url = settings.runninghub_api_base_url.rstrip("/")
        self.image_node_id = settings.runninghub_positioning_node_id
        self.image_field_name = settings.runninghub_positioning_field_name
        self.poll_interval = max(1, settings.runninghub_poll_interval_seconds)
        self.poll_timeout = max(self.poll_interval, settings.runninghub_poll_timeout_seconds)

    def _truncate_text(self, text: str, limit: int = 2000) -> str:
        if not text:
            return ""
        if len(text) <= limit:
            return text
        return f"{text[:limit]}...(truncated)"

    def _log_http_error(self, action: str, exc: httpx.HTTPStatusError) -> None:
        response = exc.response
        body = self._truncate_text(response.text or "")
        self.logger.warning(
            "RunningHub %s HTTP %s: %s",
            action,
            response.status_code,
            body,
        )

    def _parse_response_json(self, action: str, response: httpx.Response) -> Dict[str, Any]:
        try:
            return response.json()
        except ValueError:
            body = self._truncate_text(response.text or "")
            self.logger.warning(
                "RunningHub %s invalid JSON response: status=%s body=%s",
                action,
                response.status_code,
                body,
            )
            raise

    def _mask_payload(self, payload: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if payload is None:
            return None
        if not isinstance(payload, dict):
            return payload
        masked = dict(payload)
        for key in ("apiKey", "api_key"):
            if key in masked and masked[key]:
                masked[key] = "<redacted>"
        return masked

    def _summarize_files(self, files: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not files:
            return None
        summary: Dict[str, Any] = {}
        for field, value in files.items():
            if isinstance(value, (tuple, list)) and value:
                filename = value[0] if len(value) > 0 else None
                content = value[1] if len(value) > 1 else None
                content_type = value[2] if len(value) > 2 else None
                size = len(content) if isinstance(content, (bytes, bytearray)) else None
                summary[field] = {
                    "filename": filename,
                    "size": size,
                    "content_type": content_type,
                }
            else:
                summary[field] = {"type": type(value).__name__}
        return summary

    def _build_request_context(
        self,
        url: str,
        data: Optional[Dict[str, Any]],
        json: Optional[Dict[str, Any]],
        files: Optional[Dict[str, Any]],
        action: str,
    ) -> Dict[str, Any]:
        return {
            "action": action,
            "url": url,
            "data": self._mask_payload(data),
            "json": self._mask_payload(json),
            "files": self._summarize_files(files),
        }

    async def _post_json(
        self,
        url: str,
        *,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        action: str,
    ) -> Dict[str, Any]:
        request_context = self._build_request_context(url, data, json, files, action)
        try:
            async with api_limiter.slot("runninghub"):
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(url, data=data, json=json, files=files)
                    response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            self._log_http_error(action, exc)
            raise AIClientException(
                message=f"RunningHub HTTP错误: {exc.response.status_code}",
                api_name="RunningHub",
                status_code=exc.response.status_code,
                response_body=self._truncate_text(exc.response.text or ""),
                request_data=request_context,
            ) from exc
        except httpx.RequestError as exc:
            self.logger.warning(
                "RunningHub %s request error: %s", action, repr(exc)
            )
            raise AIClientException(
                message=f"RunningHub请求异常: {repr(exc)}",
                api_name="RunningHub",
                request_data=request_context,
            ) from exc

        try:
            return self._parse_response_json(action, response)
        except ValueError as exc:
            raise AIClientException(
                message=f"RunningHub响应解析失败: {str(exc)}",
                api_name="RunningHub",
                status_code=response.status_code,
                response_body=self._truncate_text(response.text or ""),
                request_data=request_context,
            ) from exc

    def _ensure_configured(self, workflow_id: Optional[str] = None) -> str:
        if not self.api_key:
            raise Exception("RunningHub API尚未配置，请设置API_KEY环境变量")

        resolved_workflow_id = (workflow_id or self.workflow_id or "").strip()
        if not resolved_workflow_id:
            raise Exception("RunningHub工作流尚未配置，请设置workflowId环境变量")

        return resolved_workflow_id

    def _parse_node_ids(self, raw_node_ids: Optional[str]) -> List[str]:
        if not raw_node_ids:
            raise Exception("RunningHub未配置nodeId")

        nodes = [node.strip() for node in str(raw_node_ids).split(",") if node.strip()]
        if not nodes:
            raise Exception("RunningHub nodeId配置格式无效")
        return nodes

    async def run_positioning_workflow(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Run the positioning workflow and return comma separated result URLs."""

        workflow_id = self._ensure_configured()
        options = options or {}
        filename = options.get("original_filename") or "positioning.png"

        uploaded_name = await self._upload_file(image_bytes, filename)
        node_ids = self._parse_node_ids(self.image_node_id)
        field_name = (options.get("field_name") or self.image_field_name).strip()
        if not field_name:
            raise Exception("RunningHub缺少字段配置 field_name")

        node_info_list = [
            {
                "nodeId": str(node_id),
                "fieldName": field_name,
                "fieldValue": uploaded_name,
            }
            for node_id in node_ids
        ]

        task_id = await self._submit_task(node_info_list, workflow_id)
        result_urls = await self._poll_task(task_id)
        return ",".join(result_urls)

    async def run_workflow_with_custom_nodes(
        self,
        image_bytes: bytes,
        workflow_id: Optional[str],
        node_ids: Optional[str],
        field_name: Optional[str],
        options: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Run a configurable RunningHub workflow and return list of result URLs.

        Args:
            image_bytes: 待处理图片字节
            workflow_id: RunningHub工作流ID
            node_ids: 节点ID，支持以逗号分隔多个
            field_name: 节点字段名称
            options: 额外参数（目前用于读取原始文件名）
        """

        resolved_workflow_id = self._ensure_configured(workflow_id)
        resolved_node_ids = self._parse_node_ids(node_ids or self.image_node_id)
        resolved_field_name = (field_name or self.image_field_name).strip()
        if not resolved_field_name:
            raise Exception("RunningHub缺少字段配置 field_name")

        options = options or {}
        filename = options.get("original_filename") or "runninghub.png"

        uploaded_name = await self._upload_file(image_bytes, filename)
        node_info_list = [
            {
                "nodeId": str(node_id),
                "fieldName": resolved_field_name,
                "fieldValue": uploaded_name,
            }
            for node_id in resolved_node_ids
        ]

        # 可选：为特定节点追加额外字段（例如 denoise 调节）
        denoise_value = (options or {}).get("denoise")
        if denoise_value is not None:
            node_info_list.append(
                {
                    "nodeId": str((options or {}).get("denoise_node_id") or 3),
                    "fieldName": "denoise",
                    "fieldValue": str(denoise_value),
                }
            )

        task_id = await self._submit_task(node_info_list, resolved_workflow_id)
        return await self._poll_task(task_id)

    async def run_seamless_loop_workflow(
        self,
        image_bytes: bytes,
        workflow_id: str,
        image_node_id: str,
        image_field_name: str,
        direction_node_id: str,
        direction_field_name: str,
        direction_value: int,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Run seamless loop workflow with image and direction parameters.

        Args:
            image_bytes: 待处理图片字节
            workflow_id: RunningHub工作流ID
            image_node_id: 图片输入节点ID
            image_field_name: 图片字段名称
            direction_node_id: 方向控制节点ID
            direction_field_name: 方向字段名称
            direction_value: 方向值 (1=四周, 2=上下, 3=左右)
            options: 额外参数
        """
        resolved_workflow_id = self._ensure_configured(workflow_id)
        options = options or {}
        filename = options.get("original_filename") or "seamless_loop.png"

        # Upload image
        uploaded_name = await self._upload_file(image_bytes, filename)

        # Build node info list with both image and direction nodes
        node_info_list = [
            {
                "nodeId": str(image_node_id),
                "fieldName": image_field_name,
                "fieldValue": uploaded_name,
            },
            {
                "nodeId": str(direction_node_id),
                "fieldName": direction_field_name,
                "fieldValue": str(direction_value),
            },
        ]

        task_id = await self._submit_task(node_info_list, resolved_workflow_id)
        return await self._poll_task(task_id)

    async def run_expand_image_workflow(
        self,
        image_bytes: bytes,
        workflow_id: str,
        image_node_id: str,
        image_field_name: str,
        expand_top: float,
        expand_bottom: float,
        expand_left: float,
        expand_right: float,
        top_node_id: str,
        bottom_node_id: str,
        left_node_id: str,
        right_node_id: str,
        margin_field_name: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Run expand image workflow with image and margin parameters.

        Args:
            image_bytes: 待处理图片字节
            workflow_id: RunningHub工作流ID
            image_node_id: 图片输入节点ID
            image_field_name: 图片字段名称
            expand_top: 上边距比例（如0.5表示扩展原高度的50%）
            expand_bottom: 下边距比例
            expand_left: 左边距比例
            expand_right: 右边距比例
            top_node_id: 上边距节点ID
            bottom_node_id: 下边距节点ID
            left_node_id: 左边距节点ID
            right_node_id: 右边距节点ID
            margin_field_name: 边距字段名称
            options: 额外参数
        """
        from PIL import Image
        from io import BytesIO

        resolved_workflow_id = self._ensure_configured(workflow_id)
        options = options or {}
        filename = options.get("original_filename") or "expand_image.png"

        # Get image dimensions
        img = Image.open(BytesIO(image_bytes))
        width, height = img.size

        # Convert ratio to pixels
        top_pixels = int(height * expand_top)
        bottom_pixels = int(height * expand_bottom)
        left_pixels = int(width * expand_left)
        right_pixels = int(width * expand_right)

        # Upload image
        uploaded_name = await self._upload_file(image_bytes, filename)

        # Build node info list with image and all margin nodes (in pixels)
        node_info_list = [
            {
                "nodeId": str(image_node_id),
                "fieldName": image_field_name,
                "fieldValue": uploaded_name,
            },
            {
                "nodeId": str(top_node_id),
                "fieldName": margin_field_name,
                "fieldValue": top_pixels,
            },
            {
                "nodeId": str(bottom_node_id),
                "fieldName": margin_field_name,
                "fieldValue": bottom_pixels,
            },
            {
                "nodeId": str(left_node_id),
                "fieldName": margin_field_name,
                "fieldValue": left_pixels,
            },
            {
                "nodeId": str(right_node_id),
                "fieldName": margin_field_name,
                "fieldValue": right_pixels,
            },
        ]

        self.logger.info(
            "Submitting expand image workflow %s (image: %dx%d) with nodes: %s",
            resolved_workflow_id,
            width,
            height,
            node_info_list,
        )

        task_id = await self._submit_task(node_info_list, resolved_workflow_id)
        return await self._poll_task(task_id)

    async def _upload_file(self, image_bytes: bytes, filename: str) -> str:
        url = f"{self.base_url}/task/openapi/upload"
        mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        data = {"apiKey": self.api_key, "fileType": "input"}
        files = {"file": (filename, image_bytes, mime_type)}

        payload = await self._post_json(
            url,
            data=data,
            files=files,
            action="upload",
        )

        if payload.get("code") != 0:
            msg = payload.get("msg") or "上传失败"
            self.logger.warning(
                "RunningHub upload failed: filename=%s size=%s response=%s",
                filename,
                len(image_bytes),
                payload,
            )
            raise AIClientException(
                message=f"RunningHub文件上传失败: {msg}",
                api_name="RunningHub",
                status_code=200,
                response_body=payload,
                request_data={"filename": filename, "size": len(image_bytes)},
            )

        file_name = (payload.get("data") or {}).get("fileName")
        if not file_name:
            raise AIClientException(
                message="RunningHub上传响应缺少fileName",
                api_name="RunningHub",
                status_code=200,
                response_body=payload,
                request_data={"filename": filename, "size": len(image_bytes)},
            )
        return file_name

    async def _submit_task(self, node_info_list: List[Dict[str, Any]], workflow_id: str) -> str:
        url = f"{self.base_url}/task/openapi/create"
        payload = {
            "apiKey": self.api_key,
            "workflowId": workflow_id,
            "nodeInfoList": node_info_list,
        }

        try:
            data = await self._post_json(
                url,
                json=payload,
                action="create task",
            )

            if data.get("code") != 0:
                msg = data.get("msg") or "创建任务失败"
                raise AIClientException(
                    message=f"RunningHub任务创建失败: {msg}",
                    api_name="RunningHub",
                    status_code=200,
                    response_body=data,
                    request_data={"workflow_id": workflow_id, "node_info": node_info_list},
                )

            task_data = data.get("data") or {}
            task_id = task_data.get("taskId")
            if not task_id:
                raise AIClientException(
                    message="RunningHub任务创建响应缺少taskId",
                    api_name="RunningHub",
                    status_code=200,
                    response_body=data,
                    request_data={"workflow_id": workflow_id, "node_info": node_info_list},
                )

            prompt_tips = task_data.get("promptTips")
            if prompt_tips:
                self.logger.debug("RunningHub prompt tips: %s", prompt_tips)

            return task_id

        except AIClientException:
            raise
        except httpx.HTTPStatusError as e:
            raise AIClientException(
                message=f"RunningHub HTTP错误: {e.response.status_code}",
                api_name="RunningHub",
                status_code=e.response.status_code,
                response_body=e.response.text,
                request_data={"workflow_id": workflow_id, "node_info": node_info_list},
            ) from e
        except httpx.RequestError as e:
            raise AIClientException(
                message=f"RunningHub请求异常: {str(e)}",
                api_name="RunningHub",
                request_data={"workflow_id": workflow_id, "node_info": node_info_list},
            ) from e
        except Exception as e:
            raise AIClientException(
                message=f"RunningHub请求异常: {str(e)}",
                api_name="RunningHub",
                request_data={"workflow_id": workflow_id, "node_info": node_info_list},
            ) from e

    async def _poll_task(self, task_id: str) -> List[str]:
        url = f"{self.base_url}/task/openapi/outputs"
        payload = {"apiKey": self.api_key, "taskId": task_id}

        start_time = time.monotonic()
        while True:
            data = await self._post_json(
                url,
                json=payload,
                action=f"poll task {task_id}",
            )

            code = data.get("code")
            result_data = data.get("data")

            if code == 0 and result_data:
                urls = [item.get("fileUrl") for item in result_data if item.get("fileUrl")]
                if not urls:
                self.logger.warning(
                    "RunningHub task returned no URLs: task_id=%s response=%s",
                    task_id,
                    data,
                )
                raise AIClientException(
                    message="RunningHub任务成功但未返回结果URL",
                    api_name="RunningHub",
                    status_code=200,
                    response_body=data,
                    request_data={"task_id": task_id},
                )
                return urls

            if code == 805:
                failed_reason = (result_data or {}).get("failedReason") if isinstance(result_data, dict) else None
                self.logger.warning(
                    "RunningHub task failed: task_id=%s response=%s",
                    task_id,
                    data,
                )
                raise AIClientException(
                    message=f"RunningHub任务失败: {data.get('msg') or ''} {failed_reason or ''}".strip(),
                    api_name="RunningHub",
                    status_code=200,
                    response_body=data,
                    request_data={"task_id": task_id},
                )

            if code in {804, 813}:
                if time.monotonic() - start_time > self.poll_timeout:
                    raise TimeoutError("等待RunningHub任务结果超时")
                await asyncio.sleep(self.poll_interval)
                continue

            self.logger.warning(
                "RunningHub task returned unknown status: task_id=%s response=%s",
                task_id,
                data,
            )
            raise AIClientException(
                message=f"RunningHub返回未知状态: {data}",
                api_name="RunningHub",
                status_code=200,
                response_body=data,
                request_data={"task_id": task_id},
            )
