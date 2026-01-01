# LoomAI API 文档

## 概览

LoomAI 是一个基于人工智能的图案处理平台，提供多种图像处理功能。本API文档涵盖了所有可用的接口。

## 基础信息

- **Base URL**: `https://api.loom-ai.com/v1`
- **认证方式**: Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8

## 功能模块

### 核心功能
- [认证管理](./auth.md) - 用户登录、注册、Token管理
- [用户管理](./user.md) - 用户信息、账户统计
- [图片处理](./processing.md) - 所有AI图片处理功能
- [算力管理](./credits.md) - 算力查询、消耗记录
- [历史记录](./history.md) - 处理历史、结果管理
- [套餐充值](./payment.md) - 套餐购买、充值功能

### 支持功能
- [错误码定义](./errors.md) - 所有错误码说明
- [文件上传](./upload.md) - 文件上传规范

## API 功能列表

### 🎨 图片处理功能

| 功能名称 | 功能描述 | 算力消耗 |
|---------|----------|----------|
| AI四方连续转换 | 将图案转换为四方连续的打印图 | 60算力 |
| AI矢量化(转SVG) | 将图片转换为SVG矢量图 | 100算力 |
| AI提取花型 | 提取图案中的花型元素 | 100算力 |
| AI智能去水印 | 去除文字和Logo水印 | 70算力 |
| AI布纹去噪 | 去除噪点和布纹 | 80算力 |
| AI毛线刺绣增强 | 使用即梦AI技术的高质量毛线刺绣增强，支持4K输出 | 120算力 |

## 快速开始

### 1. 获取访问令牌

```bash
curl -X POST https://api.loom-ai.com/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password"
  }'
```

### 2. 上传并处理图片

```bash
curl -X POST https://api.loom-ai.com/v1/processing/seamless \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "image=@path/to/your/image.jpg" \
  -F "options={\"removeBackground\": true, \"seamlessLoop\": true}"
```

### 3. 下载处理结果

```bash
curl -X GET https://api.loom-ai.com/v1/processing/result/{task_id}/download \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o result.png
```

## 请求和响应格式

### 标准响应格式

```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2023-12-01T10:00:00Z"
}
```

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "E001",
    "message": "参数错误",
    "details": "image 字段不能为空"
  },
  "timestamp": "2023-12-01T10:00:00Z"
}
```

## 认证说明

所有API请求都需要在请求头中包含有效的Bearer Token：

```
Authorization: Bearer your-access-token-here
```

## 限制说明

- 单次上传图片大小限制：15MB
- 支持的图片格式：PNG, JPG, JPEG, GIF, BMP
- 图片分辨率建议：1024-3000px
- API请求频率限制：100次/分钟

## 更新日志

- **v1.1.0** (2025-01-01): 即梦AI集成版本
  - 升级AI毛线刺绣增强功能，集成即梦4.0模型
  - 支持4K超高清输出，提供更真实的毛线质感
  - 优化处理参数，支持自定义scale、size等选项
  - 增加任务状态轮询机制，提升处理稳定性

- **v1.0.0** (2023-12-01): 初始版本发布
  - 基础的6个AI图片处理功能
  - 用户认证和算力系统
  - 套餐充值功能

## 联系支持

如有问题，请联系：
- 技术支持：tech@loom-ai.com
- API问题：api@loom-ai.com
