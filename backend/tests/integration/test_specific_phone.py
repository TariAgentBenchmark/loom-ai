#!/usr/bin/env python3
"""
针对特定手机号15637899910的短信发送测试
用于调试短信收不到的问题
"""
import sys
import os
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User
from app.services.sms_service import SMSService
from app.services.aliyun_sms import AliyunSMSClient

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def check_user_in_db(phone: str):
    """检查用户是否在数据库中"""
    print(f"\n========== 检查用户 {phone} 是否存在 ==========")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone).first()
        if user:
            print(f"✅ 用户存在")
            print(f"  用户ID: {user.user_id}")
            print(f"  昵称: {user.nickname}")
            print(f"  手机验证状态: {user.is_phone_verified}")
            print(f"  上次发送短信时间: {user.last_sms_sent}")
            print(f"  今日发送次数: {user.sms_attempts_today}")
            print(f"  验证码: {user.phone_verification_code}")
            print(f"  验证码过期时间: {user.phone_verification_expires}")
            return user
        else:
            print(f"❌ 用户不存在")
            print(f"提示: 请先注册该手机号")
            return None
    finally:
        db.close()


def test_sms_configuration():
    """测试SMS配置"""
    print("\n========== SMS配置检查 ==========")
    
    issues = []
    
    if not settings.sms_access_key:
        issues.append("❌ ALIBABA_CLOUD_ACCESS_KEY_ID 未配置")
    else:
        print(f"✅ ALIBABA_CLOUD_ACCESS_KEY_ID: {settings.sms_access_key[:10]}...")
    
    if not settings.sms_access_key_secret:
        issues.append("❌ ALIBABA_CLOUD_ACCESS_KEY_SECRET 未配置")
    else:
        print(f"✅ ALIBABA_CLOUD_ACCESS_KEY_SECRET: {settings.sms_access_key_secret[:10]}...")
    
    if not settings.sms_sign_name:
        issues.append("❌ SMS_SIGN_NAME 未配置")
    else:
        print(f"✅ SMS_SIGN_NAME: {settings.sms_sign_name}")
    
    if not settings.sms_template_code:
        issues.append("❌ SMS_TEMPLATE_CODE 未配置")
    else:
        print(f"✅ SMS_TEMPLATE_CODE: {settings.sms_template_code}")
    
    print(f"✅ SMS_REGION: {settings.sms_region}")
    print(f"✅ SMS_CODE_VALID_MINUTES: {settings.sms_code_valid_minutes}")
    print(f"✅ SMS_MOCK_ENABLED: {settings.sms_mock_enabled}")
    
    if issues:
        print("\n配置问题:")
        for issue in issues:
            print(f"  {issue}")
        return False
    
    print("\n✅ SMS配置完整")
    return True


def test_send_sms_detailed(phone: str):
    """详细测试发送短信"""
    print(f"\n========== 详细测试发送短信到 {phone} ==========")
    
    # 检查配置
    if not test_sms_configuration():
        return False
    
    try:
        # 创建阿里云SMS客户端
        client = AliyunSMSClient(
            access_key_id=settings.sms_access_key,
            access_key_secret=settings.sms_access_key_secret,
            sign_name=settings.sms_sign_name,
            template_code=settings.sms_template_code,
            region_id=settings.sms_region,
        )
        
        # 生成测试验证码
        test_code = "888888"
        print(f"\n测试验证码: {test_code}")
        
        # 构建请求参数（用于调试显示）
        template_params = {
            "code": test_code,
            "min": settings.sms_code_valid_minutes,
        }
        request_preview = {
            "PhoneNumber": phone,
            "SignName": settings.sms_sign_name,
            "TemplateCode": settings.sms_template_code,
            "TemplateParam": template_params,
            "DuplicatePolicyMinutes": settings.sms_code_valid_minutes,
        }
        
        print("\n请求参数预览:")
        for key, value in request_preview.items():
            print(f"  {key}: {value}")
        
        # 调用阿里云SMS API
        print("\n发送短信...")
        success = client.send_sms(phone, template_params)
        
        if success:
            print(f"\n✅ 短信发送成功！")
            print(f"验证码: {test_code}")
            print(f"请检查手机 {phone} 是否收到短信")
            return True
        else:
            print(f"\n❌ 短信发送失败！")
            print("请查看上面的错误信息")
            return False
            
    except Exception as e:
        logger.exception("发送短信时出错")
        print(f"\n❌ 异常: {e}")
        return False


def test_api_endpoint_flow(phone: str):
    """测试完整的API流程"""
    print(f"\n========== 测试完整API流程 ==========")
    
    db = SessionLocal()
    try:
        # 1. 查找用户
        print(f"\n1. 查找用户 {phone}...")
        user = db.query(User).filter(User.phone == phone).first()
        
        if not user:
            print(f"❌ 用户不存在")
            print(f"提示: API会返回成功但不会真正发送短信（安全考虑）")
            return False
        
        print(f"✅ 用户存在: {user.user_id}")
        
        # 2. 检查发送频率限制
        print(f"\n2. 检查发送频率限制...")
        sms_service = SMSService()
        can_send, message = sms_service.can_send_sms(user)
        
        if not can_send:
            print(f"❌ 无法发送: {message}")
            return False
        
        print(f"✅ 可以发送")
        
        # 3. 创建验证码记录
        print(f"\n3. 创建验证码记录...")
        code = sms_service.create_verification_record(user, db)
        print(f"✅ 验证码已生成: {code}")
        print(f"   过期时间: {user.phone_verification_expires}")
        
        # 4. 发送短信
        print(f"\n4. 发送短信...")
        success = sms_service.send_verification_sms(phone, code)
        
        if success:
            print(f"✅ 短信发送成功！")
            print(f"\n验证码: {code}")
            print(f"手机号: {phone}")
            print(f"有效期: {settings.sms_code_valid_minutes}分钟")
            return True
        else:
            print(f"❌ 短信发送失败！")
            return False
            
    except Exception as e:
        logger.exception("API流程测试出错")
        print(f"\n❌ 异常: {e}")
        return False
    finally:
        db.close()


def main():
    """主函数"""
    phone = "15637899910"
    
    print("=" * 60)
    print("LoomAI 短信发送调试工具")
    print(f"测试手机号: {phone}")
    print("=" * 60)
    
    # 1. 检查用户是否存在
    user = check_user_in_db(phone)
    
    # 2. 测试配置
    config_ok = test_sms_configuration()
    
    if not config_ok:
        print("\n⚠️  配置不完整，请检查.env文件")
        return
    
    # 3. 如果用户存在，测试完整流程
    if user:
        print("\n选择测试方式:")
        print("1. 测试完整API流程（推荐）")
        print("2. 直接测试阿里云SMS API")
        
        # 自动选择方式1
        print("\n执行完整API流程测试...")
        test_api_endpoint_flow(phone)
    else:
        print("\n⚠️  用户不存在，跳过API流程测试")
        print("提示: 请先在前端注册该手机号，或者只测试阿里云SMS API")
        
        # 测试阿里云SMS
        test_send_sms_detailed(phone)
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
