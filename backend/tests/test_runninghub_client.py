from io import BytesIO

import pytest
from PIL import Image

from app.services.ai_client.runninghub_client import RunningHubClient


def _make_image_bytes(width: int, height: int) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), color=(240, 240, 240)).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_expand_image_sets_target_megapixels_from_requested_canvas(monkeypatch):
    client = RunningHubClient(api_key="test-key")
    captured = {}

    async def fake_upload_file(image_bytes, filename):
        return "api/input.png"

    async def fake_submit_task(node_info_list, workflow_id):
        captured["node_info_list"] = node_info_list
        captured["workflow_id"] = workflow_id
        return "task_123"

    async def fake_poll_task(task_id):
        captured["task_id"] = task_id
        return ["https://example.com/result.png"]

    monkeypatch.setattr(client, "_upload_file", fake_upload_file)
    monkeypatch.setattr(client, "_submit_task", fake_submit_task)
    monkeypatch.setattr(client, "_poll_task", fake_poll_task)

    result = await client.run_expand_image_workflow(
        image_bytes=_make_image_bytes(1264, 1480),
        workflow_id="workflow_123",
        image_node_id="166",
        image_field_name="image",
        expand_top=0.1,
        expand_bottom=0.1,
        expand_left=0.1,
        expand_right=0.1,
        top_node_id="200",
        bottom_node_id="201",
        left_node_id="202",
        right_node_id="203",
        margin_field_name="value",
        target_megapixels_node_id="230",
        target_megapixels_field_name="megapixels",
    )

    assert result == ["https://example.com/result.png"]
    assert captured["workflow_id"] == "workflow_123"
    assert captured["task_id"] == "task_123"
    assert captured["node_info_list"] == [
        {"nodeId": "166", "fieldName": "image", "fieldValue": "api/input.png"},
        {"nodeId": "200", "fieldName": "value", "fieldValue": 148},
        {"nodeId": "201", "fieldName": "value", "fieldValue": 148},
        {"nodeId": "202", "fieldName": "value", "fieldValue": 126},
        {"nodeId": "203", "fieldName": "value", "fieldValue": 126},
        {"nodeId": "230", "fieldName": "megapixels", "fieldValue": 2.692},
    ]
