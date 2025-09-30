#!/usr/bin/env python3
"""
LoomAI Backend 服务器启动脚本
"""

import uvicorn
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 启动 LoomAI Backend 服务器...")
    print("📍 访问地址: http://localhost:8000")
    print("📖 API文档: http://localhost:8000/docs")
    print("🔍 健康检查: http://localhost:8000/health")
    print()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
