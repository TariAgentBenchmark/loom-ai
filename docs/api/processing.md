# 图片处理 API

## 概述

图片处理模块是LoomAI的核心功能，提供6种不同的AI图片处理服务。

## 通用处理流程

1. **上传图片** → 2. **提交处理任务** → 3. **查询处理状态** → 4. **下载结果**

## 接口列表

### 1. AI四方连续转换

**接口地址**: `POST /processing/seamless`

**描述**: 将图案转换为四方连续的打印图案

**算力消耗**: 60算力

**请求参数**:
- **Form Data**:
  - `image`: 图片文件（必填）
  - `options`: JSON字符串（可选）

**options参数**:
```json
{
  "removeBackground": true,  // 去重叠区（默认true）
  "seamlessLoop": true      // 无缝循环（默认true）
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "taskId": "task_seamless_123456789",
    "status": "processing",
    "estimatedTime": 120,        // 预计处理时间（秒）
    "creditsUsed": 60,
    "createdAt": "2023-12-01T10:00:00Z"
  },
  "message": "任务创建成功，正在处理中"
}
```

### 2. AI矢量化(转SVG)

**接口地址**: `POST /processing/vectorize`

**描述**: 将图片转换为SVG矢量图

**算力消耗**: 100算力

**请求参数**:
- **Form Data**:
  - `image`: 图片文件（必填）
  - `options`: JSON字符串（可选）

**options参数**:
```json
{
  "outputStyle": "vector",     // 输出风格：vector|seamless
  "outputRatio": "1:1"        // 输出比例：1:1|2:3|3:2
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "taskId": "task_vectorize_123456789",
    "status": "processing",
    "estimatedTime": 180,
    "creditsUsed": 100,
    "createdAt": "2023-12-01T10:00:00Z"
  },
  "message": "矢量化任务创建成功"
}
```

### 3. AI提取花型

**接口地址**: `POST /processing/extract-pattern`

**描述**: 提取图案中的花型元素

**算力消耗**: 100算力

**请求参数**:
- **Form Data**:
  - `image`: 图片文件（必填）
  - `options`: JSON字符串（可选）

**options参数**:
```json
{
  "preprocessing": true,       // 预处理图片
  "voiceControl": true,        // 语音控制
  "patternType": "floral"      // 花型类型：floral|geometric|abstract
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "taskId": "task_extract_pattern_123456789",
    "status": "processing",
    "estimatedTime": 200,
    "creditsUsed": 100,
    "createdAt": "2023-12-01T10:00:00Z"
  },
  "message": "花型提取任务创建成功"
}
```

### 4. AI智能去水印

**接口地址**: `POST /processing/remove-watermark`

**描述**: 去除文字和Logo水印

**算力消耗**: 70算力

**请求参数**:
- **Form Data**:
  - `image`: 图片文件（必填）
  - `options`: JSON字符串（可选）

**options参数**:
```json
{
  "watermarkType": "auto",     // 水印类型：auto|text|logo|transparent
  "preserveDetail": true       // 保留细节
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "taskId": "task_watermark_removal_123456789",
    "status": "processing",
    "estimatedTime": 90,
    "creditsUsed": 70,
    "createdAt": "2023-12-01T10:00:00Z"
  },
  "message": "去水印任务创建成功"
}
```

### 5. AI布纹去噪

**接口地址**: `POST /processing/denoise`

**描述**: 去除噪点和布纹

**算力消耗**: 80算力

**请求参数**:
- **Form Data**:
  - `image`: 图片文件（必填）
  - `options`: JSON字符串（可选）

**options参数**:
```json
{
  "noiseType": "fabric",       // 噪音类型：fabric|noise|blur
  "enhanceMode": "standard"    // 增强模式：standard|vector_redraw
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "taskId": "task_denoise_123456789",
    "status": "processing",
    "estimatedTime": 120,
    "creditsUsed": 80,
    "createdAt": "2023-12-01T10:00:00Z"
  },
  "message": "去噪任务创建成功"
}
```

### 6. AI毛线刺绣增强

**接口地址**: `POST /processing/embroidery`

**描述**: 毛线刺绣效果处理

**算力消耗**: 90算力

**请求参数**:
- **Form Data**:
  - `image`: 图片文件（必填）
  - `options`: JSON字符串（可选）

**options参数**:
```json
{
  "needleType": "medium",      // 针线类型：fine|medium|thick
  "stitchDensity": "medium",   // 针脚密度：low|medium|high
  "enhanceDetails": true       // 增强细节纹理
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "taskId": "task_embroidery_123456789",
    "status": "processing",
    "estimatedTime": 160,
    "creditsUsed": 90,
    "createdAt": "2023-12-01T10:00:00Z"
  },
  "message": "刺绣增强任务创建成功"
}
```

## 任务管理接口

### 7. 查询任务状态

**接口地址**: `GET /processing/status/{taskId}`

**描述**: 查询处理任务的当前状态

**路径参数**:
- `taskId`: 任务ID

**响应示例**:
```json
{
  "success": true,
  "data": {
    "taskId": "task_seamless_123456789",
    "status": "completed",       // 状态：queued|processing|completed|failed
    "progress": 100,            // 进度百分比
    "estimatedTime": 0,         // 剩余时间
    "result": {
      "originalImage": "https://cdn.loom-ai.com/originals/abc123.jpg",
      "processedImage": "https://cdn.loom-ai.com/results/def456.png",
      "fileSize": 2048576,      // 文件大小（字节）
      "dimensions": {
        "width": 1024,
        "height": 1024
      }
    },
    "createdAt": "2023-12-01T10:00:00Z",
    "completedAt": "2023-12-01T10:02:30Z"
  },
  "message": "任务已完成"
}
```

### 8. 下载处理结果

**接口地址**: `GET /processing/result/{taskId}/download`

**描述**: 下载处理完成的图片

**路径参数**:
- `taskId`: 任务ID

**查询参数**:
- `format`: 输出格式（png|jpg|svg）（可选，默认png）

**响应**: 直接返回图片文件流

### 9. 获取任务列表

**接口地址**: `GET /processing/tasks`

**描述**: 获取用户的处理任务列表

**查询参数**:
- `status`: 过滤状态（可选）
- `type`: 处理类型（可选）
- `page`: 页码（默认1）
- `limit`: 每页数量（默认10，最大100）

**响应示例**:
```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "taskId": "task_seamless_123456789",
        "type": "seamless",
        "status": "completed",
        "creditsUsed": 60,
        "createdAt": "2023-12-01T10:00:00Z",
        "completedAt": "2023-12-01T10:02:30Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 156,
      "totalPages": 16
    }
  },
  "message": "获取任务列表成功"
}
```

### 10. 删除任务

**接口地址**: `DELETE /processing/task/{taskId}`

**描述**: 删除指定的处理任务

**路径参数**:
- `taskId`: 任务ID

**响应示例**:
```json
{
  "success": true,
  "data": null,
  "message": "任务删除成功"
}
```

## 批量操作接口

### 11. 批量下载

**接口地址**: `POST /processing/batch-download`

**描述**: 批量下载多个处理结果

**请求参数**:
```json
{
  "taskIds": [
    "task_seamless_123456789",
    "task_vectorize_987654321"
  ],
  "format": "zip"              // 打包格式：zip|tar
}
```

**响应**: 返回压缩包文件流

## 任务状态说明

| 状态 | 说明 |
|------|------|
| `queued` | 任务已排队，等待处理 |
| `processing` | 任务正在处理中 |
| `completed` | 任务处理完成 |
| `failed` | 任务处理失败 |

## 文件格式支持

### 输入格式
- PNG, JPG, JPEG, GIF, BMP
- 最大文件大小：15MB
- 推荐分辨率：1024-3000px

### 输出格式
- 标准处理：PNG（透明背景）, JPG
- 矢量化：SVG, PNG, PDF
- 压缩包：ZIP, TAR

## 错误码说明

| 错误码 | 说明 |
|-------|------|
| P001 | 图片文件不能为空 |
| P002 | 不支持的图片格式 |
| P003 | 图片文件过大 |
| P004 | 算力不足 |
| P005 | 任务不存在 |
| P006 | 任务处理失败 |
| P007 | 参数格式错误 |
| P008 | 图片分辨率过低 |
| P009 | 服务器处理异常 |
