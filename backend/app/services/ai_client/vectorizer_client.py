import logging
import os
import uuid
from io import BytesIO
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorizerClient:
    """Vectorizer.ai API客户端"""
    
    def __init__(self):
        self.vectorizer_api_key = settings.vectorizer_api_key
        self.vectorizer_api_secret = settings.vectorizer_api_secret
        self.vectorizer_url = "https://vectorizer.ai/api/v1/vectorize"
    
    async def vectorize_image(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI矢量化(转SVG) - 使用Vectorizer.ai API"""
        try:
            # 准备文件数据
            files = {
                'image': ('image.jpeg', BytesIO(image_bytes))
            }
            
            # 准备认证信息
            auth = (self.vectorizer_api_key, self.vectorizer_api_secret)
            
            # 准备请求数据
            data = {}
            
            # 如果提供了额外选项，添加到请求中
            if options:
                # Vectorizer.ai支持的各种选项
                if 'mode' in options:
                    data['mode'] = options['mode']
                if 'colors' in options:
                    data['colors'] = options['colors']
                if 'filter_speckle' in options:
                    data['filter_speckle'] = options['filter_speckle']
                if 'corners_threshold' in options:
                    data['corners_threshold'] = options['corners_threshold']
                if 'iterations' in options:
                    data['iterations'] = options['iterations']
                if 'layering' in options:
                    data['layering'] = options['layering']
                if 'pathsimplify' in options:
                    data['pathsimplify'] = options['pathsimplify']
            
            logger.info("Sending request to Vectorizer.ai API")
            
            # 发送请求
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    self.vectorizer_url,
                    files=files,
                    data=data,
                    auth=auth
                )
                response.raise_for_status()
                
                # 保存结果为SVG文件
                filename = f"vectorized_{uuid.uuid4().hex[:8]}.svg"
                file_path = f"{settings.upload_path}/results/{filename}"
                
                # 确保目录存在
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # 保存文件
                with open(file_path, "wb") as f:
                    f.write(response.content)
                
                # 返回文件URL格式，让处理服务可以访问
                return f"/files/results/{filename}"
            
        except Exception as e:
            logger.error(f"Vectorize image failed: {str(e)}")
            raise Exception(f"矢量化失败: {str(e)}")