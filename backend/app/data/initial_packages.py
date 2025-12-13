"""初始套餐配置数据"""

from app.models.membership_package import (
    MembershipPackage,
    ServicePrice,
    NewUserBonus,
    PackageCategory,
    RefundPolicy,
)


# 会员套餐配置
MEMBERSHIP_PACKAGES = [
    {
        "package_id": "membership_168",
        "name": "优惠 套餐",
        "category": PackageCategory.MEMBERSHIP.value,
        "description": "积分灵活使用",
        "price_yuan": 168,
        "bonus_credits": 30,
        "total_credits": 198,
        "refund_policy": RefundPolicy.REFUNDABLE.value,
        "refund_deduction_rate": 0.2,  # 退款扣除20%
        "privileges": [
            "提取约0.33一张图",
            "积分永不过期",
            "支持多台电脑登录同一账号",
            "畅享全站功能",
            "会员套餐可联系客服退款（赠送不退）",
        ],
        "sort_order": 1,
    },
    {
        "package_id": "membership_688",
        "name": "专业 套餐",
        "category": PackageCategory.MEMBERSHIP.value,
        "description": "积分灵活使用",
        "price_yuan": 688,
        "bonus_credits": 240,
        "total_credits": 928,
        "refund_policy": RefundPolicy.REFUNDABLE.value,
        "refund_deduction_rate": 0.2,
        "privileges": [
            "提取约0.29一张图",
            "畅享全站功能",
            "积分永不过期",
            "支持多台电脑登录同一账号",
            "会员套餐可联系客服退款（赠送不退）",
        ],
        "sort_order": 2,
    },
    {
        "package_id": "membership_1888",
        "name": "公司 套餐",
        "category": PackageCategory.MEMBERSHIP.value,
        "description": "积分灵活使用",
        "price_yuan": 1888,
        "bonus_credits": 1088,
        "total_credits": 2976,
        "refund_policy": RefundPolicy.REFUNDABLE.value,
        "refund_deduction_rate": 0.2,
        "privileges": [
            "提取约0.23一张图",
            "畅享全站功能",
            "积分永不过期",
            "支持多台电脑登录同一账号",
            "会员套餐可联系客服退款（赠送不退）",
        ],
        "popular": True,
        "recommended": True,
        "sort_order": 3,
    },
    {
        "package_id": "membership_5888",
        "name": "商业 套餐",
        "category": PackageCategory.MEMBERSHIP.value,
        "description": "积分灵活使用",
        "price_yuan": 5888,
        "bonus_credits": 6000,
        "total_credits": 11888,
        "refund_policy": RefundPolicy.REFUNDABLE.value,
        "refund_deduction_rate": 0.2,
        "privileges": [
            "提取约0.18一张图",
            "畅享全站功能",
            "积分永不过期",
            "支持多台电脑登录同一账号",
            "提供开具增值税发票",
            "会员套餐可联系客服退款（赠送不退）",
        ],
        "sort_order": 4,
    },
]

# 积分套餐配置
DISCOUNT_PACKAGES = [
    {
        "package_id": "discount_66",
        "name": "66元试用套餐",
        "category": PackageCategory.DISCOUNT.value,
        "description": "积分灵活使用",
        "price_yuan": 66,
        "bonus_credits": 6,
        "total_credits": 72,
        "refund_policy": RefundPolicy.NON_REFUNDABLE.value,
        "refund_deduction_rate": 0.0,
        "privileges": ["提取约0.38一张图", "积分永不过期", "优惠套餐不可退款"],
        "sort_order": 5,
    },
]

# 服务价格配置
SERVICE_PRICES = [
    {
        "service_id": "seamless",
        "service_name": "四方连续转换",
        "service_key": "seamless",
        "description": "AI四方连续转换",
        "price_credits": 1.2,
    },
    {
        "service_id": "prompt_edit",
        "service_name": "用嘴改图",
        "service_key": "prompt_edit",
        "description": "AI用嘴改图",
        "price_credits": 0.5,
    },
    {
        "service_id": "embroidery",
        "service_name": "刺绣",
        "service_key": "embroidery",
        "description": "AI刺绣",
        "price_credits": 0.7,
    },
    {
        "service_id": "flat_to_3d",
        "service_name": "平面转3D",
        "service_key": "flat_to_3d",
        "description": "AI平面转3D",
        "price_credits": 1.5,
    },
    {
        "service_id": "extract_pattern",
        "service_name": "提取花型",
        "service_key": "extract_pattern",
        "description": "AI提取花型",
        "price_credits": 1.5,
    },
    {
        "service_id": "extract_pattern_general_1",
        "service_name": "提取花型-通用模型",
        "service_key": "extract_pattern_general_1",
        "description": "AI提取花型（通用模型，多结果）",
        "price_credits": 1.5,
    },
    {
        "service_id": "extract_pattern_combined",
        "service_name": "提取花型-综合模型",
        "service_key": "extract_pattern_combined",
        "description": "AI提取花型（综合模型，并行多模型输出3图）",
        "price_credits": 1.5,
    },
    {
        "service_id": "extract_pattern_general_2",
        "service_name": "提取花型-通用2",
        "service_key": "extract_pattern_general_2",
        "description": "AI提取花型（通用2，首图高清）",
        "price_credits": 1.5,
    },
    {
        "service_id": "extract_pattern_positioning",
        "service_name": "提取花型-线条/矢量",
        "service_key": "extract_pattern_positioning",
        "description": "AI提取花型（线条/矢量）",
        "price_credits": 1.5,
    },
    {
        "service_id": "extract_pattern_fine",
        "service_name": "提取花型-烫画/胸前花",
        "service_key": "extract_pattern_fine",
        "description": "AI提取花型（烫画/胸前花，多图）",
        "price_credits": 1.5,
    },
    {
        "service_id": "watermark_removal",
        "service_name": "去水印",
        "service_key": "watermark_removal",
        "description": "AI去水印",
        "price_credits": 0.9,
    },
    {
        "service_id": "noise_removal",
        "service_name": "布纹降噪",
        "service_key": "noise_removal",
        "description": "AI布纹去噪",
        "price_credits": 0.5,
    },
    {
        "service_id": "style",
        "service_name": "转矢量",
        "service_key": "style",
        "description": "AI矢量化",
        "price_credits": 2.5,
    },
    {
        "service_id": "upscale",
        "service_name": "AI高清",
        "service_key": "upscale",
        "description": "AI高清",
        "price_credits": 0.9,
    },
    {
        "service_id": "upscale_meitu_v2",
        "service_name": "AI高清-美图v2",
        "service_key": "upscale_meitu_v2",
        "description": "AI高清（美图v2算法）",
        "price_credits": 0.9,
    },
    {
        "service_id": "upscale_runninghub_vr2",
        "service_name": "AI高清-通用2",
        "service_key": "upscale_runninghub_vr2",
        "description": "AI高清（通用2算法）",
        "price_credits": 0.9,
    },
    {
        "service_id": "expand_image",
        "service_name": "扩图",
        "service_key": "expand_image",
        "description": "AI扩图",
        "price_credits": 1.0,
    },
    {
        "service_id": "seamless_loop",
        "service_name": "接循环",
        "service_key": "seamless_loop",
        "description": "AI接循环",
        "price_credits": 1.0,
    },
]

# 新用户福利配置
NEW_USER_BONUS = {"bonus_credits": 10, "active": True}
# 新用户福利配置
NEW_USER_BONUS = {
    "bonus_credits": 10,
    "active": True
}


def get_all_packages():
    """获取所有套餐"""
    return MEMBERSHIP_PACKAGES + DISCOUNT_PACKAGES


def get_membership_packages():
    """获取会员套餐"""
    return MEMBERSHIP_PACKAGES


def get_discount_packages():
    """获取积分套餐"""
    return DISCOUNT_PACKAGES


def get_service_prices():
    """获取服务价格"""
    return SERVICE_PRICES


def get_new_user_bonus():
    """获取新用户福利"""
    return NEW_USER_BONUS
