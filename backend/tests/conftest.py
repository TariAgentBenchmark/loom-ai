"""
Pytest configuration and fixtures for admin functionality tests
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Generator, Dict, Any, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.core.database import get_db, Base
from app.models.user import User, MembershipType, UserStatus
from app.models.credit import CreditTransaction, CreditSource, TransactionType
from app.models.payment import Order, Refund, OrderStatus, PackageType, PaymentMethod, Package
from app.services.auth_service import AuthService

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session() -> Generator:
    """Create a fresh database session for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session) -> Generator:
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(db_session) -> Generator:
    """Create an async test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as async_test_client:
        yield async_test_client
    
    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def auth_service() -> AuthService:
    """Create an AuthService instance for testing."""
    return AuthService()


@pytest.fixture
def test_admin_user(db_session) -> User:
    """Create a test admin user."""
    admin_user = User(
        user_id="test_admin_001",
        email="admin@test.com",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.S5uO.G",  # "admin123456"
        nickname="Test Admin",
        is_admin=True,
        status=UserStatus.ACTIVE,
        credits=999999,
        membership_type=MembershipType.ENTERPRISE
    )
    db_session.add(admin_user)
    db_session.commit()
    db_session.refresh(admin_user)
    return admin_user


@pytest.fixture
def test_normal_user(db_session) -> User:
    """Create a test normal user."""
    normal_user = User(
        user_id="test_user_001",
        email="user@test.com",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.S5uO.G",  # "user123456"
        nickname="Test User",
        is_admin=False,
        status=UserStatus.ACTIVE,
        credits=100,
        membership_type=MembershipType.FREE
    )
    db_session.add(normal_user)
    db_session.commit()
    db_session.refresh(normal_user)
    return normal_user


@pytest.fixture
def test_premium_user(db_session) -> User:
    """Create a test premium user."""
    premium_user = User(
        user_id="test_premium_001",
        email="premium@test.com",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.S5uO.G",  # "premium123456"
        nickname="Test Premium",
        is_admin=False,
        status=UserStatus.ACTIVE,
        credits=500,
        membership_type=MembershipType.PREMIUM,
        membership_expiry=datetime.utcnow() + timedelta(days=30)
    )
    db_session.add(premium_user)
    db_session.commit()
    db_session.refresh(premium_user)
    return premium_user


@pytest.fixture
def test_suspended_user(db_session) -> User:
    """Create a test suspended user."""
    suspended_user = User(
        user_id="test_suspended_001",
        email="suspended@test.com",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.S5uO.G",  # "suspended123456"
        nickname="Test Suspended",
        is_admin=False,
        status=UserStatus.SUSPENDED,
        credits=50,
        membership_type=MembershipType.FREE
    )
    db_session.add(suspended_user)
    db_session.commit()
    db_session.refresh(suspended_user)
    return suspended_user


@pytest.fixture
def admin_auth_headers(test_admin_user, auth_service) -> Dict[str, str]:
    """Create authentication headers for admin user."""
    tokens = auth_service.create_admin_login_tokens(test_admin_user)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def user_auth_headers(test_normal_user, auth_service) -> Dict[str, str]:
    """Create authentication headers for normal user."""
    tokens = auth_service.create_login_tokens(test_normal_user)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def test_credit_transactions(db_session, test_normal_user) -> list[CreditTransaction]:
    """Create test credit transactions."""
    transactions = [
        CreditTransaction(
            transaction_id="txn_001",
            user_id=test_normal_user.id,
            type=TransactionType.EARN.value,
            amount=200,
            balance_after=200,
            source=CreditSource.REGISTRATION.value,
            description="Registration bonus",
            created_at=datetime.utcnow() - timedelta(days=5)
        ),
        CreditTransaction(
            transaction_id="txn_002",
            user_id=test_normal_user.id,
            type=TransactionType.SPEND.value,
            amount=-50,
            balance_after=150,
            source=CreditSource.PROCESSING.value,
            description="Image processing",
            created_at=datetime.utcnow() - timedelta(days=3)
        ),
        CreditTransaction(
            transaction_id="txn_003",
            user_id=test_normal_user.id,
            type=TransactionType.EARN.value,
            amount=100,
            balance_after=250,
            source=CreditSource.PURCHASE.value,
            description="Credit purchase",
            created_at=datetime.utcnow() - timedelta(days=1)
        )
    ]
    
    for txn in transactions:
        db_session.add(txn)
    
    db_session.commit()
    return transactions


@pytest.fixture
def test_orders(db_session, test_normal_user, test_premium_user) -> list[Order]:
    """Create test orders."""
    orders = [
        Order(
            order_id="order_001",
            user_id=test_normal_user.id,
            package_id="pkg_basic_001",
            package_name="Basic Credits",
            package_type=PackageType.CREDITS.value,
            original_amount=1000,
            discount_amount=100,
            final_amount=900,
            payment_method=PaymentMethod.STRIPE.value,
            status=OrderStatus.PAID.value,
            credits_amount=100,
            created_at=datetime.utcnow() - timedelta(days=2),
            paid_at=datetime.utcnow() - timedelta(days=2),
            expires_at=datetime.utcnow() + timedelta(days=30)
        ),
        Order(
            order_id="order_002",
            user_id=test_premium_user.id,
            package_id="pkg_premium_001",
            package_name="Premium Membership",
            package_type=PackageType.MEMBERSHIP.value,
            original_amount=3000,
            discount_amount=0,
            final_amount=3000,
            payment_method=PaymentMethod.PAYPAL.value,
            status=OrderStatus.PENDING.value,
            membership_duration=30,
            created_at=datetime.utcnow() - timedelta(days=1),
            expires_at=datetime.utcnow() + timedelta(days=1)
        ),
        Order(
            order_id="order_003",
            user_id=test_normal_user.id,
            package_id="pkg_enterprise_001",
            package_name="Enterprise Credits",
            package_type=PackageType.CREDITS.value,
            original_amount=10000,
            discount_amount=1000,
            final_amount=9000,
            payment_method=PaymentMethod.STRIPE.value,
            status=OrderStatus.REFUNDED.value,
            credits_amount=1000,
            created_at=datetime.utcnow() - timedelta(days=5),
            paid_at=datetime.utcnow() - timedelta(days=5),
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
    ]
    
    for order in orders:
        db_session.add(order)
    
    db_session.commit()
    return orders


@pytest.fixture
def test_refunds(db_session, test_orders) -> list[Refund]:
    """Create test refunds."""
    refunds = [
        Refund(
            refund_id="refund_001",
            order_id=test_orders[2].id,  # REFUNDED order
            user_id=test_orders[2].user_id,
            amount=9000,
            reason="Customer requested refund",
            status="completed",
            created_at=datetime.utcnow() - timedelta(days=4),
            processed_at=datetime.utcnow() - timedelta(days=3),
            completed_at=datetime.utcnow() - timedelta(days=2),
            processed_by=test_orders[2].user_id,
            admin_notes="Refund processed successfully"
        ),
        Refund(
            refund_id="refund_002",
            order_id=test_orders[1].id,  # PENDING order
            user_id=test_orders[1].user_id,
            amount=3000,
            reason="Service not as expected",
            status="processing",
            created_at=datetime.utcnow() - timedelta(hours=12),
            processed_at=datetime.utcnow() - timedelta(hours=6)
        )
    ]
    
    for refund in refunds:
        db_session.add(refund)
    
    db_session.commit()
    return refunds


@pytest.fixture
def sample_image_file():
    """Create a sample image file for testing."""
    import io
    from PIL import Image
    
    # Create a simple test image
    img = Image.new("RGB", (512, 512), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    
    return img_bytes


# Test data generators
def create_test_user_data(
    email: str = "test@example.com",
    password: str = "test123456",
    nickname: str = "Test User",
    is_admin: bool = False
) -> Dict[str, Any]:
    """Generate test user data."""
    return {
        "email": email,
        "password": password,
        "confirm_password": password,
        "nickname": nickname,
        "is_admin": is_admin
    }


def create_test_order_data(
    user_id: int,
    package_type: str = PackageType.CREDITS.value,
    amount: int = 1000,
    status: str = OrderStatus.PENDING.value
) -> Dict[str, Any]:
    """Generate test order data."""
    return {
        "user_id": user_id,
        "package_id": f"pkg_{package_type}_{user_id}",
        "package_name": f"Test {package_type.title()} Package",
        "package_type": package_type,
        "original_amount": amount,
        "discount_amount": 0,
        "final_amount": amount,
        "payment_method": PaymentMethod.STRIPE.value,
        "status": status,
        "credits_amount": amount if package_type == PackageType.CREDITS.value else None,
        "membership_duration": 30 if package_type == PackageType.MEMBERSHIP.value else None
    }


def create_test_refund_data(
    order_id: int,
    user_id: int,
    amount: int = 1000,
    reason: str = "Test refund"
) -> Dict[str, Any]:
    """Generate test refund data."""
    return {
        "order_id": order_id,
        "user_id": user_id,
        "amount": amount,
        "reason": reason,
        "status": "processing"
    }


# Helper functions for testing
async def login_user(client: TestClient, email: str, password: str) -> Dict[str, Any]:
    """Helper function to login a user and return tokens."""
    response = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password
    })
    assert response.status_code == 200
    return response.json()["data"]


async def login_admin(client: TestClient, email: str = "admin@test.com", password: str = "admin123456") -> Dict[str, Any]:
    """Helper function to login an admin and return tokens."""
    response = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password
    })
    assert response.status_code == 200
    return response.json()["data"]


def create_auth_headers(token: str) -> Dict[str, str]:
    """Create authorization headers with the given token."""
    return {"Authorization": f"Bearer {token}"}


def assert_admin_response(response_data: Dict[str, Any]) -> None:
    """Assert that response contains admin session data."""
    assert response_data.get("is_admin") is True
    assert response_data.get("admin_session") is True


def assert_user_response(response_data: Dict[str, Any]) -> None:
    """Assert that response contains user session data."""
    assert response_data.get("is_admin") is False
    assert response_data.get("admin_session") is False


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


def assert_success_response(response_data: Dict[str, Any]) -> None:
    """Assert that response has the standard success format."""
    assert response_data.get("success") is True
    assert "data" in response_data
    assert "message" in response_data
    assert "timestamp" in response_data