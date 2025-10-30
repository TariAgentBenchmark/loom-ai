# LoomAI Backend

LoomAI 后端API服务，提供AI图案处理功能。

## 🚀 快速开始

### 环境要求

- Python 3.11+
- uv (Python包管理器)
- Redis (可选，用于任务队列)

### 安装和启动

1. **安装uv包管理器**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **克隆项目并进入目录**:
```bash
cd backend
```

3. **运行启动脚本**:
```bash
chmod +x start.sh
./start.sh
```

或者手动执行：

```bash
# 创建虚拟环境
uv venv

# 安装依赖
uv pip install -e .

# 配置环境变量
cp env.example .env
# 编辑 .env 文件，配置必要的API密钥

# 初始化数据库
uv run python -c "from app.core.database import init_db; init_db()"

# 启动服务
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 访问地址

- **API服务**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## ⚙️ 配置说明

### 环境变量配置

复制 `env.example` 为 `.env` 并配置以下关键变量：

```bash
# 必须配置
SECRET_KEY=your-secret-key-here
APIYI_API_KEY=your-apiyi-api-key-here
GQCH_API_KEY=your-gqch-api-key-here

# 可选配置
DATABASE_URL=sqlite:///./loom_ai.db
REDIS_URL=redis://localhost:6379/0
```

### API密钥获取

- **Apyi API**: 在 https://api.apiyi.com 获取API密钥
- 支持GPT-4o图像生成和Gemini-2.5-flash-image处理
- 支持OpenAI兼容的图像编辑和对话功能

## 🎯 核心功能

### AI图片处理功能

| 功能 | 端点 | 算力消耗 | 说明 |
|------|------|----------|------|
| AI四方连续转换 | `POST /v1/processing/seamless` | 60 | 矩形图转四方连续 |
| AI矢量化 | `POST /v1/processing/vectorize` | 100 | 图片转SVG矢量图 |
| AI提取花型 | `POST /v1/processing/extract-pattern` | 100 | 花型元素提取 |
| AI智能去水印 | `POST /v1/processing/remove-watermark` | 70 | 水印去除 |
| AI布纹去噪 | `POST /v1/processing/denoise` | 80 | 噪点布纹清理 |
| AI毛线刺绣增强 | `POST /v1/processing/embroidery` | 90 | 刺绣效果处理 |

### 支撑功能

- **用户认证**: 注册、登录、Token管理
- **算力系统**: 余额管理、消耗记录、转赠功能
- **文件管理**: 上传、存储、下载
- **历史记录**: 处理历史、收藏管理
- **支付系统**: 套餐购买、订单管理

## 📁 项目结构

```
backend/
├── app/
│   ├── api/                 # API路由
│   │   ├── v1/             # API v1版本
│   │   │   ├── auth.py     # 认证相关
│   │   │   ├── processing.py # 图片处理
│   │   │   ├── credits.py  # 算力管理
│   │   │   └── ...
│   │   ├── dependencies.py # 依赖注入
│   │   └── routes.py       # 路由汇总
│   ├── core/               # 核心配置
│   │   ├── config.py       # 应用配置
│   │   └── database.py     # 数据库配置
│   ├── models/             # 数据模型
│   │   ├── user.py         # 用户模型
│   │   ├── task.py         # 任务模型
│   │   ├── credit.py       # 算力模型
│   │   └── payment.py      # 支付模型
│   ├── schemas/            # Pydantic模式
│   ├── services/           # 业务逻辑
│   │   ├── ai_client.py    # AI服务客户端
│   │   ├── auth_service.py # 认证服务
│   │   ├── processing_service.py # 处理服务
│   │   ├── credit_service.py # 算力服务
│   │   └── file_service.py # 文件服务
│   └── main.py            # 应用入口
├── uploads/               # 文件上传目录
├── tests/                # 测试文件
├── pyproject.toml        # 项目配置
├── env.example           # 环境变量示例
└── start.sh             # 启动脚本
```

## 🔧 开发说明

### 数据库

- 默认使用SQLite，适合开发和小规模部署
- 生产环境建议使用PostgreSQL
- 自动创建表结构，无需手动建表

### AI服务集成

- **GPT-4o**: 用于图像生成和复杂处理
- **Gemini-2.5-flash-image**: 用于图像编辑和分析
- 支持异步处理，提高响应速度

### 文件存储

- 本地存储：适合开发环境
- 支持AWS S3：适合生产环境
- 自动生成缩略图和预览

### 任务队列

- 使用Celery + Redis实现异步任务处理
- 支持任务状态查询和进度跟踪
- 自动重试和错误处理

## 🧪 测试

```bash
# 运行测试
uv run pytest

# 运行特定测试
uv run pytest tests/test_auth.py

# 生成测试报告
uv run pytest --cov=app --cov-report=html
```

## 📖 API文档

详细的API文档请查看 `docs/api/` 目录：

- [API总览](../docs/api/README.md)
- [认证管理](../docs/api/auth.md)
- [图片处理](../docs/api/processing.md)
- [算力管理](../docs/api/credits.md)
- [用户管理](../docs/api/user.md)
- [支付管理](../docs/api/payment.md)
- [历史记录](../docs/api/history.md)

## 🚀 部署

### Docker部署

```bash
# 构建镜像
docker build -t loom-ai-backend .

# 运行容器
docker run -p 8000:8000 -e TUZI_API_KEY=your-key loom-ai-backend
```

### 生产环境配置

1. 使用PostgreSQL数据库
2. 配置Redis用于任务队列
3. 使用AWS S3存储文件
4. 配置HTTPS和域名
5. 设置监控和日志

## 🔍 监控和日志

- 健康检查端点：`GET /health`
- 日志级别可通过环境变量配置
- 支持结构化日志输出

## 🛠️ 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查DATABASE_URL配置
   - 确保数据库服务正在运行

2. **AI API调用失败**
   - 检查TUZI_API_KEY是否正确
   - 确认网络连接正常

3. **文件上传失败**
   - 检查uploads目录权限
   - 确认磁盘空间充足

4. **Redis连接失败**
   - 检查REDIS_URL配置
   - 确保Redis服务正在运行

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log
```

## 📞 技术支持

- **GitHub Issues**: 提交bug报告和功能请求
- **技术支持**: tech@loom-ai.com
- **API问题**: api@loom-ai.com

---

**版本**: v1.0.0  
**最后更新**: 2023-12-01
