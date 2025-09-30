# 文件上传规范

## 概述

本文档规定了LoomAI API中文件上传的标准和最佳实践。

## 支持的文件类型

### 图片文件

| 格式 | 扩展名 | MIME类型 | 最大尺寸 | 说明 |
|------|--------|----------|----------|------|
| PNG | .png | image/png | 50MB | 支持透明背景，推荐 |
| JPEG | .jpg, .jpeg | image/jpeg | 50MB | 压缩率高，适合照片 |
| GIF | .gif | image/gif | 50MB | 支持动画（仅处理第一帧） |
| BMP | .bmp | image/bmp | 50MB | 无损格式 |
| WebP | .webp | image/webp | 50MB | 现代格式，高压缩率 |

### 其他文件（特定接口）

| 格式 | 扩展名 | MIME类型 | 最大尺寸 | 用途 |
|------|--------|----------|----------|------|
| PDF | .pdf | application/pdf | 20MB | 文档处理 |
| SVG | .svg | image/svg+xml | 10MB | 矢量图输入 |

## 上传限制

### 文件大小限制

- **单个文件**: 最大50MB
- **批量上传**: 总大小不超过200MB
- **头像文件**: 最大5MB

### 图片分辨率限制

- **最小分辨率**: 256x256px
- **推荐分辨率**: 1024-4096px
- **最大分辨率**: 8192x8192px
- **宽高比**: 建议在1:4到4:1之间

### 数量限制

- **单次上传**: 最多10个文件
- **并发上传**: 最多5个并发请求
- **每日上传**: 个人用户1000次，企业用户10000次

## 上传方式

### 1. 表单上传 (multipart/form-data)

**适用场景**: 单文件或少量文件上传

```http
POST /processing/seamless
Content-Type: multipart/form-data
Authorization: Bearer your-token

------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="image"; filename="pattern.jpg"
Content-Type: image/jpeg

[二进制文件数据]
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="options"

{"removeBackground": true, "seamlessLoop": true}
------WebKitFormBoundary7MA4YWxkTrZu0gW--
```

### 2. Base64编码上传

**适用场景**: 小文件或需要在JSON中传输

```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
  "filename": "pattern.jpg",
  "options": {
    "removeBackground": true,
    "seamlessLoop": true
  }
}
```

**限制**: Base64编码会增加约33%的大小，建议仅用于小于10MB的文件。

### 3. 分片上传

**适用场景**: 大文件上传，网络不稳定的情况

#### 步骤1: 初始化分片上传

```http
POST /upload/init
Content-Type: application/json
Authorization: Bearer your-token

{
  "filename": "large_image.png",
  "filesize": 52428800,
  "filetype": "image/png",
  "chunks": 10
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "uploadId": "upload_123456789",
    "chunkSize": 5242880,
    "uploadUrls": [
      "https://api.loom-ai.com/upload/chunk/upload_123456789/1",
      "https://api.loom-ai.com/upload/chunk/upload_123456789/2",
      ...
    ]
  }
}
```

#### 步骤2: 上传分片

```http
PUT /upload/chunk/upload_123456789/1
Content-Type: application/octet-stream
Content-Length: 5242880

[分片二进制数据]
```

#### 步骤3: 完成上传

```http
POST /upload/complete
Content-Type: application/json
Authorization: Bearer your-token

{
  "uploadId": "upload_123456789",
  "chunks": [
    {"number": 1, "etag": "abc123"},
    {"number": 2, "etag": "def456"},
    ...
  ]
}
```

### 4. 预签名URL上传

**适用场景**: 客户端直接上传到云存储

#### 步骤1: 获取预签名URL

```http
POST /upload/presigned
Content-Type: application/json
Authorization: Bearer your-token

{
  "filename": "pattern.jpg",
  "filetype": "image/jpeg",
  "filesize": 1048576
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "uploadUrl": "https://cdn.loom-ai.com/upload/signed-url",
    "fileId": "file_123456789",
    "expiresIn": 3600
  }
}
```

#### 步骤2: 直接上传到URL

```http
PUT https://cdn.loom-ai.com/upload/signed-url
Content-Type: image/jpeg
Content-Length: 1048576

[文件二进制数据]
```

## 上传优化建议

### 文件优化

1. **压缩图片**: 在保证质量的前提下压缩文件大小
2. **选择合适格式**: PNG适合图形，JPEG适合照片
3. **去除元数据**: 清除EXIF等不必要的元数据
4. **调整分辨率**: 根据用途选择合适的分辨率

### 上传策略

1. **并行上传**: 对于多个小文件，使用并行上传
2. **分片上传**: 对于大文件（>10MB），使用分片上传
3. **断点续传**: 实现上传失败后的续传机制
4. **进度反馈**: 提供上传进度反馈给用户

### 错误处理

1. **重试机制**: 实现指数退避的重试策略
2. **校验文件**: 上传前验证文件格式和大小
3. **超时处理**: 设置合理的上传超时时间
4. **用户提示**: 提供清晰的错误提示信息

## 安全考虑

### 文件验证

1. **文件头检查**: 验证文件的magic number
2. **病毒扫描**: 对上传文件进行安全扫描
3. **内容检测**: 检测不当内容（如暴力、色情等）
4. **格式验证**: 严格验证文件格式和结构

### 访问控制

1. **身份认证**: 所有上传都需要有效的访问令牌
2. **权限控制**: 基于用户角色限制上传权限
3. **配额管理**: 限制用户的存储配额和上传频率
4. **IP限制**: 可选的IP白名单机制

## 示例代码

### JavaScript/Node.js

```javascript
// 表单上传
async function uploadFile(file, options) {
  const formData = new FormData();
  formData.append('image', file);
  formData.append('options', JSON.stringify(options));
  
  const response = await fetch('/api/processing/seamless', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  return response.json();
}

// 分片上传
async function chunkedUpload(file) {
  const chunkSize = 5 * 1024 * 1024; // 5MB
  const chunks = Math.ceil(file.size / chunkSize);
  
  // 初始化上传
  const initResponse = await fetch('/api/upload/init', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      filename: file.name,
      filesize: file.size,
      filetype: file.type,
      chunks: chunks
    })
  });
  
  const { uploadId, uploadUrls } = await initResponse.json();
  
  // 上传分片
  const uploadPromises = [];
  for (let i = 0; i < chunks; i++) {
    const start = i * chunkSize;
    const end = Math.min(start + chunkSize, file.size);
    const chunk = file.slice(start, end);
    
    uploadPromises.push(
      fetch(uploadUrls[i], {
        method: 'PUT',
        body: chunk
      })
    );
  }
  
  await Promise.all(uploadPromises);
  
  // 完成上传
  const completeResponse = await fetch('/api/upload/complete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      uploadId: uploadId
    })
  });
  
  return completeResponse.json();
}
```

### Python

```python
import requests

def upload_file(file_path, options, token):
    """表单上传示例"""
    with open(file_path, 'rb') as f:
        files = {'image': f}
        data = {'options': json.dumps(options)}
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.post(
            'https://api.loom-ai.com/v1/processing/seamless',
            files=files,
            data=data,
            headers=headers
        )
        
        return response.json()

def chunked_upload(file_path, token):
    """分片上传示例"""
    chunk_size = 5 * 1024 * 1024  # 5MB
    
    with open(file_path, 'rb') as f:
        file_size = os.path.getsize(file_path)
        chunks = math.ceil(file_size / chunk_size)
        
        # 初始化上传
        init_response = requests.post(
            'https://api.loom-ai.com/v1/upload/init',
            json={
                'filename': os.path.basename(file_path),
                'filesize': file_size,
                'filetype': 'image/jpeg',
                'chunks': chunks
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        upload_data = init_response.json()['data']
        upload_id = upload_data['uploadId']
        upload_urls = upload_data['uploadUrls']
        
        # 上传分片
        for i in range(chunks):
            chunk_data = f.read(chunk_size)
            requests.put(upload_urls[i], data=chunk_data)
        
        # 完成上传
        complete_response = requests.post(
            'https://api.loom-ai.com/v1/upload/complete',
            json={'uploadId': upload_id},
            headers={'Authorization': f'Bearer {token}'}
        )
        
        return complete_response.json()
```

## 常见问题

### Q: 上传失败如何处理？
A: 检查文件格式、大小是否符合要求，网络是否稳定，实现重试机制。

### Q: 如何提高上传速度？
A: 使用分片上传、并行上传，选择就近的上传节点。

### Q: 是否支持断点续传？
A: 分片上传模式支持断点续传，可重新上传失败的分片。

### Q: 上传的文件如何管理？
A: 文件上传后会自动分配文件ID，可通过历史记录API管理文件。

### Q: 文件存储多长时间？
A: 处理结果默认保存30天，会员用户可保存更长时间。
