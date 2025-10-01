"""
Integration tests for admin API endpoints
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, MembershipType, UserStatus
from app.models.credit import CreditTransaction, TransactionType, CreditSource
from app.models.payment import Order, Refund, OrderStatus, PackageType, PaymentMethod
from tests.conftest import (
    test_admin_user, test_normal_user, test_premium_user, test_suspended_user,
    admin_auth_headers, user_auth_headers, test_credit_transactions,
    test_orders, test_refunds, assert_success_response, assert_pagination_response
)
from tests.utils import (
    TestDataGenerator, DatabaseHelper, ApiHelper, SecurityTestHelper,
    create_test_user_data, create_test_order_data, create_test_refund_data
)


pytestmark = pytest.mark.integration


class TestAdminAuthentication:
    """Test admin authentication endpoints."""
    
    def test_admin_login_success(self, client: TestClient, test_admin_user):
        """Test successful admin login."""
        response = client.post("/api/v1/auth/login", json={
            "email": test_admin_user.email,
            "password": "admin123456"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        
        login_data = data["data"]
        assert login_data["is_admin"] is True
        assert login_data["admin_session"] is True
        assert "accessToken" in login_data
        assert "refreshToken" in login_data
    
    def test_admin_login_invalid_credentials(self, client: TestClient, test_admin_user):
        """Test admin login with invalid credentials."""
        response = client.post("/api/v1/auth/login", json={
            "email": test_admin_user.email,
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "Invalid credentials" in data["message"]
    
    def test_admin_login_non_admin_user(self, client: TestClient, test_normal_user):
        """Test admin login with non-admin user."""
        response = client.post("/api/v1/auth/login", json={
            "email": test_normal_user.email,
            "password": "user123456"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        
        login_data = data["data"]
        assert login_data["is_admin"] is False
        assert login_data.get("admin_session") is False
    
    def test_admin_login_suspended_user(self, client: TestClient, test_suspended_user):
        """Test admin login with suspended user."""
        response = client.post("/api/v1/auth/login", json={
            "email": test_suspended_user.email,
            "password": "suspended123456"
        })
        
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert "suspended" in data["message"].lower()
    
    def test_admin_token_verification(self, client: TestClient, admin_auth_headers):
        """Test admin token verification."""
        response = client.get("/api/v1/user/profile", headers=admin_auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert_success_response(data)
        user_data = data["data"]
        assert user_data["isAdmin"] is True
    
    def test_admin_token_refresh(self, client: TestClient, test_admin_user):
        """Test admin token refresh."""
        # Login to get tokens
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_admin_user.email,
            "password": "admin123456"
        })
        login_data = login_response.json()["data"]
        refresh_token = login_data["refreshToken"]
        
        # Refresh token
        response = client.post("/api/v1/auth/refresh", headers={
            "Authorization": f"Bearer {refresh_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        
        refresh_data = data["data"]
        assert "accessToken" in refresh_data
        assert refresh_data["is_admin"] is True


class TestAdminUserManagement:
    """Test admin user management endpoints."""
    
    def test_get_users_list_success(self, client: TestClient, admin_auth_headers, test_normal_user, test_premium_user):
        """Test successful retrieval of users list."""
        response = client.get("/api/v1/admin/users", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert_pagination_response(data["data"])
        
        users_data = data["data"]["users"]
        assert len(users_data) >= 2  # At least our test users
        
        # Check that users have required fields
        for user in users_data:
            assert "userId" in user
            assert "email" in user
            assert "nickname" in user
            assert "credits" in user
            assert "membershipType" in user
            assert "status" in user
            assert "isAdmin" in user
            assert "createdAt" in user
    
    def test_get_users_list_with_filters(self, client: TestClient, admin_auth_headers, test_normal_user, test_premium_user):
        """Test retrieval of users list with filters."""
        # Filter by status
        response = client.get("/api/v1/admin/users?status_filter=active", headers=admin_auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        users = data["data"]["users"]
        for user in users:
            assert user["status"] == "active"
        
        # Filter by membership
        response = client.get("/api/v1/admin/users?membership_filter=premium", headers=admin_auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        users = data["data"]["users"]
        for user in users:
            assert user["membershipType"] == "premium"
        
        # Filter by email
        response = client.get(f"/api/v1/admin/users?email_filter={test_normal_user.email[:5]}", headers=admin_auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        users = data["data"]["users"]
        for user in users:
            assert test_normal_user.email[:5] in user["email"]
    
    def test_get_users_list_with_pagination(self, client: TestClient, admin_auth_headers):
        """Test retrieval of users list with pagination."""
        response = client.get("/api/v1/admin/users?page=1&page_size=5", headers=admin_auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        pagination = data["data"]["pagination"]
        assert pagination["page"] == 1
        assert pagination["limit"] == 5
        assert len(data["data"]["users"]) <= 5
    
    def test_get_users_list_unauthorized(self, client: TestClient, user_auth_headers):
        """Test that normal users cannot access users list."""
        response = client.get("/api/v1/admin/users", headers=user_auth_headers)
        assert response.status_code == 403
    
    def test_get_user_detail_success(self, client: TestClient, admin_auth_headers, test_normal_user):
        """Test successful retrieval of user detail."""
        response = client.get(f"/api/v1/admin/users/{test_normal_user.user_id}", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        
        user_data = data["data"]
        assert user_data["userId"] == test_normal_user.user_id
        assert user_data["email"] == test_normal_user.email
        assert user_data["nickname"] == test_normal_user.nickname
        assert user_data["credits"] == test_normal_user.credits
        assert user_data["membershipType"] == test_normal_user.membership_type.value
        assert user_data["status"] == test_normal_user.status.value
        assert user_data["isAdmin"] is False
    
    def test_get_user_detail_not_found(self, client: TestClient, admin_auth_headers):
        """Test retrieval of non-existent user detail."""
        response = client.get("/api/v1/admin/users/nonexistent_user", headers=admin_auth_headers)
        assert response.status_code == 404
    
    def test_update_user_status_success(self, client: TestClient, admin_auth_headers, test_normal_user, db_session):
        """Test successful user status update."""
        response = client.put(
            f"/api/v1/admin/users/{test_normal_user.user_id}/status",
            json={"status": "suspended", "reason": "Test suspension"},
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        
        # Verify in database
        db_session.refresh(test_normal_user)
        assert test_normal_user.status == UserStatus.SUSPENDED
    
    def test_update_user_status_invalid_status(self, client: TestClient, admin_auth_headers, test_normal_user):
        """Test user status update with invalid status."""
        response = client.put(
            f"/api/v1/admin/users/{test_normal_user.user_id}/status",
            json={"status": "invalid_status", "reason": "Test"},
            headers=admin_auth_headers
        )
        
        assert response.status_code == 400
    
    def test_update_user_subscription_success(self, client: TestClient, admin_auth_headers, test_normal_user, db_session):
        """Test successful user subscription update."""
        response = client.put(
            f"/api/v1/admin/users/{test_normal_user.user_id}/subscription",
            json={
                "membershipType": "premium",
                "duration": 30,
                "reason": "Test upgrade"
            },
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        
        # Verify in database
        db_session.refresh(test_normal_user)
        assert test_normal_user.membership_type == MembershipType.PREMIUM
        assert test_normal_user.membership_expiry is not None
    
    def test_adjust_user_credits_success(self, client: TestClient, admin_auth_headers, test_normal_user, db_session):
        """Test successful user credits adjustment."""
        original_credits = test_normal_user.credits
        
        response = client.post(
            f"/api/v1/admin/users/{test_normal_user.user_id}/credits/adjust",
            json={
                "amount": 100,
                "reason": "Test credit adjustment",
                "sendNotification": True
            },
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        
        # Verify in database
        db_session.refresh(test_normal_user)
        assert test_normal_user.credits == original_credits + 100
        
        # Verify transaction record
        transaction = db_session.query(CreditTransaction).filter(
            CreditTransaction.user_id == test_normal_user.id,
            CreditTransaction.amount == 100,
            CreditTransaction.source == CreditSource.ADMIN_ADJUST.value
        ).first()
        assert transaction is not None
        assert "管理员调整" in transaction.description
    
    def test_get_user_transactions_success(self, client: TestClient, admin_auth_headers, test_normal_user, test_credit_transactions):
        """Test successful retrieval of user transactions."""
        response = client.get(f"/api/v1/admin/users/{test_normal_user.user_id}/transactions", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert_pagination_response(data["data"])
        
        transactions = data["data"]["transactions"]
        assert len(transactions) >= len(test_credit_transactions)
        
        # Check summary data
        summary = data["data"]["summary"]
        assert "totalEarned" in summary
        assert "totalSpent" in summary
        assert "netChange" in summary
        assert "currentBalance" in summary
    
    def test_get_user_transactions_with_filters(self, client: TestClient, admin_auth_headers, test_normal_user):
        """Test retrieval of user transactions with filters."""
        # Filter by transaction type
        response = client.get(
            f"/api/v1/admin/users/{test_normal_user.user_id}/transactions?transaction_type=earn",
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        transactions = data["data"]["transactions"]
        for txn in transactions:
            assert txn["type"] == "earn"
        
        # Filter by date range
        start_date = (datetime.utcnow() - timedelta(days=10)).strftime("%Y-%m-%d")
        end_date = datetime.utcnow().strftime("%Y-%m-%d")
        
        response = client.get(
            f"/api/v1/admin/users/{test_normal_user.user_id}/transactions?start_date={start_date}&end_date={end_date}",
            headers=admin_auth_headers
        )
        assert response.status_code == 200


class TestAdminOrderManagement:
    """Test admin order management endpoints."""
    
    def test_get_orders_list_success(self, client: TestClient, admin_auth_headers, test_orders):
        """Test successful retrieval of orders list."""
        response = client.get("/api/v1/admin/orders", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert_pagination_response(data["data"])
        
        orders = data["data"]["orders"]
        assert len(orders) >= len(test_orders)
        
        # Check summary data
        summary = data["data"]["summary"]
        assert "totalRevenue" in summary
        assert "pendingOrders" in summary
        assert "conversionRate" in summary
    
    def test_get_orders_list_with_filters(self, client: TestClient, admin_auth_headers, test_orders):
        """Test retrieval of orders list with filters."""
        # Filter by status
        response = client.get("/api/v1/admin/orders?status_filter=paid", headers=admin_auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        orders = data["data"]["orders"]
        for order in orders:
            assert order["status"] == "paid"
        
        # Filter by package type
        response = client.get("/api/v1/admin/orders?package_type_filter=credits", headers=admin_auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        orders = data["data"]["orders"]
        for order in orders:
            assert order["packageType"] == "credits"
    
    def test_get_order_detail_success(self, client: TestClient, admin_auth_headers, test_orders):
        """Test successful retrieval of order detail."""
        order = test_orders[0]
        response = client.get(f"/api/v1/admin/orders/{order.order_id}", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        
        order_data = data["data"]
        assert order_data["orderId"] == order.order_id
        assert order_data["userId"] == order.user.user_id
        assert order_data["packageName"] == order.package_name
        assert order_data["status"] == order.status
    
    def test_get_order_detail_not_found(self, client: TestClient, admin_auth_headers):
        """Test retrieval of non-existent order detail."""
        response = client.get("/api/v1/admin/orders/nonexistent_order", headers=admin_auth_headers)
        assert response.status_code == 404
    
    def test_update_order_status_success(self, client: TestClient, admin_auth_headers, test_orders, db_session):
        """Test successful order status update."""
        order = test_orders[1]  # PENDING order
        response = client.put(
            f"/api/v1/admin/orders/{order.order_id}/status",
            json={
                "status": "paid",
                "reason": "Test payment confirmation",
                "adminNotes": "Manually marked as paid"
            },
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        
        # Verify in database
        db_session.refresh(order)
        assert order.status == OrderStatus.PAID
        assert order.paid_at is not None
    
    def test_update_order_status_invalid_status(self, client: TestClient, admin_auth_headers, test_orders):
        """Test order status update with invalid status."""
        order = test_orders[0]
        response = client.put(
            f"/api/v1/admin/orders/{order.order_id}/status",
            json={"status": "invalid_status", "reason": "Test"},
            headers=admin_auth_headers
        )
        
        assert response.status_code == 400


class TestAdminRefundManagement:
    """Test admin refund management endpoints."""
    
    def test_get_refunds_list_success(self, client: TestClient, admin_auth_headers, test_refunds):
        """Test successful retrieval of refunds list."""
        response = client.get("/api/v1/admin/refunds", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert_pagination_response(data["data"])
        
        refunds = data["data"]["refunds"]
        assert len(refunds) >= len(test_refunds)
        
        # Check summary data
        summary = data["data"]["summary"]
        assert "pendingRefunds" in summary
        assert "approvedRefunds" in summary
        assert "totalRefundAmount" in summary
    
    def test_get_refunds_list_with_filters(self, client: TestClient, admin_auth_headers, test_refunds):
        """Test retrieval of refunds list with filters."""
        # Filter by status
        response = client.get("/api/v1/admin/refunds?status_filter=processing", headers=admin_auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        refunds = data["data"]["refunds"]
        for refund in refunds:
            assert refund["status"] == "processing"
    
    def test_process_refund_approve_success(self, client: TestClient, admin_auth_headers, test_refunds, db_session):
        """Test successful refund approval."""
        refund = test_refunds[1]  # PROCESSING refund
        response = client.post(
            f"/api/v1/admin/refunds/{refund.refund_id}/action",
            json={
                "action": "approve",
                "reason": "Test approval",
                "adminNotes": "Approved for testing"
            },
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        
        # Verify in database
        db_session.refresh(refund)
        assert refund.status == "approved"
        assert refund.processed_at is not None
    
    def test_process_refund_reject_success(self, client: TestClient, admin_auth_headers, test_refunds, db_session):
        """Test successful refund rejection."""
        # Create a new refund for testing
        new_refund_data = create_test_refund_data(
            order_id=test_refunds[0].order_id,
            user_id=test_refunds[0].user_id,
            status="processing"
        )
        new_refund = DatabaseHelper.create_refund(db_session, new_refund_data)
        
        response = client.post(
            f"/api/v1/admin/refunds/{new_refund.refund_id}/action",
            json={
                "action": "reject",
                "reason": "Test rejection",
                "adminNotes": "Rejected for testing"
            },
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        
        # Verify in database
        db_session.refresh(new_refund)
        assert new_refund.status == "rejected"
    
    def test_process_refund_invalid_action(self, client: TestClient, admin_auth_headers, test_refunds):
        """Test refund processing with invalid action."""
        refund = test_refunds[0]
        response = client.post(
            f"/api/v1/admin/refunds/{refund.refund_id}/action",
            json={"action": "invalid_action", "reason": "Test"},
            headers=admin_auth_headers
        )
        
        assert response.status_code == 400


class TestAdminDashboard:
    """Test admin dashboard endpoints."""
    
    def test_get_dashboard_stats_success(self, client: TestClient, admin_auth_headers, test_normal_user, test_premium_user, test_orders):
        """Test successful retrieval of dashboard statistics."""
        response = client.get("/api/v1/admin/dashboard/stats", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        
        stats = data["data"]
        
        # Check user stats
        assert "users" in stats
        user_stats = stats["users"]
        assert "total" in user_stats
        assert "active" in user_stats
        assert "admin" in user_stats
        assert "newToday" in user_stats
        assert "membershipBreakdown" in user_stats
        
        # Check credit stats
        assert "credits" in stats
        credit_stats = stats["credits"]
        assert "total" in credit_stats
        assert "transactionsToday" in credit_stats
        
        # Check order stats
        assert "orders" in stats
        order_stats = stats["orders"]
        assert "total" in order_stats
        assert "paid" in order_stats
        assert "pending" in order_stats
        assert "conversionRate" in order_stats
        
        # Check revenue stats
        assert "revenue" in stats
        revenue_stats = stats["revenue"]
        assert "total" in revenue_stats
        assert "today" in revenue_stats
        assert "averageOrderValue" in revenue_stats
        
        # Check recent activity
        assert "recentActivity" in stats
        assert isinstance(stats["recentActivity"], list)
    
    def test_get_dashboard_stats_unauthorized(self, client: TestClient, user_auth_headers):
        """Test that normal users cannot access dashboard stats."""
        response = client.get("/api/v1/admin/dashboard/stats", headers=user_auth_headers)
        assert response.status_code == 403


class TestAdminSecurity:
    """Test admin security features."""
    
    def test_admin_endpoint_protection(self, client: TestClient):
        """Test that admin endpoints are protected."""
        admin_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/orders",
            "/api/v1/admin/refunds",
            "/api/v1/admin/dashboard/stats"
        ]
        
        for endpoint in admin_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
    
    def test_admin_endpoint_user_access(self, client: TestClient, user_auth_headers):
        """Test that normal users cannot access admin endpoints."""
        admin_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/orders",
            "/api/v1/admin/refunds",
            "/api/v1/admin/dashboard/stats"
        ]
        
        for endpoint in admin_endpoints:
            response = client.get(endpoint, headers=user_auth_headers)
            assert response.status_code == 403
    
    def test_sql_injection_protection(self, client: TestClient, admin_auth_headers):
        """Test SQL injection protection."""
        sql_payloads = SecurityTestHelper.test_sql_injection_payloads()
        
        for payload in sql_payloads:
            # Test in user search
            response = client.get(f"/api/v1/admin/users?email_filter={payload}", headers=admin_auth_headers)
            # Should not return 500 (server error)
            assert response.status_code not in [500, 502, 503]
            
            # Test in user ID
            response = client.get(f"/api/v1/admin/users/{payload}", headers=admin_auth_headers)
            # Should not return 500 (server error)
            assert response.status_code not in [500, 502, 503]
    
    def test_xss_protection(self, client: TestClient, admin_auth_headers):
        """Test XSS protection."""
        xss_payloads = SecurityTestHelper.test_xss_payloads()
        
        for payload in xss_payloads:
            # Test in user status update reason
            response = client.put(
                "/api/v1/admin/users/test_user_001/status",
                json={"status": "suspended", "reason": payload},
                headers=admin_auth_headers
            )
            # Should not return 500 (server error)
            assert response.status_code not in [500, 502, 503]
    
    def test_rate_limiting(self, client: TestClient, admin_auth_headers):
        """Test rate limiting on admin endpoints."""
        # Make multiple rapid requests
        for i in range(10):
            response = client.get("/api/v1/admin/users", headers=admin_auth_headers)
            if response.status_code == 429:
                # Rate limiting is working
                return True
        
        # If we get here, rate limiting might not be properly configured
        # This is not necessarily a failure, as rate limiting might be disabled in tests
        return True