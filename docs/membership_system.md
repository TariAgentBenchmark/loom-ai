# 会员与价格体系档

## 概述

本系统实现了完整的会员和价格体系，支持积分兑换、套餐购买、服务计费和退款管理。

## 核心功能

### 1. 积分兑换系统
- **兑换率**: 1元人民币 = 1积分
- **积分永不过期**: 所有积分永久有效
- **积分用途**: 用于支付AI服务费用

### 2. 会员套餐体系

#### 👑 会员套餐（可退款）
| 套餐名称 | 价格 | 赠送积分 | 实得积分 | 每元积分 | 退款政策 |
|---------|------|----------|----------|----------|----------|
| 3000元会员套餐 | ¥3,000 | 400 | 3,400 | 1.13 | 扣除20% |
| 6000元会员套餐 | ¥6,000 | 900 | 6,900 | 1.15 | 扣除20% |
| 10000元会员套餐 | ¥10,000 | 2,000 | 12,000 | 1.20 | 扣除20% |
| 15000元会员套餐 | ¥15,000 | 3,000 | 18,000 | 1.20 | 扣除20% |

**会员特权**:
- ✅ 购买全站功能
- ✅ 积分永不过期
- ✅ 可退款（需扣除充值原金额的20%，赠送积分不参与退款）

#### 💰 优惠套餐（不可退款）
| 套餐名称 | 价格 | 赠送积分 | 实得积分 | 每元积分 |
|---------|------|----------|----------|----------|
| 30元优惠套餐 | ¥30 | 0 | 30 | 1.00 |
| 100元优惠套餐 | ¥100 | 10 | 110 | 1.10 |
| 300元优惠套餐 | ¥300 | 30 | 330 | 1.10 |
| 500元优惠套餐 | ¥500 | 50 | 550 | 1.10 |

**优惠套餐说明**:
- ✅ 购买全站功能
- ✅ 积分永不过期
- ❌ 不可退款

### 3. 服务项目价格

#### 🛠️ AI服务价格（积分）
| 服务项目 | 价格 | 描述 |
|---------|------|------|
| 用嘴改图 | 0.5 积分 | AI用嘴改图 |
| 刺绣 | 0.7 积分 | AI刺绣 |
| 提取花型 | 1.5 积分 | AI提取花型 |
| 去水印 | 0.9 积分 | AI去水印 |
| 布纹降噪 | 0.5 积分 | AI布纹去噪 |
| 转矢量 | 2.5 积分 | AI矢量化 |
| AI高清 | 0.9 积分 | AI高清 |

### 4. 新用户福利
- **👤 新用户福利**: 注册即赠送 10 积分

## 系统架构

### 数据模型

#### MembershipPackage (会员套餐)
- `package_id`: 套餐唯一标识
- `name`: 套餐名称
- `category`: 套餐分类 (membership/discount)
- `price_yuan`: 价格（元）
- `bonus_credits`: 赠送积分
- `total_credits`: 实得积分
- `refund_policy`: 退款策略
- `refund_deduction_rate`: 退款扣除比例
- `privileges`: 特权列表

#### ServicePrice (服务价格)
- `service_id`: 服务唯一标识
- `service_name`: 服务名称
- `service_key`: 服务标识键
- `price_credits`: 价格（积分）

#### UserMembership (用户会员记录)
- 记录用户购买的套餐信息
- 跟踪退款状态和使用情况

#### NewUserBonus (新用户福利)
- 配置新用户赠送积分数量

### API 端点

#### 套餐管理
- `GET /v1/membership/packages` - 获取套餐列表
- `GET /v1/membership/packages?category={category}` - 按分类获取套餐

#### 服务价格
- `GET /v1/membership/services` - 获取服务价格列表
- `GET /v1/membership/service-cost` - 计算服务成本

#### 购买与退款
- `POST /v1/membership/purchase` - 购买套餐
- `POST /v1/membership/refund` - 退款套餐
- `POST /v1/membership/new-user-bonus` - 申请新用户福利

#### 用户管理
- `GET /v1/membership/my-memberships` - 获取我的会员记录
- `GET /v1/membership/can-afford-service` - 检查是否能支付服务费用

### 业务逻辑

#### 积分兑换服务 (CreditExchangeService)
- 人民币与积分转换
- 套餐价值计算
- 性价比分析
- 使用场景推荐

#### 会员服务 (MembershipService)
- 套餐购买处理
- 积分发放
- 退款处理
- 新用户福利发放

## 使用示例

### 1. 获取套餐列表
```bash
curl -X GET "http://localhost:8000/v1/membership/packages"
```

### 2. 购买套餐
```bash
curl -X POST "http://localhost:8000/v1/membership/purchase" \
  -H "Content-Type: application/json" \
  -d '{
    "package_id": "membership_3000",
    "payment_method": "alipay",
    "order_id": "order_123456"
  }'
```

### 3. 申请新用户福利
```bash
curl -X POST "http://localhost:8000/v1/membership/new-user-bonus"
```

### 4. 计算服务成本
```bash
curl -X GET "http://localhost:8000/v1/membership/service-cost?service_key=extract_pattern&quantity=5"
```

## 前端组件

### MembershipPricingModal
- 展示完整的会员和价格体系
- 支持套餐分类切换
- 显示服务价格信息
- 提供购买入口

## 初始化数据

系统启动时会自动初始化以下数据：

1. **会员套餐**: 4个可退款套餐
2. **优惠套餐**: 4个不可退款套餐
3. **服务价格**: 7个AI服务项目
4. **新用户福利**: 10积分赠送

## 测试

运行测试脚本验证功能：
```bash
cd backend
python test_membership_api.py
```

## 部署说明

1. 确保数据库已创建
2. 运行数据初始化脚本：
   ```bash
   python migrations/init_membership_packages.py
   ```
3. 启动后端服务
4. 前端集成 `MembershipPricingModal` 组件

## 注意事项

1. **退款策略**: 会员套餐退款时只扣除实际支付金额的20%，赠送积分不参与退款计算
2. **积分有效期**: 所有积分永久有效，无过期时间
3. **服务计费**: 每次使用AI服务时实时扣除相应积分
4. **余额检查**: 使用服务前会检查用户积分余额是否足够
