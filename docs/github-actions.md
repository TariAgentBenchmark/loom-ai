# GitHub Actions Docker 构建工作流

本文档说明如何使用 GitHub Actions 自动构建和推送 Docker 镜像到阿里云容器镜像服务。

## 工作流概述

GitHub Actions 工作流文件位于 [`.github/workflows/docker-build.yml`](../.github/workflows/docker-build.yml)，它实现了以下功能：

- 自动构建前端和后端独立的 Docker 镜像
- 支持多种触发条件和镜像标签策略
- 推送到阿里云容器镜像服务
- 包含安全扫描和构建缓存优化

## 触发条件

工作流支持以下触发条件：

| 触发条件 | 镜像标签 | 推送状态 |
|---------|---------|---------|
| 推送到 `main` 分支 | `latest` | ✅ 推送 |
| 创建 Pull Request | `dev-{pr_number}` | ❌ 仅构建 |
| 创建 Tag (如 `v1.0.0`) | `v1.0.0` | ✅ 推送 |
| 手动触发 | 自定义标签 | ✅ 推送 |

## 镜像信息

- **Registry**: `crpi-lxfoqbwevmx9mc1q.cn-chengdu.personal.cr.aliyuncs.com`
- **Namespace**: `tari_tech`
- **前端镜像**: `loomai`
- **后端镜像**: `loomai-backend`

### 镜像地址示例

- 前端: `crpi-lxfoqbwevmx9mc1q.cn-chengdu.personal.cr.aliyuncs.com/tari_tech/loomai:latest`
- 后端: `crpi-lxfoqbwevmx9mc1q.cn-chengdu.personal.cr.aliyuncs.com/tari_tech/loomai-backend:latest`

## 配置步骤

### 1. 设置 GitHub Secrets

在 GitHub 仓库设置中添加以下 Secrets：

| Secret 名称 | 描述 |
|------------|------|
| `ALIYUN_CR_USERNAME` | 阿里云容器镜像服务用户名 |
| `ALIYUN_CR_PASSWORD` | 阿里云容器镜像服务密码 |

### 2. 验证权限

确保 GitHub Actions 有足够的权限：
1. 进入仓库设置 → Actions → General
2. 在 "Workflow permissions" 中选择 "Read and write permissions"
3. 勾选 "Allow GitHub Actions to create and approve pull requests"

## 使用方法

### 自动触发

1. **推送到 main 分支**
   ```bash
   git push origin main
   ```
   将自动构建并推送 `latest` 标签的镜像

2. **创建 Pull Request**
   ```bash
   # 创建新分支并推送
   git checkout -b feature/new-feature
   git push origin feature/new-feature
   # 在 GitHub 上创建 Pull Request
   ```
   将自动构建 `dev-{pr_number}` 标签的镜像（仅构建，不推送）

3. **创建 Tag**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
   将自动构建并推送 `v1.0.0` 标签的镜像

### 手动触发

1. 进入 GitHub 仓库的 Actions 页面
2. 选择 "Build and Push Docker Images" 工作流
3. 点击 "Run workflow"
4. 输入自定义镜像标签
5. 点击 "Run workflow" 开始构建

## 工作流详情

### 构建流程

1. **确定标签**: 根据触发条件确定镜像标签
2. **并行构建**: 前端和后端镜像并行构建
3. **安全扫描**: 使用 Trivy 扫描镜像安全漏洞
4. **推送镜像**: 将构建好的镜像推送到阿里云容器镜像服务
5. **生成摘要**: 在 GitHub Actions 摘要中显示构建结果

### 构建优化

- **多架构支持**: 支持 `linux/amd64` 和 `linux/arm64` 架构
- **构建缓存**: 使用 GitHub Actions 缓存加速后续构建
- **并行构建**: 前端和后端镜像并行构建，提高效率

### 安全特性

- **权限最小化**: 仅授予必要的权限
- **密钥管理**: 使用 GitHub Secrets 存储敏感信息
- **安全扫描**: 自动扫描镜像中的安全漏洞
- **结果报告**: 将扫描结果上传到 GitHub Security 标签页

## 故障排除

### 常见问题

1. **认证失败**
   - 检查 `ALIYUN_CR_USERNAME` 和 `ALIYUN_CR_PASSWORD` 是否正确
   - 确认阿里云容器镜像服务权限配置

2. **构建失败**
   - 检查 Dockerfile 文件是否正确
   - 查看构建日志中的错误信息

3. **推送失败**
   - 确认镜像仓库是否存在
   - 检查网络连接和防火墙设置

### 查看日志

1. 进入 GitHub 仓库的 Actions 页面
2. 点击对应的工作流运行
3. 查看各个步骤的详细日志

## 本地测试

在推送代码前，可以在本地测试 Docker 构建：

```bash
# 构建前端镜像
docker build -t loomai:local ./frontend

# 构建后端镜像
docker build -t loomai-backend:local ./backend

# 运行容器测试
docker run -p 3000:3000 loomai:local
docker run -p 8000:8000 loomai-backend:local
```

## 使用远程镜像

### Docker Compose 配置

项目已配置为支持使用 GitHub Actions 构建的远程镜像。通过环境变量控制使用哪个版本的镜像：

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，设置所需的镜像标签
# IMAGE_TAG=v1.0.0  # 使用特定版本
# IMAGE_TAG=latest   # 使用最新版本
# IMAGE_TAG=dev-123  # 使用 PR 构建版本
```

### 启动不同版本的服务

```bash
# 使用远程镜像启动生产版本
docker-compose --profile production up -d

# 使用远程镜像启动（等同于 production）
docker-compose --profile remote up -d

# 使用本地构建启动开发版本
docker-compose --profile local up -d

# 默认启动（使用远程镜像）
docker-compose up -d
```

### 环境变量说明

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `REGISTRY` | 阿里云容器镜像服务地址 | `crpi-lxfoqbwevmx9mc1q.cn-chengdu.personal.cr.aliyuncs.com` |
| `NAMESPACE` | 命名空间 | `tari_tech` |
| `FRONTEND_IMAGE` | 前端镜像名称 | `loomai` |
| `BACKEND_IMAGE` | 后端镜像名称 | `loomai-backend` |
| `IMAGE_TAG` | 镜像标签 | `latest` |

### 镜像标签对应关系

| 触发条件 | 镜像标签 | 使用方式 |
|---------|---------|---------|
| main 分支推送 | `latest` | `IMAGE_TAG=latest` |
| Pull Request #123 | `dev-123` | `IMAGE_TAG=dev-123` |
| Tag v1.0.0 | `v1.0.0` | `IMAGE_TAG=v1.0.0` |
| 手动触发 | 自定义标签 | `IMAGE_TAG=your-tag` |

## 更新工作流

如需修改工作流：

1. 编辑 `.github/workflows/docker-build.yml` 文件
2. 提交更改到 main 分支或创建 Pull Request
3. 测试工作流是否正常运行

## 相关文档

- [阿里云容器镜像服务文档](https://help.aliyun.com/zh/acr/user-guide/what-is-acr)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Docker Buildx 文档](https://docs.docker.com/buildx/)