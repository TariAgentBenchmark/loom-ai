# 认证管理 API

## 概述

认证系统负责用户的注册、登录、Token管理等功能。

## 接口列表

### 1. 用户注册

**接口地址**: `POST /auth/register`

**描述**: 新用户注册账号

**请求参数**:

```json
{
  "email": "user@example.com",      // 邮箱地址（必填）
  "password": "password123",        // 密码（必填，至少8位）
  "confirmPassword": "password123", // 确认密码（必填）
  "nickname": "用户昵称",           // 昵称（可选）
  "phone": "13888888888"           // 手机号（可选）
}
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "userId": "user_123456789",
    "email": "user@example.com",
    "nickname": "用户昵称",
    "credits": 200,                 // 新用户赠送200算力
    "createdAt": "2023-12-01T10:00:00Z"
  },
  "message": "注册成功，已赠送200算力"
}
```

### 2. 用户登录

**接口地址**: `POST /auth/login`

**描述**: 用户登录获取访问令牌

**请求参数**:

```json
{
  "email": "user@example.com",     // 邮箱地址（必填）
  "password": "password123",       // 密码（必填）
  "rememberMe": true              // 是否记住登录状态（可选）
}
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 86400,             // Token过期时间（秒）
    "tokenType": "Bearer",
    "user": {
      "userId": "user_123456789",
      "email": "user@example.com",
      "nickname": "用户昵称",
      "credits": 2580,              // 剩余算力
      "avatar": "https://cdn.loom-ai.com/avatars/user_123456789.jpg"
    }
  },
  "message": "登录成功"
}
```

### 3. 刷新Token

**接口地址**: `POST /auth/refresh`

**描述**: 使用refresh token获取新的access token

**请求头**:
```
Authorization: Bearer refresh-token-here
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 86400,
    "tokenType": "Bearer"
  },
  "message": "Token刷新成功"
}
```

### 4. 用户登出

**接口地址**: `POST /auth/logout`

**描述**: 用户登出，使Token失效

**请求头**:
```
Authorization: Bearer access-token-here
```

**响应示例**:

```json
{
  "success": true,
  "data": null,
  "message": "登出成功"
}
```

### 5. 忘记密码

**接口地址**: `POST /auth/forgot-password`

**描述**: 发送密码重置邮件

**请求参数**:

```json
{
  "email": "user@example.com"     // 邮箱地址（必填）
}
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "resetToken": "reset_token_123456",
    "expiresIn": 3600               // 重置链接有效期（秒）
  },
  "message": "密码重置邮件已发送"
}
```

### 6. 重置密码

**接口地址**: `POST /auth/reset-password`

**描述**: 使用重置令牌重置密码

**请求参数**:

```json
{
  "resetToken": "reset_token_123456", // 重置令牌（必填）
  "newPassword": "newpassword123",    // 新密码（必填）
  "confirmPassword": "newpassword123" // 确认密码（必填）
}
```

**响应示例**:

```json
{
  "success": true,
  "data": null,
  "message": "密码重置成功"
}
```

### 7. 修改密码

**接口地址**: `PUT /auth/change-password`

**描述**: 用户修改密码

**请求头**:
```
Authorization: Bearer access-token-here
```

**请求参数**:

```json
{
  "currentPassword": "oldpassword123", // 当前密码（必填）
  "newPassword": "newpassword123",     // 新密码（必填）
  "confirmPassword": "newpassword123"  // 确认密码（必填）
}
```

**响应示例**:

```json
{
  "success": true,
  "data": null,
  "message": "密码修改成功"
}
```

### 8. 验证Token

**接口地址**: `GET /auth/verify`

**描述**: 验证当前Token是否有效

**请求头**:
```
Authorization: Bearer access-token-here
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "valid": true,
    "expiresAt": "2023-12-02T10:00:00Z",
    "user": {
      "userId": "user_123456789",
      "email": "user@example.com",
      "nickname": "用户昵称"
    }
  },
  "message": "Token有效"
}
```

## 错误码说明

| 错误码 | 说明 |
|-------|------|
| A001 | 邮箱格式不正确 |
| A002 | 密码长度不足 |
| A003 | 邮箱已存在 |
| A004 | 登录凭据无效 |
| A005 | Token已过期 |
| A006 | Token无效 |
| A007 | 重置令牌无效或已过期 |
| A008 | 当前密码错误 |

## 安全说明

1. 所有密码都应该进行安全加密存储
2. Token应该设置合理的过期时间
3. 登录失败次数应该有限制
4. 重要操作应该进行二次验证
5. 建议使用HTTPS协议传输敏感信息
