import asyncio
import logging
import mimetypes
import time
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.services.api_limiter import api_limiter


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

        task_id = await self._submit_task(node_info_list, resolved_workflow_id)
        return await self._poll_task(task_id)

    async def _upload_file(self, image_bytes: bytes, filename: str) -> str:
        url = f"{self.base_url}/task/openapi/upload"
        mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        data = {"apiKey": self.api_key, "fileType": "input"}
        files = {"file": (filename, image_bytes, mime_type)}

        async with api_limiter.slot("runninghub"):
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, data=data, files=files)
                response.raise_for_status()
                payload = response.json()

        if payload.get("code") != 0:
            msg = payload.get("msg") or "上传失败"
            raise Exception(f"RunningHub文件上传失败: {msg}")

        file_name = (payload.get("data") or {}).get("fileName")
        if not file_name:
            raise Exception("RunningHub上传响应缺少fileName")
        return file_name

    async def _submit_task(self, node_info_list: List[Dict[str, Any]], workflow_id: str) -> str:
        url = f"{self.base_url}/task/openapi/create"
        payload = {
            "apiKey": self.api_key,
            "workflowId": workflow_id,
            "nodeInfoList": node_info_list,
        }

        async with api_limiter.slot("runninghub"):
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

        if data.get("code") != 0:
            msg = data.get("msg") or "创建任务失败"
            raise Exception(f"RunningHub任务创建失败: {msg}")

        task_data = data.get("data") or {}
        task_id = task_data.get("taskId")
        if not task_id:
            raise Exception("RunningHub任务创建响应缺少taskId")

        prompt_tips = task_data.get("promptTips")
        if prompt_tips:
            self.logger.debug("RunningHub prompt tips: %s", prompt_tips)

        return task_id

    async def _poll_task(self, task_id: str) -> List[str]:
        url = f"{self.base_url}/task/openapi/outputs"
        payload = {"apiKey": self.api_key, "taskId": task_id}

        start_time = time.monotonic()
        while True:
            async with api_limiter.slot("runninghub"):
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()

            code = data.get("code")
            result_data = data.get("data")

            if code == 0 and result_data:
                urls = [item.get("fileUrl") for item in result_data if item.get("fileUrl")]
                if not urls:
                    raise Exception("RunningHub任务成功但未返回结果URL")
                return urls

            if code == 805:
                failed_reason = (result_data or {}).get("failedReason") if isinstance(result_data, dict) else None
                raise Exception(
                    f"RunningHub任务失败: {data.get('msg') or ''} {failed_reason or ''}".strip()
                )

            if code in {804, 813}:
                if time.monotonic() - start_time > self.poll_timeout:
                    raise TimeoutError("等待RunningHub任务结果超时")
                await asyncio.sleep(self.poll_interval)
                continue

            raise Exception(f"RunningHub返回未知状态: {data}")
