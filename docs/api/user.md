# 用户管理 API

## 概述

用户管理模块负责用户信息的查询、更新和账户统计功能。

## 接口列表

### 1. 获取用户信息

**接口地址**: `GET /user/profile`

**描述**: 获取当前用户的详细信息

**请求头**:
```
Authorization: Bearer access-token-here
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "userId": "user_123456789",
    "email": "user@example.com",
    "nickname": "用户昵称",
    "phone": "13888888888",
    "avatar": "https://cdn.loom-ai.com/avatars/user_123456789.jpg",
    "credits": 2580,             // 剩余算力
    "membershipType": "premium",  // 会员类型：free|basic|premium|enterprise
    "membershipExpiry": "2024-03-01T00:00:00Z",
    "totalProcessed": 1247,      // 总处理次数
    "monthlyProcessed": 156,     // 本月处理次数
    "joinedAt": "2023-06-15T08:30:00Z",
    "lastLoginAt": "2023-12-01T09:45:00Z",
    "status": "active"           // 账户状态：active|suspended|inactive
  },
  "message": "获取用户信息成功"
}
```

### 2. 更新用户信息

**接口地址**: `PUT /user/profile`

**描述**: 更新用户基本信息

**请求头**:
```
Authorization: Bearer access-token-here
```

**请求参数**:
```json
{
  "nickname": "新昵称",         // 昵称（可选）
  "phone": "13999999999",       // 手机号（可选）
  "avatar": "avatar_file_id"    // 头像文件ID（可选）
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "userId": "user_123456789",
    "email": "user@example.com",
    "nickname": "新昵称",
    "phone": "13999999999",
    "avatar": "https://cdn.loom-ai.com/avatars/user_123456789_new.jpg",
    "updatedAt": "2023-12-01T10:15:00Z"
  },
  "message": "用户信息更新成功"
}
```

### 3. 上传头像

**接口地址**: `POST /user/avatar`

**描述**: 上传用户头像

**请求头**:
```
Authorization: Bearer access-token-here
Content-Type: multipart/form-data
```

**请求参数**:
- **Form Data**:
  - `avatar`: 头像文件（必填，支持JPG/PNG，最大5MB）

**响应示例**:
```json
{
  "success": true,
  "data": {
    "avatarUrl": "https://cdn.loom-ai.com/avatars/user_123456789.jpg",
    "fileId": "avatar_file_123456",
    "uploadedAt": "2023-12-01T10:20:00Z"
  },
  "message": "头像上传成功"
}
```

### 4. 获取账户统计

**接口地址**: `GET /user/stats`

**描述**: 获取用户账户统计信息

**请求头**:
```
Authorization: Bearer access-token-here
```

**查询参数**:
- `period`: 统计周期（可选）
  - `today`: 今日
  - `week`: 本周
  - `month`: 本月
  - `year`: 本年
  - `all`: 全部（默认）

**响应示例**:
```json
{
  "success": true,
  "data": {
    "credits": {
      "current": 2580,           // 当前算力
      "totalEarned": 15000,      // 总获得算力
      "totalUsed": 12420,        // 总消耗算力
      "monthlyUsed": 1840        // 本月消耗算力
    },
    "processing": {
      "totalTasks": 1247,        // 总任务数
      "completedTasks": 1190,    // 完成任务数
      "failedTasks": 57,         // 失败任务数
      "monthlyTasks": 156        // 本月任务数
    },
    "usage": {
      "seamless": 234,           // 四方连续转换使用次数
      "vectorize": 189,          // 矢量化使用次数
      "extractPattern": 145,     // 提取花型使用次数
      "removeWatermark": 234,    // 去水印使用次数
      "denoise": 178,            // 去噪使用次数
      "embroidery": 101          // 刺绣增强使用次数
    },
    "membership": {
      "type": "premium",
      "startDate": "2023-09-01T00:00:00Z",
      "endDate": "2024-03-01T00:00:00Z",
      "daysRemaining": 89
    },
    "period": "all"
  },
  "message": "获取统计信息成功"
}
```

### 5. 获取使用历史

**接口地址**: `GET /user/usage-history`

**描述**: 获取用户的使用历史记录

**请求头**:
```
Authorization: Bearer access-token-here
```

**查询参数**:
- `startDate`: 开始日期 (YYYY-MM-DD)
- `endDate`: 结束日期 (YYYY-MM-DD)
- `type`: 处理类型过滤（可选）
- `page`: 页码（默认1）
- `limit`: 每页数量（默认20）

**响应示例**:
```json
{
  "success": true,
  "data": {
    "records": [
      {
        "date": "2023-12-01",
        "type": "seamless",
        "typeName": "AI四方连续转换",
        "count": 8,
        "creditsUsed": 480,
        "tasks": [
          {
            "taskId": "task_seamless_123456789",
            "status": "completed",
            "creditsUsed": 60,
            "createdAt": "2023-12-01T10:00:00Z"
          }
        ]
      }
    ],
    "summary": {
      "totalTasks": 156,
      "totalCredits": 12420,
      "period": "2023-11-01 to 2023-12-01"
    },
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 156,
      "totalPages": 8
    }
  },
  "message": "获取使用历史成功"
}
```

### 6. 获取通知设置

**接口地址**: `GET /user/notifications`

**描述**: 获取用户的通知设置

**请求头**:
```
Authorization: Bearer access-token-here
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "email": {
      "taskCompleted": true,      // 任务完成通知
      "creditLow": true,          // 算力不足通知
      "membershipExpiry": true,   // 会员到期通知
      "newsletter": false         // 新闻邮件
    },
    "push": {
      "taskCompleted": true,
      "creditLow": true,
      "membershipExpiry": true
    },
    "sms": {
      "taskCompleted": false,
      "creditLow": true,
      "membershipExpiry": true
    }
  },
  "message": "获取通知设置成功"
}
```

### 7. 更新通知设置

**接口地址**: `PUT /user/notifications`

**描述**: 更新用户的通知设置

**请求头**:
```
Authorization: Bearer access-token-here
```

**请求参数**:
```json
{
  "email": {
    "taskCompleted": true,
    "creditLow": true,
    "membershipExpiry": true,
    "newsletter": false
  },
  "push": {
    "taskCompleted": true,
    "creditLow": true,
    "membershipExpiry": true
  },
  "sms": {
    "taskCompleted": false,
    "creditLow": true,
    "membershipExpiry": true
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "updatedAt": "2023-12-01T10:30:00Z"
  },
  "message": "通知设置更新成功"
}
```

### 8. 注销账户

**接口地址**: `DELETE /user/account`

**描述**: 注销用户账户（需要二次确认）

**请求头**:
```
Authorization: Bearer access-token-here
```

**请求参数**:
```json
{
  "password": "user_password",    // 用户密码（必填）
  "reason": "不再需要此服务",      // 注销原因（可选）
  "confirmText": "DELETE"        // 确认文本（必填）
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "scheduledDeletion": "2023-12-08T10:00:00Z" // 计划删除时间（7天后）
  },
  "message": "账户注销申请已提交，7天内可取消"
}
```

### 9. 取消注销

**接口地址**: `POST /user/account/restore`

**描述**: 取消账户注销申请

**请求头**:
```
Authorization: Bearer access-token-here
```

**响应示例**:
```json
{
  "success": true,
  "data": null,
  "message": "账户注销已取消"
}
```

### 10. 获取API密钥

**接口地址**: `GET /user/api-keys`

**描述**: 获取用户的API密钥列表

**请求头**:
```
Authorization: Bearer access-token-here
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "apiKeys": [
      {
        "keyId": "key_123456789",
        "name": "生产环境密钥",
        "keyPrefix": "loom_prod_",
        "permissions": ["processing", "user"],
        "lastUsed": "2023-12-01T09:30:00Z",
        "createdAt": "2023-11-01T10:00:00Z",
        "status": "active"
      }
    ]
  },
  "message": "获取API密钥成功"
}
```

### 11. 创建API密钥

**接口地址**: `POST /user/api-keys`

**描述**: 创建新的API密钥

**请求头**:
```
Authorization: Bearer access-token-here
```

**请求参数**:
```json
{
  "name": "测试环境密钥",         // 密钥名称（必填）
  "permissions": [              // 权限列表（必填）
    "processing",
    "user"
  ],
  "expiresIn": 2592000         // 过期时间（秒，可选，默认永不过期）
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "keyId": "key_987654321",
    "name": "测试环境密钥",
    "apiKey": "loom_test_abcdef123456...",  // 完整密钥（仅此次显示）
    "permissions": ["processing", "user"],
    "expiresAt": "2024-01-01T10:00:00Z",
    "createdAt": "2023-12-01T10:00:00Z"
  },
  "message": "API密钥创建成功"
}
```

## 错误码说明

| 错误码 | 说明 |
|-------|------|
| U001 | 用户不存在 |
| U002 | 头像文件格式不支持 |
| U003 | 头像文件过大 |
| U004 | 昵称已被使用 |
| U005 | 手机号格式不正确 |
| U006 | 账户已被暂停 |
| U007 | 密码验证失败 |
| U008 | 注销确认文本不正确 |
| U009 | API密钥数量已达上限 |
| U010 | 权限不足 |
