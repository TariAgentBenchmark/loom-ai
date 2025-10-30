import pytest
import asyncio
import os
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db, Base
from app.models.user import User, MembershipType
from app.models.task import TaskType, TaskStatus


# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_jimeng.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖数据库依赖"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def client():
    """创建测试客户端"""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db):
    """创建测试用户"""
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        credits=1000,
        membership_type=MembershipType.FREE
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def db():
    """创建数据库会话"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def auth_headers(test_user):
    """创建认证头"""
    # 模拟JWT token
    return {"Authorization": "Bearer mock_token"}


class TestJimengIntegration:
    """即梦API集成测试类"""
    
    def test_embroidery_endpoint_exists(self, client, auth_headers):
        """测试毛线刺绣增强端点是否存在"""
        response = client.post("/v1/processing/embroidery", headers=auth_headers)
        # 应该返回400错误，因为没有提供图片
        assert response.status_code == 400
    
    @patch('app.services.ai_client.AIClient.enhance_embroidery')
    @patch('app.services.auth_service.AuthService.verify_token')
    def test_embroidery_task_creation(self, mock_auth, mock_enhance, client, db, test_user):
        """测试毛线刺绣增强任务创建（使用即梦API）"""
        # 模拟认证
        mock_auth.return_value = test_user
        
        # 模拟AI客户端返回
        mock_enhance.return_value = "/files/results/test_embroidery.png"
        
        # 创建测试图片
        test_image_content = b"fake_image_content"
        
        # 发送请求
        response = client.post(
            "/v1/processing/embroidery",
            headers={"Authorization": "Bearer valid_token"},
            files={"image": ("test.jpg", test_image_content, "image/jpeg")},
            data={
                "scale": 0.7,
                "size": 2048*2048,
                "force_single": True
            }
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "taskId" in data["data"]
        assert data["data"]["status"] == "queued"
        assert data["data"]["creditsUsed"] > 0
        
        # 验证数据库中的任务
        task = db.query(Task).filter(Task.task_id == data["data"]["taskId"]).first()
        assert task is not None
        assert task.type == TaskType.EMBROIDERY.value
        assert task.status == TaskStatus.QUEUED.value
        assert task.user_id == test_user.id
    
    @patch('app.services.ai_client.AIClient.enhance_embroidery')
    @patch('app.services.auth_service.AuthService.verify_token')
    def test_embroidery_task_processing(self, mock_auth, mock_enhance, client, db, test_user):
        """测试毛线刺绣增强任务处理（使用即梦API）"""
        # 模拟认证
        mock_auth.return_value = test_user
        
        # 模拟AI客户端返回
        mock_enhance.return_value = "/files/results/test_embroidery.png"
        
        # 创建测试图片
        test_image_content = b"fake_image_content"
        
        # 创建任务
        response = client.post(
            "/v1/processing/embroidery",
            headers={"Authorization": "Bearer valid_token"},
            files={"image": ("test.jpg", test_image_content, "image/jpeg")},
            data={
                "scale": 0.7,
                "size": 2048*2048,
                "force_single": True
            }
        )
        
        task_id = response.json()["data"]["taskId"]
        
        # 等待任务处理完成
        import time
        time.sleep(2)
        
        # 检查任务状态
        response = client.get(
            f"/v1/processing/status/{task_id}",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        # 验证任务状态
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] in ["processing", "completed"]
    
    @patch('app.services.auth_service.AuthService.verify_token')
    def test_embroidery_insufficient_credits(self, mock_auth, client, db, test_user):
    """测试积分不足的情况"""
        # 模拟认证
        mock_auth.return_value = test_user
        
    # 将用户积分设置为0
        test_user.credits = 0
        db.commit()
        
        # 创建测试图片
        test_image_content = b"fake_image_content"
        
        # 发送请求
        response = client.post(
            "/v1/processing/embroidery",
            headers={"Authorization": "Bearer valid_token"},
            files={"image": ("test.jpg", test_image_content, "image/jpeg")},
            data={
                "scale": 0.7,
                "size": 2048*2048,
                "force_single": True
            }
        )
        
        # 验证响应
        assert response.status_code == 400
        data = response.json()
    assert "积分不足" in data["detail"]
    
    @patch('app.services.ai_client.AIClient.enhance_embroidery')
    @patch('app.services.auth_service.AuthService.verify_token')
    def test_embroidery_parameters(self, mock_auth, mock_enhance, client, db, test_user):
        """测试毛线刺绣增强参数传递（使用即梦API）"""
        # 模拟认证
        mock_auth.return_value = test_user
        
        # 模拟AI客户端返回
        mock_enhance.return_value = "/files/results/test_embroidery.png"
        
        # 创建测试图片
        test_image_content = b"fake_image_content"
        
        # 发送请求，使用自定义参数
        response = client.post(
            "/v1/processing/embroidery",
            headers={"Authorization": "Bearer valid_token"},
            files={"image": ("test.jpg", test_image_content, "image/jpeg")},
            data={
                "scale": 0.8,
                "size": 4096*4096,
                "force_single": False
            }
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 验证AI客户端被调用时使用了正确的参数
        mock_enhance.assert_called_once()
        call_args = mock_enhance.call_args
        assert call_args[0][0] == test_image_content  # 图片数据
        assert "options" in call_args[1]
        assert call_args[1]["options"]["scale"] == 0.8
        assert call_args[1]["options"]["size"] == 4096*4096
        assert call_args[1]["options"]["force_single"] is False


if __name__ == "__main__":
    pytest.main([__file__])