# LoomAI API 文档索引

欢迎使用 LoomAI API 文档！本文档提供了完整的 API 接口说明。

## 📚 文档结构

### 核心模块
- [**总览**](./README.md) - API概述、快速开始、基础信息
- [**认证管理**](./auth.md) - 用户注册、登录、Token管理
- [**用户管理**](./user.md) - 用户信息、账户统计、设置管理
- [**图片处理**](./processing.md) - 7种AI图片处理功能的完整API
- [**算力管理**](./credits.md) - 算力查询、消耗记录、转赠功能
- [**历史记录**](./history.md) - 处理历史、结果管理、收藏功能
- [**套餐充值**](./payment.md) - 套餐购买、支付管理、退款流程

### 技术规范
- [**文件上传**](./upload.md) - 文件上传规范、最佳实践
- [**错误码定义**](./errors.md) - 完整的错误码说明和处理建议

## 🚀 快速导航

### 开发必读
1. [API概览](./README.md#概览) - 了解基础信息
2. [认证流程](./auth.md#用户登录) - 获取访问令牌
3. [图片处理](./processing.md#接口列表) - 核心功能使用

### 常用功能
- [图片处理流程](./processing.md#通用处理流程)
- [算力余额查询](./credits.md#获取算力余额)
- [处理历史管理](./history.md#获取处理历史)
- [套餐购买流程](./payment.md#支付流程说明)

### 错误处理
- [HTTP状态码](./errors.md#http状态码)
- [错误码分类](./errors.md#错误码分类)
- [重试策略](./errors.md#重试策略)

## 🎯 AI功能列表

| 功能名称 | 端点 | 算力消耗 | 说明 |
|---------|------|----------|------|
| AI四方连续转换 | `/processing/seamless` | 60 | 矩形图转四方连续打印图 |
| AI矢量化(转SVG) | `/processing/vectorize` | 100 | 图片转SVG矢量图 |
| AI提取编辑 | `/processing/extract-edit` | 80 | 智能编辑，支持语音控制 |
| AI提取花型 | `/processing/extract-pattern` | 100 | 提取花型元素 |
| AI智能去水印 | `/processing/remove-watermark` | 70 | 去除各类水印 |
| AI布纹去噪 | `/processing/denoise` | 80 | 去噪点和布纹 |
| AI毛线刺绣增强 | `/processing/embroidery` | 90 | 毛线刺绣效果 |

## 📖 使用指南

### 第一次使用
1. [注册账号](./auth.md#用户注册)
2. [登录获取Token](./auth.md#用户登录)
3. [选择处理功能](./processing.md)
4. [上传图片进行处理](./upload.md)
5. [查看处理结果](./processing.md#查询任务状态)

### 进阶功能
- [批量处理](./processing.md#批量操作接口)
- [历史管理](./history.md)
- [算力转赠](./credits.md#算力转赠)
- [API密钥管理](./user.md#获取api密钥)

## 🛠️ 技术支持

- **API问题**: api@loom-ai.com
- **技术支持**: tech@loom-ai.com
- **商务合作**: business@loom-ai.com

---

**版本**: v1.0.0  
**更新日期**: 2023-12-01  
**Base URL**: `https://api.loom-ai.com/v1`
