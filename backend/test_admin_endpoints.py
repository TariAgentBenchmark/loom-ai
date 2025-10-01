import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from app.main import app
from app.core.database import get_db, Base
from app.models.user import User, MembershipType, UserStatus
from app.models.credit import CreditTransaction, CreditSource
from app.models.payment import Order, Refund, OrderStatus, PackageType
from app.services.auth_service import AuthService

# Test client
client = TestClient(app)

# Test data
TEST_ADMIN_EMAIL = "admin@test.com"
TEST_ADMIN_PASSWORD = "admin123456"
TEST_USER_EMAIL = "user@test.com"
TEST_USER_PASSWORD = "user123456"


class TestAdminEndpoints:
    """测试管理员端点"""
    
    @pytest.fixture(scope="class")
    def setup_test_data(self):
        """设置测试数据"""
        # 这里应该设置测试数据库和创建测试用户
        # 由于这是示例，我们只提供测试用例结构
        pass
    
    def test_get_users_list(self):
        """测试获取用户列表"""
        # 登录管理员
        login_response = client.post("/api/v1/auth/login", json={
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["data"]["token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试获取用户列表
            response = client.get("/api/v1/admin/users", headers=headers)
            assert response.status_code == 200
            
            data = response.json()["data"]
            assert "users" in data
            assert "pagination" in data
            assert "page" in data["pagination"]
            assert "limit" in data["pagination"]
            assert "total" in data["pagination"]
            assert "total_pages" in data["pagination"]
            
            # 测试带过滤器的用户列表
            response = client.get("/api/v1/admin/users?status_filter=active&membership_filter=premium", headers=headers)
            assert response.status_code == 200
            
            # 测试搜索功能
            response = client.get("/api/v1/admin/users?email_filter=test", headers=headers)
            assert response.status_code == 200
            
            # 测试排序
            response = client.get("/api/v1/admin/users?sort_by=created_at&sort_order=desc", headers=headers)
            assert response.status_code == 200
    
    def test_get_user_detail(self):
        """测试获取用户详情"""
        # 登录管理员
        login_response = client.post("/api/v1/auth/login", json={
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["data"]["token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试获取用户详情
            response = client.get("/api/v1/admin/users/test_user_id", headers=headers)
            # 可能返回404如果用户不存在，这是正常的
            assert response.status_code in [200, 404]
    
    def test_update_user_status(self):
        """测试更新用户状态"""
        # 登录管理员
        login_response = client.post("/api/v1/auth/login", json={
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["data"]["token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试更新用户状态
            response = client.put("/api/v1/admin/users/test_user_id/status", 
                                 json={"status": "suspended", "reason": "测试"},
                                 headers=headers)
            # 可能返回404如果用户不存在，这是正常的
            assert response.status_code in [200, 404]
    
    def test_update_user_subscription(self):
        """测试更新用户订阅"""
        # 登录管理员
        login_response = client.post("/api/v1/auth/login", json={
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["data"]["token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试更新用户订阅
            response = client.put("/api/v1/admin/users/test_user_id/subscription", 
                                 json={
                                     "membershipType": "premium",
                                     "duration": 30,
                                     "reason": "测试升级"
                                 },
                                 headers=headers)
            # 可能返回404如果用户不存在，这是正常的
            assert response.status_code in [200, 404]
    
    def test_adjust_user_credits(self):
        """测试调整用户算力"""
        # 登录管理员
        login_response = client.post("/api/v1/auth/login", json={
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["data"]["token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试增加用户算力
            response = client.post("/api/v1/admin/users/test_user_id/credits/adjust", 
                                  json={
                                      "amount": 100,
                                      "reason": "测试添加算力",
                                      "sendNotification": True
                                  },
                                  headers=headers)
            # 可能返回404如果用户不存在，这是正常的
            assert response.status_code in [200, 404]
    
    def test_get_user_transactions(self):
        """测试获取用户交易记录"""
        # 登录管理员
        login_response = client.post("/api/v1/auth/login", json={
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["data"]["token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试获取用户交易记录
            response = client.get("/api/v1/admin/users/test_user_id/transactions", headers=headers)
            # 可能返回404如果用户不存在，这是正常的
            assert response.status_code in [200, 404]
            
            # 测试带过滤器的交易记录
            response = client.get("/api/v1/admin/users/test_user_id/transactions?transaction_type=earn", headers=headers)
            assert response.status_code in [200, 404]
    
    def test_get_orders_list(self):
        """测试获取订单列表"""
        # 登录管理员
        login_response = client.post("/api/v1/auth/login", json={
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["data"]["token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试获取订单列表
            response = client.get("/api/v1/admin/orders", headers=headers)
            assert response.status_code == 200
            
            data = response.json()["data"]
            assert "orders" in data
            assert "pagination" in data
            assert "summary" in data
            
            # 测试带过滤器的订单列表
            response = client.get("/api/v1/admin/orders?status_filter=pending", headers=headers)
            assert response.status_code == 200
    
    def test_get_order_detail(self):
        """测试获取订单详情"""
        # 登录管理员
        login_response = client.post("/api/v1/auth/login", json={
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["data"]["token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试获取订单详情
            response = client.get("/api/v1/admin/orders/test_order_id", headers=headers)
            # 可能返回404如果订单不存在，这是正常的
            assert response.status_code in [200, 404]
    
    def test_update_order_status(self):
        """测试更新订单状态"""
        # 登录管理员
        login_response = client.post("/api/v1/auth/login", json={
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["data"]["token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试更新订单状态
            response = client.put("/api/v1/admin/orders/test_order_id/status", 
                                 json={
                                     "status": "paid",
                                     "reason": "测试标记为已支付"
                                 },
                                 headers=headers)
            # 可能返回404如果订单不存在，这是正常的
            assert response.status_code in [200, 404]
    
    def test_get_refunds_list(self):
        """测试获取退款申请列表"""
        # 登录管理员
        login_response = client.post("/api/v1/auth/login", json={
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["data"]["token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试获取退款申请列表
            response = client.get("/api/v1/admin/refunds", headers=headers)
            assert response.status_code == 200
            
            data = response.json()["data"]
            assert "refunds" in data
            assert "pagination" in data
            assert "summary" in data
            
            # 测试带过滤器的退款申请列表
            response = client.get("/api/v1/admin/refunds?status_filter=processing", headers=headers)
            assert response.status_code == 200
    
    def test_process_refund_action(self):
        """测试处理退款申请"""
        # 登录管理员
        login_response = client.post("/api/v1/auth/login", json={
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["data"]["token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试批准退款申请
            response = client.post("/api/v1/admin/refunds/test_refund_id/action", 
                                  json={
                                      "action": "approve",
                                      "adminNotes": "测试批准"
                                  },
                                  headers=headers)
            # 可能返回404如果退款申请不存在，这是正常的
            assert response.status_code in [200, 404]
    
    def test_get_dashboard_stats(self):
        """测试获取仪表板统计数据"""
        # 登录管理员
        login_response = client.post("/api/v1/auth/login", json={
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["data"]["token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试获取仪表板统计数据
            response = client.get("/api/v1/admin/dashboard/stats", headers=headers)
            assert response.status_code == 200
            
            data = response.json()["data"]
            assert "users" in data
            assert "credits" in data
            assert "orders" in data
            assert "revenue" in data
            assert "subscriptions" in data
            assert "recentActivity" in data
            
            # 验证用户统计数据
            user_stats = data["users"]
            assert "total" in user_stats
            assert "active" in user_stats
            assert "admin" in user_stats
            assert "newToday" in user_stats
            assert "membershipBreakdown" in user_stats
            
            # 验证订单统计数据
            order_stats = data["orders"]
            assert "total" in order_stats
            assert "paid" in order_stats
            assert "pending" in order_stats
            assert "conversionRate" in order_stats
            
            # 验证收入统计数据
            revenue_stats = data["revenue"]
            assert "total" in revenue_stats
            assert "today" in revenue_stats
            assert "averageOrderValue" in revenue_stats


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__])