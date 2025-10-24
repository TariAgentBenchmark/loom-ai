"""初始套餐配置数据"""

from app.models.membership_package import MembershipPackage, ServicePrice, NewUserBonus, PackageCategory, RefundPolicy


# 会员套餐配置
MEMBERSHIP_PACKAGES = [
    # 会员套餐（可退款）
    {
        "package_id": "membership_3000",
        "name": "3000元会员套餐",
        "category": PackageCategory.MEMBERSHIP.value,
        "description": "高性价比会员套餐，适合长期使用",
        "price_yuan": 3000,
        "bonus_credits": 400,
        "total_credits": 3400,
        "refund_policy": RefundPolicy.REFUNDABLE.value,
        "refund_deduction_rate": 0.2,  # 退款扣除20%
        "privileges": [
            "购买全站功能",
            "积分永不过期",
            "可退款（需扣除充值原金额的20%，赠送积分不参与退款）"
        ],
        "sort_order": 1
    },
    {
        "package_id": "membership_6000",
        "name": "6000元会员套餐",
        "category": PackageCategory.MEMBERSHIP.value,
        "description": "专业级会员套餐，更多积分赠送",
        "price_yuan": 6000,
        "bonus_credits": 900,
        "total_credits": 6900,
        "refund_policy": RefundPolicy.REFUNDABLE.value,
        "refund_deduction_rate": 0.2,
        "privileges": [
            "购买全站功能",
            "积分永不过期",
            "可退款（需扣除充值原金额的20%，赠送积分不参与退款）"
        ],
        "sort_order": 2
    },
    {
        "package_id": "membership_10000",
        "name": "10000元会员套餐",
        "category": PackageCategory.MEMBERSHIP.value,
        "description": "企业级会员套餐，超高性价比",
        "price_yuan": 10000,
        "bonus_credits": 2000,
        "total_credits": 12000,
        "refund_policy": RefundPolicy.REFUNDABLE.value,
        "refund_deduction_rate": 0.2,
        "privileges": [
            "购买全站功能",
            "积分永不过期",
            "可退款（需扣除充值原金额的20%，赠送积分不参与退款）"
        ],
        "popular": True,
        "recommended": True,
        "sort_order": 3
    },
    {
        "package_id": "membership_15000",
        "name": "15000元会员套餐",
        "category": PackageCategory.MEMBERSHIP.value,
        "description": "至尊会员套餐，最大积分赠送",
        "price_yuan": 15000,
        "bonus_credits": 3000,
        "total_credits": 18000,
        "refund_policy": RefundPolicy.REFUNDABLE.value,
        "refund_deduction_rate": 0.2,
        "privileges": [
            "购买全站功能",
            "积分永不过期",
            "可退款（需扣除充值原金额的20%，赠送积分不参与退款）"
        ],
        "sort_order": 4
    },
]

# 优惠套餐配置
DISCOUNT_PACKAGES = [
    # 优惠套餐（不可退款）
    {
        "package_id": "discount_30",
        "name": "30元优惠套餐",
        "category": PackageCategory.DISCOUNT.value,
        "description": "入门级优惠套餐",
        "price_yuan": 30,
        "bonus_credits": 0,
        "total_credits": 30,
        "refund_policy": RefundPolicy.NON_REFUNDABLE.value,
        "refund_deduction_rate": 0.0,
        "privileges": [
            "购买全站功能",
            "积分永不过期",
            "不可退款"
        ],
        "sort_order": 5
    },
    {
        "package_id": "discount_100",
        "name": "100元优惠套餐",
        "category": PackageCategory.DISCOUNT.value,
        "description": "标准优惠套餐",
        "price_yuan": 100,
        "bonus_credits": 10,
        "total_credits": 110,
        "refund_policy": RefundPolicy.NON_REFUNDABLE.value,
        "refund_deduction_rate": 0.0,
        "privileges": [
            "购买全站功能",
            "积分永不过期",
            "不可退款"
        ],
        "sort_order": 6
    },
    {
        "package_id": "discount_300",
        "name": "300元优惠套餐",
        "category": PackageCategory.DISCOUNT.value,
        "description": "高级优惠套餐",
        "price_yuan": 300,
        "bonus_credits": 30,
        "total_credits": 330,
        "refund_policy": RefundPolicy.NON_REFUNDABLE.value,
        "refund_deduction_rate": 0.0,
        "privileges": [
            "购买全站功能",
            "积分永不过期",
            "不可退款"
        ],
        "popular": True,
        "sort_order": 7
    },
    {
        "package_id": "discount_500",
        "name": "500元优惠套餐",
        "category": PackageCategory.DISCOUNT.value,
        "description": "专业优惠套餐",
        "price_yuan": 500,
        "bonus_credits": 50,
        "total_credits": 550,
        "refund_policy": RefundPolicy.NON_REFUNDABLE.value,
        "refund_deduction_rate": 0.0,
        "privileges": [
            "购买全站功能",
            "积分永不过期",
            "不可退款"
        ],
        "sort_order": 8
    },
]

# 服务价格配置
SERVICE_PRICES = [
    {
        "service_id": "prompt_edit",
        "service_name": "用嘴改图",
        "service_key": "prompt_edit",
        "description": "AI用嘴改图",
        "price_credits": 0.5
    },
    {
        "service_id": "embroidery",
        "service_name": "刺绣",
        "service_key": "embroidery",
        "description": "AI刺绣",
        "price_credits": 0.7
    },
    {
        "service_id": "extract_pattern",
        "service_name": "提取花型",
        "service_key": "extract_pattern",
        "description": "AI提取花型",
        "price_credits": 1.5
    },
    {
        "service_id": "watermark_removal",
        "service_name": "去水印",
        "service_key": "watermark_removal",
        "description": "AI去水印",
        "price_credits": 0.9
    },
    {
        "service_id": "noise_removal",
        "service_name": "布纹降噪",
        "service_key": "noise_removal",
        "description": "AI布纹去噪",
        "price_credits": 0.5
    },
    {
        "service_id": "style",
        "service_name": "转矢量",
        "service_key": "style",
        "description": "AI矢量化",
        "price_credits": 2.5
    },
    {
        "service_id": "upscale",
        "service_name": "高清放大",
        "service_key": "upscale",
        "description": "AI无损放大",
        "price_credits": 0.9
    },
]

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
    """获取优惠套餐"""
    return DISCOUNT_PACKAGES


def get_service_prices():
    """获取服务价格"""
    return SERVICE_PRICES


def get_new_user_bonus():
    """获取新用户福利"""
    return NEW_USER_BONUS