# LoomAI Backend 快速启动指南

## 🚀 5分钟启动指南

### 1. 安装uv包管理器

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # 或重启终端
```

### 2. 配置环境变量

```bash
cd backend
cp env.example .env
```

编辑 `.env` 文件，至少配置以下变量：
```bash
SECRET_KEY=your-super-secret-key-here
TUZI_API_KEY=your-tuzi-api-key-here
```

### 3. 初始化和启动

```bash
# 方式1: 使用启动脚本（推荐）
chmod +x start.sh
./start.sh

# 方式2: 手动启动
uv venv
uv pip install -e .
python init_db.py
python run_server.py
```

### 4. 验证服务

访问以下地址验证服务是否正常：

- **API服务**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

### 5. 测试API

```bash
# 运行API测试
python test_api.py
```

## 🔑 获取API密钥

### 兔子API密钥

1. 访问 https://api.tu-zi.com
2. 注册账号并获取API密钥
3. 将密钥配置到 `.env` 文件中

## 🎯 核心功能测试

### 用户注册和登录

```bash
# 注册用户
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "confirm_password": "password123",
    "nickname": "测试用户"
  }'

# 用户登录
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 图片处理

```bash
# 获取访问令牌后，处理图片
curl -X POST http://localhost:8000/v1/processing/seamless \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "image=@test_image.jpg" \
  -F "options={\"removeBackground\": true, \"seamlessLoop\": true}"
```

## 🐳 Docker 部署

```bash
# 使用docker-compose启动
docker-compose up -d

# 查看日志
docker-compose logs -f backend

# 停止服务
docker-compose down
```

## 📊 监控和管理

### 查看服务状态

```bash
# 健康检查
curl http://localhost:8000/health

# 查看日志
tail -f logs/app.log
```

### 数据库管理

```bash
# 重新初始化数据库
python init_db.py

# 查看数据库文件
ls -la loom_ai.db
```

## 🛠️ 开发模式

### 启动开发服务器

```bash
# 带自动重载的开发模式
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 运行测试

```bash
# 运行测试
uv run pytest

# 生成覆盖率报告
uv run pytest --cov=app
```

## 🔧 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 查看占用端口的进程
   lsof -i :8000
   
   # 使用其他端口
   uvicorn app.main:app --port 8001
   ```

2. **依赖安装失败**
   ```bash
   # 清理缓存重新安装
   uv cache clean
   uv pip install -e . --no-cache
   ```

3. **数据库权限问题**
   ```bash
   # 确保有写权限
   chmod 755 .
   chmod 644 loom_ai.db
   ```

4. **AI API调用失败**
   - 检查网络连接
   - 验证API密钥是否正确
   - 查看API配额是否充足

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志  
tail -f logs/error.log

# 实时查看所有日志
tail -f logs/*.log
```

## 📞 获取帮助

- **文档**: `docs/api/` 目录下的完整API文档
- **示例**: `test_api.py` 中的API调用示例
- **问题反馈**: 创建GitHub Issue
- **技术支持**: tech@loom-ai.com

---

🎉 **恭喜！LoomAI Backend 已成功启动！**
