"""
Test configuration settings for admin functionality tests
"""

import os
from typing import Dict, Any

# Test database settings
TEST_DATABASE_URL = "sqlite:///./test.db"
TEST_DATABASE_URL_SYNC = "sqlite:///./test_sync.db"

# Test authentication settings
TEST_ADMIN_EMAIL = "admin@test.com"
TEST_ADMIN_PASSWORD = "admin123456"
TEST_USER_EMAIL = "user@test.com"
TEST_USER_PASSWORD = "user123456"

# Test API settings
TEST_API_BASE_URL = "http://localhost:8000"
TEST_API_V1_PREFIX = "/api/v1"

# Test timeout settings
DEFAULT_TIMEOUT = 30.0
LONG_TIMEOUT = 60.0
SHORT_TIMEOUT = 5.0

# Test pagination settings
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Test data settings
DEFAULT_TEST_CREDITS = 100
ADMIN_TEST_CREDITS = 999999
PREMIUM_TEST_CREDITS = 500

# Test file settings
TEST_IMAGE_SIZE = (512, 512)
TEST_IMAGE_FORMAT = "PNG"
TEST_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Test rate limiting settings
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60  # seconds

# Test security settings
TEST_JWT_SECRET_KEY = "test_secret_key_for_testing_only"
TEST_JWT_ALGORITHM = "HS256"
TEST_ACCESS_TOKEN_EXPIRE_MINUTES = 30
TEST_REFRESH_TOKEN_EXPIRE_DAYS = 7

# Test performance settings
PERFORMANCE_THRESHOLD_SLOW = 1.0  # seconds
PERFORMANCE_THRESHOLD_VERY_SLOW = 2.0  # seconds
LOAD_TEST_CONCURRENT_REQUESTS = 10
LOAD_TEST_TOTAL_REQUESTS = 100

# Test email settings
TEST_EMAIL_FROM = "test@example.com"
TEST_EMAIL_TO = "recipient@example.com"

# Test payment settings
TEST_STRIPE_PUBLIC_KEY = "pk_test_123456789"
TEST_STRIPE_SECRET_KEY = "sk_test_123456789"
TEST_PAYPAL_CLIENT_ID = "test_paypal_client_id"
TEST_PAYPAL_CLIENT_SECRET = "test_paypal_client_secret"

# Test external service settings
TEST_AWS_ACCESS_KEY_ID = "test_aws_access_key"
TEST_AWS_SECRET_ACCESS_KEY = "test_aws_secret_key"
TEST_AWS_REGION = "us-east-1"
TEST_S3_BUCKET = "test-bucket"

# Test logging settings
TEST_LOG_LEVEL = "DEBUG"
TEST_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Test environment settings
TEST_ENVIRONMENT = "testing"
TEST_DEBUG = True

# Test cache settings
TEST_CACHE_TTL = 300  # seconds
TEST_CACHE_MAX_SIZE = 1000

# Test monitoring settings
TEST_METRICS_ENABLED = True
TEST_HEALTH_CHECK_INTERVAL = 30  # seconds

# Test feature flags
TEST_FEATURE_ADMIN_DASHBOARD = True
TEST_FEATURE_USER_MANAGEMENT = True
TEST_FEATURE_ORDER_MANAGEMENT = True
TEST_FEATURE_REFUND_MANAGEMENT = True
TEST_FEATURE_CREDIT_MANAGEMENT = True
TEST_FEATURE_ANALYTICS = True
TEST_FEATURE_NOTIFICATIONS = True

# Test data retention settings
TEST_RETENTION_DAYS = 30
TEST_ARCHIVE_DAYS = 90
TEST_DELETE_DAYS = 365

# Test backup settings
TEST_BACKUP_ENABLED = False
TEST_BACKUP_INTERVAL = 24  # hours
TEST_BACKUP_RETENTION = 7  # days

# Test integration settings
TEST_EMAIL_PROVIDER = "smtp"
TEST_SMS_PROVIDER = "twilio"
TEST_STORAGE_PROVIDER = "local"

# Test security headers
TEST_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'"
}

# Test CORS settings
TEST_CORS_ORIGINS = ["http://localhost:3000", "http://localhost:8080"]
TEST_CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
TEST_CORS_HEADERS = ["*"]

# Test rate limiting by endpoint
RATE_LIMITS = {
    "/api/v1/auth/login": {"requests": 5, "window": 60},
    "/api/v1/auth/register": {"requests": 3, "window": 300},
    "/api/v1/admin/*": {"requests": 100, "window": 60},
    "/api/v1/processing/*": {"requests": 20, "window": 60},
    "/api/v1/credits/*": {"requests": 50, "window": 60}
}

# Test data validation settings
MAX_EMAIL_LENGTH = 255
MAX_NICKNAME_LENGTH = 100
MAX_PASSWORD_LENGTH = 128
MIN_PASSWORD_LENGTH = 8
MAX_REASON_LENGTH = 500
MAX_ADMIN_NOTES_LENGTH = 1000

# Test file upload settings
ALLOWED_IMAGE_FORMATS = ["JPEG", "PNG", "GIF", "BMP", "TIFF"]
MAX_IMAGE_DIMENSION = 4096
MIN_IMAGE_DIMENSION = 32

# Test processing settings
MAX_CONCURRENT_PROCESSES = 5
PROCESSING_TIMEOUT = 300  # seconds
MAX_PROCESSING_RETRIES = 3

# Test notification settings
NOTIFICATION_RETRY_ATTEMPTS = 3
NOTIFICATION_RETRY_DELAY = 5  # seconds
BATCH_NOTIFICATION_SIZE = 100

# Test analytics settings
ANALYTICS_RETENTION_DAYS = 90
ANALYTICS_BATCH_SIZE = 1000
ANALYTICS_PROCESSING_INTERVAL = 3600  # seconds

# Test audit settings
AUDIT_LOG_RETENTION_DAYS = 365
AUDIT_LOG_BATCH_SIZE = 500
AUDIT_LOG_PROCESSING_INTERVAL = 1800  # seconds


class TestConfig:
    """Test configuration class."""
    
    def __init__(self):
        # Database settings
        self.database_url = TEST_DATABASE_URL
        self.database_url_sync = TEST_DATABASE_URL_SYNC
        
        # Authentication settings
        self.admin_email = TEST_ADMIN_EMAIL
        self.admin_password = TEST_ADMIN_PASSWORD
        self.user_email = TEST_USER_EMAIL
        self.user_password = TEST_USER_PASSWORD
        
        # API settings
        self.api_base_url = TEST_API_BASE_URL
        self.api_v1_prefix = TEST_API_V1_PREFIX
        
        # Timeout settings
        self.default_timeout = DEFAULT_TIMEOUT
        self.long_timeout = LONG_TIMEOUT
        self.short_timeout = SHORT_TIMEOUT
        
        # Pagination settings
        self.default_page_size = DEFAULT_PAGE_SIZE
        self.max_page_size = MAX_PAGE_SIZE
        
        # Test data settings
        self.default_test_credits = DEFAULT_TEST_CREDITS
        self.admin_test_credits = ADMIN_TEST_CREDITS
        self.premium_test_credits = PREMIUM_TEST_CREDITS
        
        # File settings
        self.test_image_size = TEST_IMAGE_SIZE
        self.test_image_format = TEST_IMAGE_FORMAT
        self.test_max_file_size = TEST_MAX_FILE_SIZE
        
        # Rate limiting settings
        self.rate_limit_requests = RATE_LIMIT_REQUESTS
        self.rate_limit_window = RATE_LIMIT_WINDOW
        
        # JWT settings
        self.jwt_secret_key = TEST_JWT_SECRET_KEY
        self.jwt_algorithm = TEST_JWT_ALGORITHM
        self.access_token_expire_minutes = TEST_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = TEST_REFRESH_TOKEN_EXPIRE_DAYS
        
        # Performance settings
        self.performance_threshold_slow = PERFORMANCE_THRESHOLD_SLOW
        self.performance_threshold_very_slow = PERFORMANCE_THRESHOLD_VERY_SLOW
        self.load_test_concurrent_requests = LOAD_TEST_CONCURRENT_REQUESTS
        self.load_test_total_requests = LOAD_TEST_TOTAL_REQUESTS
        
        # Environment settings
        self.environment = TEST_ENVIRONMENT
        self.debug = TEST_DEBUG
        
        # Feature flags
        self.features = {
            "admin_dashboard": TEST_FEATURE_ADMIN_DASHBOARD,
            "user_management": TEST_FEATURE_USER_MANAGEMENT,
            "order_management": TEST_FEATURE_ORDER_MANAGEMENT,
            "refund_management": TEST_FEATURE_REFUND_MANAGEMENT,
            "credit_management": TEST_FEATURE_CREDIT_MANAGEMENT,
            "analytics": TEST_FEATURE_ANALYTICS,
            "notifications": TEST_FEATURE_NOTIFICATIONS
        }
        
        # Security settings
        self.security_headers = TEST_SECURITY_HEADERS
        self.cors_origins = TEST_CORS_ORIGINS
        self.cors_methods = TEST_CORS_METHODS
        self.cors_headers = TEST_CORS_HEADERS
        
        # Rate limits by endpoint
        self.rate_limits = RATE_LIMITS
        
        # Data validation settings
        self.max_email_length = MAX_EMAIL_LENGTH
        self.max_nickname_length = MAX_NICKNAME_LENGTH
        self.max_password_length = MAX_PASSWORD_LENGTH
        self.min_password_length = MIN_PASSWORD_LENGTH
        self.max_reason_length = MAX_REASON_LENGTH
        self.max_admin_notes_length = MAX_ADMIN_NOTES_LENGTH
        
        # File upload settings
        self.allowed_image_formats = ALLOWED_IMAGE_FORMATS
        self.max_image_dimension = MAX_IMAGE_DIMENSION
        self.min_image_dimension = MIN_IMAGE_DIMENSION
        
        # Processing settings
        self.max_concurrent_processes = MAX_CONCURRENT_PROCESSES
        self.processing_timeout = PROCESSING_TIMEOUT
        self.max_processing_retries = MAX_PROCESSING_RETRIES
        
        # Notification settings
        self.notification_retry_attempts = NOTIFICATION_RETRY_ATTEMPTS
        self.notification_retry_delay = NOTIFICATION_RETRY_DELAY
        self.batch_notification_size = BATCH_NOTIFICATION_SIZE
        
        # Analytics settings
        self.analytics_retention_days = ANALYTICS_RETENTION_DAYS
        self.analytics_batch_size = ANALYTICS_BATCH_SIZE
        self.analytics_processing_interval = ANALYTICS_PROCESSING_INTERVAL
        
        # Audit settings
        self.audit_log_retention_days = AUDIT_LOG_RETENTION_DAYS
        self.audit_log_batch_size = AUDIT_LOG_BATCH_SIZE
        self.audit_log_processing_interval = AUDIT_LOG_PROCESSING_INTERVAL
    
    def get_rate_limit(self, endpoint: str) -> Dict[str, int]:
        """Get rate limit settings for a specific endpoint."""
        for pattern, limit in self.rate_limits.items():
            if endpoint.startswith(pattern.replace("*", "")):
                return limit
        return {"requests": self.rate_limit_requests, "window": self.rate_limit_window}
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled."""
        return self.features.get(feature, False)
    
    def get_database_url(self, async_mode: bool = True) -> str:
        """Get database URL based on mode."""
        return self.database_url if async_mode else self.database_url_sync
    
    def get_timeout(self, timeout_type: str = "default") -> float:
        """Get timeout based on type."""
        if timeout_type == "short":
            return self.short_timeout
        elif timeout_type == "long":
            return self.long_timeout
        else:
            return self.default_timeout


# Global test configuration instance
test_config = TestConfig()


def get_test_config() -> TestConfig:
    """Get the global test configuration instance."""
    return test_config


def override_test_config(**kwargs) -> TestConfig:
    """Create a test configuration with overridden values."""
    config = TestConfig()
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    return config


def setup_test_environment():
    """Setup the test environment."""
    # Set environment variables
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["SECRET_KEY"] = TEST_JWT_SECRET_KEY
    os.environ["DEBUG"] = str(TEST_DEBUG)
    
    # Configure logging
    import logging
    logging.basicConfig(
        level=getattr(logging, TEST_LOG_LEVEL),
        format=TEST_LOG_FORMAT
    )


def teardown_test_environment():
    """Teardown the test environment."""
    # Clean up environment variables
    os.environ.pop("TESTING", None)
    os.environ.pop("DATABASE_URL", None)
    os.environ.pop("SECRET_KEY", None)
    os.environ.pop("DEBUG", None)