"""
测试美图AI超清V2无损放大功能
"""
import asyncio
import os
import sys
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 设置日志级别为DEBUG以查看详细信息
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from app.services.ai_client import ai_client


async def test_upscale_v2():
    """测试AI超清V2功能"""
    
    # 测试图片URL（使用一个公开可访问的测试图片）
    # 注意：必须使用公开可访问的URL，美图API服务器需要能够下载这个图片
    test_image_url = "https://wheeai.meitudata.com/static/666162c4139073547bhMUcLeee3093.jpeg"
    
    print("=" * 50)
    print("测试美图AI超清V2无损放大")
    print("=" * 50)
    print(f"\n使用测试图片: {test_image_url}")
    print("注意：如果使用本地图片，需要配置OSS才能正常工作\n")
    
    # 测试2倍放大（高清模式）
    print("\n1. 测试2倍放大（高清模式）...")
    try:
        result_url = await ai_client.upscale_image(test_image_url, scale_factor=2)
        print(f"✓ 2倍放大成功！")
        print(f"  结果URL: {result_url}")
    except Exception as e:
        print(f"✗ 2倍放大失败: {str(e)}")
    
    # 测试4倍放大（超清模式）
    print("\n2. 测试4倍放大（超清模式）...")
    try:
        result_url = await ai_client.upscale_image(test_image_url, scale_factor=4)
        print(f"✓ 4倍放大成功！")
        print(f"  结果URL: {result_url}")
    except Exception as e:
        print(f"✗ 4倍放大失败: {str(e)}")
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_upscale_v2())
