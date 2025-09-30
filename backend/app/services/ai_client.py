import httpx
import base64
import json
import logging
from typing import Dict, Any, Optional
from io import BytesIO
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIClient:
    """AI服务客户端"""
    
    def __init__(self):
        self.base_url = settings.tuzi_base_url
        self.api_key = settings.tuzi_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """发送API请求"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"AI API request failed: {e.response.status_code} - {e.response.text}")
            raise Exception(f"AI服务请求失败: {e.response.status_code}")
        except Exception as e:
            logger.error(f"AI API request error: {str(e)}")
            raise Exception(f"AI服务连接失败: {str(e)}")

    def _image_to_base64(self, image_bytes: bytes, format: str = "JPEG") -> str:
        """将图片字节转换为base64编码"""
        try:
            # 使用PIL处理图片
            image = Image.open(BytesIO(image_bytes))
            
            # 如果是RGBA模式且要转换为JPEG，需要转换为RGB
            if image.mode == "RGBA" and format.upper() == "JPEG":
                # 创建白色背景
                background = Image.new("RGB", image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])  # 使用alpha通道作为mask
                image = background
            
            # 转换为字节
            buffer = BytesIO()
            image.save(buffer, format=format, quality=95)
            image_bytes = buffer.getvalue()
            
            # 编码为base64
            return base64.b64encode(image_bytes).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Image to base64 conversion failed: {str(e)}")
            raise Exception(f"图片格式转换失败: {str(e)}")

    async def generate_image_gpt4o(self, prompt: str, size: str = "1024x1024") -> Dict[str, Any]:
        """使用GPT-4o生成图片"""
        endpoint = "/v1/images/generations"
        data = {
            "model": "gpt-4o-image-vip",
            "prompt": prompt,
            "n": 1,
            "size": size
        }
        
        logger.info(f"Generating image with GPT-4o: {prompt[:100]}...")
        return await self._make_request("POST", endpoint, data)

    async def process_image_gemini(self, image_bytes: bytes, prompt: str, mime_type: str = "image/jpeg") -> Dict[str, Any]:
        """使用Gemini-2.5-flash-image处理图片"""
        endpoint = "/v1beta/models/gemini-2.5-flash-image:generateContent"
        
        # 转换图片为base64
        image_base64 = self._image_to_base64(image_bytes, 
                                           "PNG" if mime_type == "image/png" else "JPEG")
        
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        },
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_base64
                            }
                        }
                    ]
                }
            ]
        }
        
        logger.info(f"Processing image with Gemini: {prompt[:100]}...")
        return await self._make_request("POST", endpoint, data)

    async def seamless_pattern_conversion(self, image_bytes: bytes, options: Dict[str, Any]) -> str:
        """AI四方连续转换"""
        prompt = f"""
        将这张图片转换为可以四方连续拼接的图案。要求：
        1. 确保图案边缘可以无缝连接
        2. 保持原有图案的主要特征和风格
        3. {'去除背景元素' if options.get('removeBackground', True) else '保留背景'}
        4. {'确保完美的循环拼接效果' if options.get('seamlessLoop', True) else ''}
        5. 输出为PNG格式，保持透明背景
        
        请生成一个可以四方连续拼接的图案版本。
        """
        
        result = await self.process_image_gemini(image_bytes, prompt, "image/png")
        return self._extract_image_url(result)

    async def vectorize_image(self, image_bytes: bytes, options: Dict[str, Any]) -> str:
        """AI矢量化(转SVG)"""
        output_style = options.get('outputStyle', 'vector')
        output_ratio = options.get('outputRatio', '1:1')
        
        prompt = f"""
        将这张图片转换为矢量风格的图案：
        1. 输出风格：{'矢量风格，线条清晰简洁' if output_style == 'vector' else '无缝循环风格'}
        2. 输出比例：{output_ratio}
        3. 保持图片的主要特征和识别度
        4. 线条要清晰，颜色要准确
        5. 适合用于产品设计和印刷
        
        请生成高质量的矢量风格图案。
        """
        
        result = await self.process_image_gemini(image_bytes, prompt, "image/png")
        return self._extract_image_url(result)

    async def extract_and_edit(self, image_bytes: bytes, options: Dict[str, Any]) -> str:
        """AI提取编辑"""
        edit_mode = options.get('editMode', 'smart')
        instructions = options.get('instructions', '')
        
        prompt = f"""
        对这张图片进行智能编辑处理：
        1. 编辑模式：{'智能自动编辑' if edit_mode == 'smart' else '精确手动编辑'}
        2. 具体指令：{instructions if instructions else '优化图片质量和视觉效果'}
        3. 保持图片的主要内容和结构
        4. 提升图片的整体质量和美观度
        5. 确保编辑结果自然真实
        
        请按照要求对图片进行编辑处理。
        """
        
        result = await self.process_image_gemini(image_bytes, prompt, "image/jpeg")
        return self._extract_image_url(result)

    async def extract_pattern(self, image_bytes: bytes, options: Dict[str, Any]) -> str:
        """AI提取花型"""
        pattern_type = options.get('patternType', 'floral')
        preprocessing = options.get('preprocessing', True)
        
        pattern_descriptions = {
            'floral': '花卉图案，包括花朵、叶子等植物元素',
            'geometric': '几何图案，包括线条、形状等几何元素', 
            'abstract': '抽象图案，包括艺术化的抽象元素'
        }
        
        prompt = f"""
        从这张图片中提取{pattern_descriptions.get(pattern_type, '图案')}：
        1. {'先进行图片预处理，提升清晰度' if preprocessing else '直接处理原图'}
        2. 专注提取{pattern_type}类型的图案元素
        3. 去除背景和无关元素
        4. 保持图案的完整性和细节
        5. 输出清晰的图案，适合设计应用
        
        请提取出清晰的{pattern_type}图案。
        """
        
        result = await self.process_image_gemini(image_bytes, prompt, "image/png")
        return self._extract_image_url(result)

    async def remove_watermark(self, image_bytes: bytes, options: Dict[str, Any]) -> str:
        """AI智能去水印"""
        watermark_type = options.get('watermarkType', 'auto')
        preserve_detail = options.get('preserveDetail', True)
        
        watermark_descriptions = {
            'auto': '自动识别并去除所有类型的水印',
            'text': '重点去除文字水印',
            'logo': '重点去除Logo水印',
            'transparent': '去除半透明水印'
        }
        
        prompt = f"""
        去除这张图片中的水印：
        1. 水印类型：{watermark_descriptions.get(watermark_type, '自动识别')}
        2. {'保留图片的原有细节和质量' if preserve_detail else '优先去除水印，可适当牺牲细节'}
        3. 确保去除水印后图片看起来自然
        4. 不要留下水印的痕迹或空白区域
        5. 保持图片的整体美观
        
        请彻底去除水印并修复图片。
        """
        
        result = await self.process_image_gemini(image_bytes, prompt, "image/jpeg")
        return self._extract_image_url(result)

    async def denoise_image(self, image_bytes: bytes, options: Dict[str, Any]) -> str:
        """AI布纹去噪"""
        noise_type = options.get('noiseType', 'fabric')
        enhance_mode = options.get('enhanceMode', 'standard')
        
        noise_descriptions = {
            'fabric': '布纹纹理',
            'noise': '图片噪点',
            'blur': '模糊效果'
        }
        
        prompt = f"""
        去除这张图片中的{noise_descriptions.get(noise_type, '噪音')}：
        1. 重点处理：{noise_type}类型的问题
        2. 处理模式：{'标准去噪处理' if enhance_mode == 'standard' else '矢量重绘模式，重新绘制清晰版本'}
        3. 保持图片的主要内容和结构
        4. 提升图片的清晰度和质量
        5. 确保处理后的图片自然美观
        
        请生成清晰、高质量的图片。
        """
        
        result = await self.process_image_gemini(image_bytes, prompt, "image/png")
        return self._extract_image_url(result)

    async def enhance_embroidery(self, image_bytes: bytes, options: Dict[str, Any]) -> str:
        """AI毛线刺绣增强"""
        needle_type = options.get('needleType', 'medium')
        stitch_density = options.get('stitchDensity', 'medium')
        enhance_details = options.get('enhanceDetails', True)
        
        needle_descriptions = {
            'fine': '细针，精细的针脚效果',
            'medium': '中等针脚，平衡的刺绣效果',
            'thick': '粗针，明显的针脚纹理'
        }
        
        density_descriptions = {
            'low': '稀疏的针脚密度',
            'medium': '适中的针脚密度',
            'high': '密集的针脚密度'
        }
        
        prompt = f"""
        将这张图片转换为毛线刺绣效果：
        1. 针线类型：{needle_descriptions.get(needle_type, '中等针脚')}
        2. 针脚密度：{density_descriptions.get(stitch_density, '适中密度')}
        3. {'增强纹理细节，展现真实的毛线质感' if enhance_details else '保持简洁的刺绣风格'}
        4. 保持原图的主体形状和轮廓
        5. 营造真实的手工刺绣效果
        6. 色彩要自然，符合毛线刺绣的特点
        
        请生成逼真的毛线刺绣效果图。
        """
        
        result = await self.process_image_gemini(image_bytes, prompt, "image/png")
        return self._extract_image_url(result)

    def _extract_image_url(self, api_response: Dict[str, Any]) -> str:
        """从API响应中提取图片URL"""
        try:
            # GPT-4o响应格式
            if "data" in api_response and isinstance(api_response["data"], list):
                return api_response["data"][0]["url"]
            
            # Gemini响应格式 (需要根据实际响应调整)
            if "candidates" in api_response:
                # 这里需要根据Gemini的实际响应格式调整
                # 假设响应中包含生成的图片URL或base64数据
                candidate = api_response["candidates"][0]
                if "content" in candidate:
                    # 处理Gemini的响应格式
                    return self._process_gemini_response(candidate["content"])
            
            # 如果是base64格式，需要保存为文件并返回URL
            if "image" in api_response:
                return self._save_base64_image(api_response["image"])
                
            raise Exception("无法从AI响应中提取图片")
            
        except Exception as e:
            logger.error(f"Failed to extract image URL: {str(e)}")
            raise Exception(f"处理AI响应失败: {str(e)}")

    def _process_gemini_response(self, content: Dict[str, Any]) -> str:
        """处理Gemini响应内容"""
        # 这里需要根据Gemini的实际响应格式实现
        # 暂时返回占位符，实际使用时需要调整
        logger.warning("Gemini response processing not fully implemented")
        return "https://cdn.loom-ai.com/temp/gemini_result.png"

    def _save_base64_image(self, base64_data: str) -> str:
        """保存base64图片并返回URL"""
        try:
            # 解码base64数据
            image_data = base64.b64decode(base64_data)
            
            # 生成文件名
            import uuid
            filename = f"ai_result_{uuid.uuid4().hex[:8]}.png"
            file_path = f"{settings.upload_path}/results/{filename}"
            
            # 确保目录存在
            import os
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 保存文件
            with open(file_path, "wb") as f:
                f.write(image_data)
            
            # 返回访问URL
            return f"/files/results/{filename}"
            
        except Exception as e:
            logger.error(f"Failed to save base64 image: {str(e)}")
            raise Exception(f"保存图片失败: {str(e)}")


# 创建全局AI客户端实例
ai_client = AIClient()
