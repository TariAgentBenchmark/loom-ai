# 集成测试

本目录包含项目的集成测试脚本，用于验证各种功能的完整性。

## 测试脚本说明

### API测试脚本
- `test_api.py` - 基础API功能测试
- `test_admin_auth.py` - 管理员认证功能测试
- `test_admin_endpoints.py` - 管理员端点测试

### 美图API测试脚本
- `test_meitu_api.py` - 美图去水印功能测试
- `test_meitu_upscale.py` - 美图高清放大功能测试

## 运行测试

### 前置条件
1. 确保后端服务正在运行
2. 设置必要的环境变量（特别是美图API的密钥）
3. 安装所有依赖包

### 运行单个测试
```bash
# 进入backend目录
cd backend

# 运行API测试
python tests/integration/test_api.py

# 运行管理员认证测试
python tests/integration/test_admin_auth.py

# 运行美图API测试（需要设置MEITU_API_KEY和MEITU_API_SECRET）
python tests/integration/test_meitu_api.py
python tests/integration/test_meitu_upscale.py
```

### 运行pytest测试
```bash
# 运行管理员端点测试（使用pytest）
pytest tests/integration/test_admin_endpoints.py
```

## 环境变量配置

对于美图API测试，需要设置以下环境变量：
- `MEITU_API_KEY` - 美图API密钥
- `MEITU_API_SECRET` - 美图API密钥

可以通过以下方式设置：
1. 在`.env`文件中添加
2. 在运行时导出环境变量
3. 在docker-compose.yml中配置

## 注意事项

1. 这些测试脚本会创建真实的测试数据，请在测试环境中运行
2. 美图API测试需要有效的API密钥，并且可能会产生费用
3. 管理员测试会创建测试用户和订单数据
4. 建议在运行测试前备份数据库
