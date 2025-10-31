import pytest
import asyncio
import os
import sys
from types import SimpleNamespace
from unittest.mock import patch, AsyncMock, MagicMock

mock_oss2_exceptions = SimpleNamespace(OssError=Exception)
mock_oss2 = SimpleNamespace(
    Auth=MagicMock(),
    Bucket=MagicMock(),
    exceptions=mock_oss2_exceptions,
)
sys.modules.setdefault("oss2", mock_oss2)
sys.modules.setdefault("oss2.exceptions", mock_oss2_exceptions)

import app.services.oss_service as oss_module
from app.services.ai_client import AIClient
from app.core.config import settings


class TestJimengAPI:
    """即梦API测试类"""
    
    @pytest.fixture
    def ai_client(self):
        """创建AI客户端实例"""
        original_key = settings.jimeng_api_key
        original_secret = settings.jimeng_api_secret
        settings.jimeng_api_key = "test_key"
        settings.jimeng_api_secret = "test_secret"

        try:
            yield AIClient()
        finally:
            settings.jimeng_api_key = original_key
            settings.jimeng_api_secret = original_secret
    
    @pytest.fixture
    def sample_image_bytes(self):
        """示例图片字节数据"""
        # 返回一个简单的PNG图片数据
        return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
    
    @pytest.mark.asyncio
    async def test_make_jimeng_request(self, ai_client):
        """测试即梦API请求方法"""
        # 模拟即梦API响应
        mock_response_data = {
            "code": 10000,
            "data": {
                "task_id": "test_task_id_123"
            },
            "message": "Success"
        }
        
        with patch('httpx.AsyncClient.request', new_callable=AsyncMock) as mock_request:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json = MagicMock(return_value=mock_response_data)
            mock_request.return_value = mock_response
            
            # 测试数据
            test_data = {
                "Action": "CVSync2AsyncSubmitTask",
                "Version": "2022-08-31",
                "req_key": "jimeng_t2i_v40",
                "prompt": "测试毛线刺绣增强",
                "image_urls": ["https://example.com/test.jpg"]
            }
            
            # 调用方法
            result = await ai_client.jimeng_client._make_jimeng_request("POST", "", test_data)
            
            # 验证结果
            assert result == mock_response_data
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_query_jimeng_task_status(self, ai_client):
        """测试查询即梦任务状态"""
        # 模拟任务状态响应
        mock_response = {
            "code": 10000,
            "data": {
                "status": "done",
                "image_urls": ["https://example.com/result.jpg"]
            },
            "message": "Success"
        }
        
        with patch.object(ai_client.jimeng_client, '_make_jimeng_request') as mock_request:
            mock_request.return_value = mock_response
            
            # 调用方法
            result = await ai_client.jimeng_client.query_task_status("test_task_id")
            
            # 验证结果
            assert result == mock_response
            mock_request.assert_called_once_with(
                "POST", "", {
                    "Action": "CVSync2AsyncGetResult",
                    "Version": "2022-08-31",
                    "req_key": "jimeng_t2i_v40",
                    "task_id": "test_task_id"
                }
            )
    
    @pytest.mark.asyncio
    async def test_enhance_embroidery_with_jimeng(self, ai_client, sample_image_bytes):
        """测试使用即梦API进行毛线刺绣增强"""
        # 模拟任务提交响应
        submit_response = {
            "code": 10000,
            "data": {
                "task_id": "jimeng_task_123"
            },
            "message": "Success"
        }
        
        # 模拟任务完成响应
        complete_response = {
            "code": 10000,
            "data": {
                "status": "done",
                "image_urls": ["https://example.com/embroidery_result.jpg"]
            },
            "message": "Success"
        }
        
        # 模拟图片下载
        mock_image_data = b"mock_image_data"
        
        with patch.object(ai_client.jimeng_client, '_make_jimeng_request') as mock_request, \
             patch.object(ai_client.jimeng_client, 'query_task_status') as mock_query, \
             patch.object(ai_client.gemini_client, '_download_image_from_url') as mock_download, \
             patch.object(oss_module, 'oss_service') as mock_oss_service, \
             patch.object(ai_client.base_client_utils, '_save_image_bytes') as mock_save:
            
            # 设置模拟返回值
            mock_request.return_value = submit_response
            mock_query.return_value = complete_response
            mock_download.return_value = mock_image_data
            mock_oss_service.is_configured.return_value = True
            mock_oss_service.upload_image_for_jimeng = AsyncMock(return_value="https://example.com/uploaded.jpg")
            mock_save.return_value = "/files/results/embroidery_test12345.png"
            
            # 调用方法
            result = await ai_client.enhance_embroidery(sample_image_bytes)
            
            # 验证结果
            assert result == "/files/results/embroidery_test12345.png"
            mock_request.assert_called_once()
            mock_query.assert_called_once_with("jimeng_task_123")
            mock_download.assert_called_once_with("https://example.com/embroidery_result.jpg")
            mock_oss_service.upload_image_for_jimeng.assert_called_once()
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_flat_to_3d_with_jimeng(self, ai_client, sample_image_bytes):
        """测试使用即梦API进行平面转3D"""
        submit_response = {
            "code": 10000,
            "data": {
                "task_id": "jimeng_task_flat3d"
            },
            "message": "Success"
        }

        complete_response = {
            "code": 10000,
            "data": {
                "status": "done",
                "image_urls": ["https://example.com/flat3d_result.jpg"]
            },
            "message": "Success"
        }

        mock_image_data = b"mock_flat3d_image"

        with patch.object(ai_client.jimeng_client, '_make_jimeng_request') as mock_request, \
             patch.object(ai_client.jimeng_client, 'query_task_status') as mock_query, \
             patch.object(ai_client.gemini_client, '_download_image_from_url') as mock_download, \
             patch.object(oss_module, 'oss_service') as mock_oss_service, \
             patch.object(ai_client.base_client_utils, '_save_image_bytes') as mock_save:

            mock_request.return_value = submit_response
            mock_query.return_value = complete_response
            mock_download.return_value = mock_image_data
            mock_oss_service.is_configured.return_value = True
            mock_oss_service.upload_image_for_jimeng = AsyncMock(return_value="https://example.com/uploaded_flat3d.jpg")
            mock_save.return_value = "/files/results/flat3d_test12345.png"

            result = await ai_client.convert_flat_to_3d(sample_image_bytes)

            assert result == "/files/results/flat3d_test12345.png"
            mock_request.assert_called_once()
            mock_query.assert_called_once_with("jimeng_task_flat3d")
            mock_download.assert_called_once_with("https://example.com/flat3d_result.jpg")
            mock_oss_service.upload_image_for_jimeng.assert_called_once()
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_image_from_url(self, ai_client):
        """测试从URL下载图片"""
        mock_image_data = b"test_image_data"
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.content = mock_image_data
            mock_get.return_value = mock_response
            
            # 调用方法
            result = await ai_client._download_image_from_url("https://example.com/test.jpg")
            
            # 验证结果
            assert result == mock_image_data
            mock_get.assert_called_once_with("https://example.com/test.jpg")
    
    @pytest.mark.asyncio
    async def test_jimeng_api_error_handling(self, ai_client):
        """测试即梦API错误处理"""
        # 模拟API错误响应
        error_response = {
            "code": 50411,
            "message": "Pre Img Risk Not Pass"
        }
        
        with patch.object(ai_client.jimeng_client, '_make_jimeng_request') as mock_request, \
             patch.object(oss_module, 'oss_service') as mock_oss_service:
            mock_request.return_value = error_response
            mock_oss_service.is_configured.return_value = True
            mock_oss_service.upload_image_for_jimeng = AsyncMock(return_value="https://example.com/uploaded.jpg")
            
            # 调用方法并验证异常
            with pytest.raises(Exception) as exc_info:
                await ai_client.enhance_embroidery(b"test_image_data")
            
            assert "毛线刺绣增强失败" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_jimeng_task_timeout(self, ai_client, sample_image_bytes):
        """测试即梦任务超时处理"""
        # 模拟任务提交响应
        submit_response = {
            "code": 10000,
            "data": {
                "task_id": "timeout_task_123"
            },
            "message": "Success"
        }
        
        # 模拟任务处理中响应
        processing_response = {
            "code": 10000,
            "data": {
                "status": "generating"
            },
            "message": "Success"
        }
        
        with patch.object(ai_client.jimeng_client, '_make_jimeng_request') as mock_request, \
             patch.object(ai_client.jimeng_client, 'query_task_status') as mock_query, \
             patch.object(oss_module, 'oss_service') as mock_oss_service, \
             patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            
            # 设置模拟返回值
            mock_request.return_value = submit_response
            mock_query.return_value = processing_response
            mock_oss_service.is_configured.return_value = True
            mock_oss_service.upload_image_for_jimeng = AsyncMock(return_value="https://example.com/uploaded.jpg")
            
            # 调用方法并验证超时异常
            with pytest.raises(Exception) as exc_info:
                await ai_client.enhance_embroidery(sample_image_bytes)
            
            assert "任务超时" in str(exc_info.value)
            # 验证轮询次数
            assert mock_query.call_count == 40  # 最大轮询次数


if __name__ == "__main__":
    pytest.main([__file__])
