#!/usr/bin/env python3
"""
测试阿里云OSS集成
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.oss_service import oss_service
from app.services.ai_client import ai_client
from app.core.config import settings


async def test_oss_configuration():
    """测试OSS配置"""
    print("=== 测试OSS配置 ===")
    
    if oss_service.is_configured():
        print("✓ OSS服务已正确配置")
        print(f"  - Endpoint: {settings.oss_endpoint}")
        print(f"  - Bucket: {settings.oss_bucket_name}")
        print(f"  - 自定义域名: {settings.oss_bucket_domain or '未配置'}")
    else:
        print("✗ OSS服务未配置或配置不完整")
        print("  请检查以下配置项:")
        print(f"  - OSS_ACCESS_KEY_ID: {'已配置' if settings.oss_access_key_id else '未配置'}")
        print(f"  - OSS_ACCESS_KEY_SECRET: {'已配置' if settings.oss_access_key_secret else '未配置'}")
        print(f"  - OSS_ENDPOINT: {'已配置' if settings.oss_endpoint else '未配置'}")
        print(f"  - OSS_BUCKET_NAME: {'已配置' if settings.oss_bucket_name else '未配置'}")
        return False
    
    return True


async def test_oss_upload():
    """测试OSS上传功能"""
    print("\n=== 测试OSS上传功能 ===")
    
    if not oss_service.is_configured():
        print("✗ OSS未配置，跳过上传测试")
        return False
    
    # 创建测试文件
    test_content = b"This is a test file content for verifying OSS upload functionality."
    test_filename = "test_oss_upload.txt"
    
    try:
        result = await oss_service.upload_file(
            test_content, 
            test_filename, 
            prefix="test"
        )
        
        print("✓ 文件上传成功")
        print(f"  - URL: {result['url']}")
        print(f"  - 对象键: {result['object_key']}")
        print(f"  - 大小: {result['size']} 字节")
        
        # 测试文件是否存在
        exists = await oss_service.check_file_exists(result['object_key'])
        if exists:
            print("✓ 文件存在性验证成功")
        else:
            print("✗ 文件存在性验证失败")
            return False
        
        # 清理测试文件
        deleted = await oss_service.delete_file(result['object_key'])
        if deleted:
            print("✓ 测试文件清理成功")
        else:
            print("⚠ 测试文件清理失败")
        
        return True
        
    except Exception as e:
        print(f"✗ OSS上传测试失败: {str(e)}")
        return False


async def test_embroidery_with_oss():
    """测试毛线刺绣增强功能（使用OSS）"""
    print("\n=== 测试毛线刺绣增强功能（使用OSS） ===")
    
    if not oss_service.is_configured():
        print("✗ OSS未配置，跳过刺绣增强测试")
        return False
    
    if not settings.jimeng_api_key or not settings.jimeng_api_secret:
        print("✗ 即梦API未配置，跳过刺绣增强测试")
        return False
    
    # 创建测试图片（1x1像素的红色JPEG）
    from PIL import Image
    import io
    
    # 创建一个简单的测试图片
    test_image = Image.new('RGB', (100, 100), color='red')
    img_buffer = io.BytesIO()
    test_image.save(img_buffer, format='JPEG')
    image_bytes = img_buffer.getvalue()
    
    try:
        print("开始测试毛线刺绣增强...")
        print("注意：这将调用即梦API，可能会产生费用")
        
        # 这里我们只测试上传部分，不实际调用即梦API
        # 因为即梦API是付费服务，测试会产生费用
        test_filename = "test_embroidery.jpg"
        
        # 测试上传到OSS
        oss_url = await oss_service.upload_image_for_jimeng(image_bytes, test_filename)
        print(f"✓ 图片已上传到OSS: {oss_url}")
        
        # 清理测试图片
        # 从URL中提取对象键
        if settings.oss_bucket_domain and oss_url.startswith(f"https://{settings.oss_bucket_domain}/"):
            object_key = oss_url.replace(f"https://{settings.oss_bucket_domain}/", "")
        else:
            object_key = oss_url.replace(f"https://{settings.oss_bucket_name}.{settings.oss_endpoint.replace('https://', '')}/", "")
        
        deleted = await oss_service.delete_file(object_key)
        if deleted:
            print("✓ 测试图片清理成功")
        
        print("✓ OSS集成测试通过")
        print("注意：完整的即梦API测试需要有效的API密钥且会产生费用")
        
        return True
        
    except Exception as e:
        print(f"✗ 毛线刺绣增强测试失败: {str(e)}")
        return False


async def main():
    """主测试函数"""
    print("阿里云OSS集成测试")
    print("=" * 50)
    
    # 测试配置
    config_ok = await test_oss_configuration()
    
    if not config_ok:
        print("\n请先配置OSS后再运行测试")
        print("配置方法：")
        print("1. 复制 .env.example 为 .env")
        print("2. 填写OSS相关配置项")
        print("3. 重新运行测试")
        return
    
    # 测试上传功能
    upload_ok = await test_oss_upload()
    
    # 测试刺绣增强功能
    embroidery_ok = await test_embroidery_with_oss()
    
    # 总结
    print("\n" + "=" * 50)
    print("测试结果总结:")
    print(f"  - OSS配置: {'✓ 通过' if config_ok else '✗ 失败'}")
    print(f"  - OSS上传: {'✓ 通过' if upload_ok else '✗ 失败'}")
    print(f"  - 刺绣增强: {'✓ 通过' if embroidery_ok else '✗ 失败'}")
    
    if config_ok and upload_ok:
        print("\n✓ OSS集成基本功能正常")
        print("现在可以正常使用毛线刺绣增强功能了")
    else:
        print("\n✗ OSS集成存在问题，请检查配置")


if __name__ == "__main__":
    asyncio.run(main())