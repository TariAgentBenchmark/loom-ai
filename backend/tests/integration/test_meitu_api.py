#!/usr/bin/env python3
"""
测试美图API集成
"""
import asyncio
import base64
import io
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.services.ai_client import AIClient
from app.core.config import settings


async def test_meitu_api():
    """测试美图API去水印功能"""
    print("开始测试美图API去水印功能...")
    
    # 检查环境变量是否设置
    if not settings.meitu_api_key or not settings.meitu_api_secret:
        print("错误: 请设置美图API的环境变量 MEITU_API_KEY 和 MEITU_API_SECRET")
        return False
    
    # 创建AI客户端
    ai_client = AIClient()
    
    # 创建一个简单的测试图片（1x1像素的红色图片）
    from PIL import Image
    test_image = Image.new('RGB', (100, 100), color='red')
    
    # 在图片上添加一些文本作为"水印"
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(test_image)
    try:
        # 尝试使用默认字体
        font = ImageFont.load_default()
    except:
        font = None
    
    # 添加文本水印
    draw.text((10, 10), "WATERMARK", fill='white', font=font)
    
    # 将图片转换为字节
    img_bytes = io.BytesIO()
    test_image.save(img_bytes, format='JPEG')
    image_bytes = img_bytes.getvalue()
    
    try:
        print("发送去水印请求...")
        result_url = await ai_client.remove_watermark(image_bytes)
        print(f"去水印成功! 结果URL: {result_url}")
        return True
    except Exception as e:
        print(f"去水印失败: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_meitu_api())
    if success:
        print("测试通过!")
    else:
        print("测试失败!")
        sys.exit(1)