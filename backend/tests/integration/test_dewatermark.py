import asyncio
import os
import sys
import base64
from io import BytesIO
from PIL import Image

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_client import ai_client
from app.core.config import settings

async def test_dewatermark_api():
    """测试Dewatermark.ai API集成"""
    
    # 检查API密钥是否配置
    if not settings.dewatermark_api_key:
        print("错误: DEWATERMARK_API_KEY 未配置")
        return False
    
    # 创建一个测试图片
    test_image = Image.new('RGB', (500, 500), color='white')
    test_bytes = BytesIO()
    test_image.save(test_bytes, format='JPEG')
    test_bytes.seek(0)
    
    try:
        print("开始测试Dewatermark.ai API...")
        result_url = await ai_client.remove_watermark(test_bytes.read())
        print(f"测试成功! 处理后的图片URL: {result_url}")
        return True
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    # 设置测试环境变量
    os.environ.setdefault("DEWATERMARK_API_KEY", "YOUR_API_KEY_HERE")
    
    # 运行测试
    success = asyncio.run(test_dewatermark_api())
    if success:
        print("Dewatermark.ai API集成测试通过!")
    else:
        print("Dewatermark.ai API集成测试失败!")