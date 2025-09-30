# 历史记录 API

## 概述

历史记录模块负责管理用户的处理历史、结果下载、收藏管理等功能。

## 接口列表

### 1. 获取处理历史

**接口地址**: `GET /history/tasks`

**描述**: 获取用户的图片处理历史记录

**请求头**:
```
Authorization: Bearer access-token-here
```

**查询参数**:
- `type`: 处理类型过滤（可选）
  - `seamless`: AI四方连续转换
  - `vectorize`: AI矢量化(转SVG)
  - `extractEdit`: AI提取编辑
  - `extractPattern`: AI提取花型
  - `removeWatermark`: AI智能去水印
  - `denoise`: AI布纹去噪
  - `embroidery`: AI毛线刺绣增强
- `status`: 状态过滤（可选）
  - `completed`: 已完成
  - `failed`: 失败
  - `processing`: 处理中
- `startDate`: 开始日期 (YYYY-MM-DD)
- `endDate`: 结束日期 (YYYY-MM-DD)
- `keyword`: 关键词搜索（可选）
- `page`: 页码（默认1）
- `limit`: 每页数量（默认20）
- `sortBy`: 排序字段（createdAt|completedAt）
- `sortOrder`: 排序方式（desc|asc，默认desc）

**响应示例**:
```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "taskId": "task_seamless_123456789",
        "type": "seamless",
        "typeName": "AI四方连续转换",
        "status": "completed",
        "originalImage": {
          "url": "https://cdn.loom-ai.com/originals/abc123.jpg",
          "filename": "original_pattern.jpg",
          "size": 1048576,
          "dimensions": {
            "width": 1024,
            "height": 768
          }
        },
        "resultImage": {
          "url": "https://cdn.loom-ai.com/results/def456.png",
          "filename": "seamless_pattern.png",
          "size": 2048576,
          "dimensions": {
            "width": 1024,
            "height": 1024
          }
        },
        "options": {
          "removeBackground": true,
          "seamlessLoop": true
        },
        "creditsUsed": 60,
        "processingTime": 125,        // 处理时间（秒）
        "favorite": false,            // 是否收藏
        "tags": ["花卉", "装饰"],     // 用户标签
        "createdAt": "2023-12-01T10:00:00Z",
        "completedAt": "2023-12-01T10:02:05Z"
      }
    ],
    "statistics": {
      "totalTasks": 156,
      "completedTasks": 148,
      "failedTasks": 8,
      "totalCreditsUsed": 12420,
      "avgProcessingTime": 142
    },
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 156,
      "totalPages": 8
    }
  },
  "message": "获取历史记录成功"
}
```

### 2. 获取单个任务详情

**接口地址**: `GET /history/tasks/{taskId}`

**描述**: 获取指定任务的详细信息

**请求头**:
```
Authorization: Bearer access-token-here
```

**路径参数**:
- `taskId`: 任务ID

**响应示例**:
```json
{
  "success": true,
  "data": {
    "taskId": "task_seamless_123456789",
    "type": "seamless",
    "typeName": "AI四方连续转换",
    "status": "completed",
    "originalImage": {
      "url": "https://cdn.loom-ai.com/originals/abc123.jpg",
      "filename": "original_pattern.jpg",
      "size": 1048576,
      "format": "jpeg",
      "dimensions": {
        "width": 1024,
        "height": 768
      },
      "uploadedAt": "2023-12-01T10:00:00Z"
    },
    "resultImage": {
      "url": "https://cdn.loom-ai.com/results/def456.png",
      "filename": "seamless_pattern.png",
      "size": 2048576,
      "format": "png",
      "dimensions": {
        "width": 1024,
        "height": 1024
      }
    },
    "options": {
      "removeBackground": true,
      "seamlessLoop": true
    },
    "metadata": {
      "algorithm": "seamless-v2.1",
      "processingSteps": [
        {
          "step": "background_removal",
          "duration": 45,
          "status": "completed"
        },
        {
          "step": "pattern_analysis",
          "duration": 32,
          "status": "completed"
        },
        {
          "step": "seamless_generation", 
          "duration": 48,
          "status": "completed"
        }
      ]
    },
    "creditsUsed": 60,
    "processingTime": 125,
    "favorite": false,
    "tags": ["花卉", "装饰"],
    "notes": "用于春季产品设计",     // 用户备注
    "downloadCount": 3,             // 下载次数
    "lastDownloaded": "2023-12-01T15:30:00Z",
    "createdAt": "2023-12-01T10:00:00Z",
    "startedAt": "2023-12-01T10:00:15Z",
    "completedAt": "2023-12-01T10:02:05Z"
  },
  "message": "获取任务详情成功"
}
```

### 3. 下载历史结果

**接口地址**: `GET /history/download/{taskId}`

**描述**: 下载历史处理结果

**请求头**:
```
Authorization: Bearer access-token-here
```

**路径参数**:
- `taskId`: 任务ID

**查询参数**:
- `format`: 输出格式（png|jpg|svg）（可选，默认原格式）
- `size`: 输出尺寸（small|medium|large|original）（可选，默认original）

**响应**: 直接返回图片文件流

### 4. 批量下载

**接口地址**: `POST /history/batch-download`

**描述**: 批量下载多个历史结果

**请求头**:
```
Authorization: Bearer access-token-here
```

**请求参数**:
```json
{
  "taskIds": [
    "task_seamless_123456789",
    "task_vectorize_987654321",
    "task_denoise_456789123"
  ],
  "format": "zip",              // 压缩格式：zip|tar
  "includeOriginals": false     // 是否包含原图
}
```

**响应**: 返回压缩包文件流

### 5. 添加到收藏

**接口地址**: `POST /history/favorites/{taskId}`

**描述**: 将任务添加到收藏夹

**请求头**:
```
Authorization: Bearer access-token-here
```

**路径参数**:
- `taskId`: 任务ID

**响应示例**:
```json
{
  "success": true,
  "data": {
    "taskId": "task_seamless_123456789",
    "favorite": true,
    "favoritedAt": "2023-12-01T11:00:00Z"
  },
  "message": "添加收藏成功"
}
```

### 6. 取消收藏

**接口地址**: `DELETE /history/favorites/{taskId}`

**描述**: 从收藏夹中移除任务

**请求头**:
```
Authorization: Bearer access-token-here
```

**路径参数**:
- `taskId`: 任务ID

**响应示例**:
```json
{
  "success": true,
  "data": {
    "taskId": "task_seamless_123456789",
    "favorite": false
  },
  "message": "取消收藏成功"
}
```

### 7. 获取收藏列表

**接口地址**: `GET /history/favorites`

**描述**: 获取用户的收藏任务列表

**请求头**:
```
Authorization: Bearer access-token-here
```

**查询参数**:
- `type`: 处理类型过滤（可选）
- `page`: 页码（默认1）
- `limit`: 每页数量（默认20）
- `sortBy`: 排序字段（favoritedAt|createdAt）
- `sortOrder`: 排序方式（desc|asc，默认desc）

**响应示例**:
```json
{
  "success": true,
  "data": {
    "favorites": [
      {
        "taskId": "task_seamless_123456789",
        "type": "seamless",
        "typeName": "AI四方连续转换",
        "originalImage": {
          "url": "https://cdn.loom-ai.com/originals/abc123.jpg",
          "thumbnail": "https://cdn.loom-ai.com/thumbnails/abc123_thumb.jpg"
        },
        "resultImage": {
          "url": "https://cdn.loom-ai.com/results/def456.png",
          "thumbnail": "https://cdn.loom-ai.com/thumbnails/def456_thumb.jpg"
        },
        "tags": ["花卉", "装饰"],
        "createdAt": "2023-12-01T10:00:00Z",
        "favoritedAt": "2023-12-01T11:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 23,
      "totalPages": 2
    }
  },
  "message": "获取收藏列表成功"
}
```

### 8. 添加任务标签

**接口地址**: `POST /history/tasks/{taskId}/tags`

**描述**: 为任务添加标签

**请求头**:
```
Authorization: Bearer access-token-here
```

**路径参数**:
- `taskId`: 任务ID

**请求参数**:
```json
{
  "tags": ["春季", "花卉", "产品设计"]    // 标签数组（必填）
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "taskId": "task_seamless_123456789",
    "tags": ["春季", "花卉", "产品设计", "装饰"],
    "updatedAt": "2023-12-01T11:15:00Z"
  },
  "message": "标签添加成功"
}
```

### 9. 更新任务备注

**接口地址**: `PUT /history/tasks/{taskId}/notes`

**描述**: 更新任务备注

**请求头**:
```
Authorization: Bearer access-token-here
```

**路径参数**:
- `taskId`: 任务ID

**请求参数**:
```json
{
  "notes": "这个设计用于春季新品发布，需要制作成不同尺寸的版本。"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "taskId": "task_seamless_123456789",
    "notes": "这个设计用于春季新品发布，需要制作成不同尺寸的版本。",
    "updatedAt": "2023-12-01T11:20:00Z"
  },
  "message": "备注更新成功"
}
```

### 10. 删除历史记录

**接口地址**: `DELETE /history/tasks/{taskId}`

**描述**: 删除指定的历史记录

**请求头**:
```
Authorization: Bearer access-token-here
```

**路径参数**:
- `taskId`: 任务ID

**响应示例**:
```json
{
  "success": true,
  "data": null,
  "message": "历史记录删除成功"
}
```

### 11. 批量删除历史记录

**接口地址**: `POST /history/tasks/batch-delete`

**描述**: 批量删除历史记录

**请求头**:
```
Authorization: Bearer access-token-here
```

**请求参数**:
```json
{
  "taskIds": [
    "task_seamless_123456789",
    "task_vectorize_987654321"
  ],
  "deleteFiles": true           // 是否同时删除文件
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "deletedCount": 2,
    "failedIds": []             // 删除失败的任务ID
  },
  "message": "批量删除成功"
}
```

### 12. 获取常用标签

**接口地址**: `GET /history/tags`

**描述**: 获取用户常用的标签列表

**请求头**:
```
Authorization: Bearer access-token-here
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "tags": [
      {
        "name": "花卉",
        "count": 45,              // 使用次数
        "color": "#ff6b6b"        // 标签颜色
      },
      {
        "name": "装饰",
        "count": 38,
        "color": "#4ecdc4"
      },
      {
        "name": "产品设计",
        "count": 29,
        "color": "#45b7d1"
      }
    ]
  },
  "message": "获取标签列表成功"
}
```

### 13. 分享任务

**接口地址**: `POST /history/tasks/{taskId}/share`

**描述**: 生成任务分享链接

**请求头**:
```
Authorization: Bearer access-token-here
```

**路径参数**:
- `taskId`: 任务ID

**请求参数**:
```json
{
  "expireHours": 24,            // 分享链接有效期（小时）
  "allowDownload": true,        // 是否允许下载
  "password": "123456"          // 分享密码（可选）
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "shareId": "share_123456789",
    "shareUrl": "https://loom-ai.com/share/share_123456789",
    "qrCode": "https://api.loom-ai.com/share/qr/share_123456789.png",
    "expiresAt": "2023-12-02T11:30:00Z",
    "viewCount": 0
  },
  "message": "分享链接生成成功"
}
```

### 14. 获取分享记录

**接口地址**: `GET /history/shares`

**描述**: 获取用户的分享记录

**请求头**:
```
Authorization: Bearer access-token-here
```

**查询参数**:
- `status`: 分享状态（active|expired）（可选）
- `page`: 页码（默认1）
- `limit`: 每页数量（默认20）

**响应示例**:
```json
{
  "success": true,
  "data": {
    "shares": [
      {
        "shareId": "share_123456789",
        "taskId": "task_seamless_123456789",
        "shareUrl": "https://loom-ai.com/share/share_123456789",
        "status": "active",       // 状态：active|expired
        "viewCount": 12,
        "downloadCount": 3,
        "createdAt": "2023-12-01T11:30:00Z",
        "expiresAt": "2023-12-02T11:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 8,
      "totalPages": 1
    }
  },
  "message": "获取分享记录成功"
}
```

## 数据统计

### 历史统计信息

- **总任务数**: 用户处理的所有任务数量
- **成功率**: 完成任务数 / 总任务数
- **平均处理时间**: 所有完成任务的平均处理时长
- **算力消耗**: 总计消耗的算力数量
- **收藏数量**: 收藏的任务数量
- **分享次数**: 生成的分享链接数量

### 按类型统计

系统会统计每种处理类型的使用情况：
- 使用次数
- 成功率
- 平均处理时间
- 算力消耗

## 错误码说明

| 错误码 | 说明 |
|-------|------|
| H001 | 历史记录不存在 |
| H002 | 文件已过期或不可下载 |
| H003 | 批量操作数量超限 |
| H004 | 标签数量超限 |
| H005 | 备注长度超限 |
| H006 | 分享已过期 |
| H007 | 分享密码错误 |
| H008 | 无权限访问该记录 |
| H009 | 文件下载失败 |
| H010 | 分享链接生成失败 |
