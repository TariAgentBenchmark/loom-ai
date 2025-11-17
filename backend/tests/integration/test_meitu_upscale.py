#!/usr/bin/env python3
"""
测试美图API高清放大功能
"""
import asyncio
import io
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.services.ai_client import AIClient
from app.core.config import settings
from app.services.file_service import save_uploaded_file


async def test_meitu_upscale():
    """测试美图API高清放大功能"""
    print("开始测试美图API高清放大功能...")
    
    # 检查环境变量是否设置
    if not settings.meitu_api_key or not settings.meitu_api_secret:
        print("错误: 请设置美图API的环境变量 MEITU_API_KEY 和 MEITU_API_SECRET")
        return False
    
    # 创建AI客户端
    ai_client = AIClient()
    
    # 创建一个简单的测试图片
    from PIL import Image
    test_image = Image.new('RGB', (200, 200), color='blue')
    
    # 保存图片并获取URL
    img_bytes = io.BytesIO()
    test_image.save(img_bytes, format='JPEG')
    image_bytes = img_bytes.getvalue()
    
    try:
        # 保存测试图片
        filename = "test_upscale_input.jpg"
        file_path = await save_uploaded_file(image_bytes, filename)
        image_url = f"/files/originals/{filename}"
        
        print(f"测试图片已保存: {image_url}")
        
        # 测试2倍放大
        print("测试2倍放大...")
        result_url = await ai_client.upscale_image(image_url, scale_factor=2)
        print(f"2倍放大成功! 结果URL: {result_url}")
        
        # 测试4倍放大
        print("测试4倍放大...")
        result_url = await ai_client.upscale_image(image_url, scale_factor=4)
        print(f"4倍放大成功! 结果URL: {result_url}")
        
        # 测试自定义尺寸放大
        print("测试自定义尺寸放大(400x400)...")
        result_url = await ai_client.upscale_image(image_url, custom_width=400, custom_height=400)
        print(f"自定义尺寸放大成功! 结果URL: {result_url}")
        
        return True
        
    except Exception as e:
        print(f"AI高清放大测试失败: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_meitu_upscale())
    if success:
        print("测试通过!")
    else:
        print("测试失败!")
        sys.exit(1)
