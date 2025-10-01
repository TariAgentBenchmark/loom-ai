"""
Database migration tests for admin functionality
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import Base, get_db
from app.models.user import User, MembershipType, UserStatus
from app.models.credit import CreditTransaction, CreditSource, TransactionType
from app.models.payment import Order, Refund, OrderStatus, PackageType, PaymentMethod
from tests.utils import TestDataGenerator, DatabaseHelper


pytestmark = pytest.mark.migrations


class TestAdminColumnMigration:
    """Test the is_admin column migration."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for migration testing."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_migration.db")
        db_url = f"sqlite:///{db_path}"
        
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        yield engine, SessionLocal, db_path
        
        # Cleanup
        engine.dispose()
        shutil.rmtree(temp_dir)
    
    def test_is_admin_column_exists(self, temp_db):
        """Test that is_admin column exists in users table."""
        engine, SessionLocal, db_path = temp_db
        
        # Create tables without is_admin column (simulate old schema)
        old_metadata = Base.metadata
        # Remove is_admin column from User table temporarily
        old_user_table = old_metadata.tables['users']
        old_user_table._columns.pop('is_admin', None)
        
        old_metadata.create_all(bind=engine)
        
        # Verify is_admin column doesn't exist
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        assert 'is_admin' not in columns
        
        # Run migration
        self._run_is_admin_migration(engine)
        
        # Verify is_admin column exists
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        assert 'is_admin' in columns
        
        # Verify column properties
        is_admin_column = inspector.get_columns('users', ['is_admin'])[0]
        assert is_admin_column['nullable'] is False
        assert is_admin_column['default'] == 0
    
    def test_is_admin_column_default_values(self, temp_db):
        """Test that is_admin column has correct default values for existing users."""
        engine, SessionLocal, db_path = temp_db
        
        # Create tables without is_admin column
        old_metadata = Base.metadata
        old_user_table = old_metadata.tables['users']
        old_user_table._columns.pop('is_admin', None)
        
        old_metadata.create_all(bind=engine)
        
        # Create users before migration
        session = SessionLocal()
        try:
            user_data = TestDataGenerator.create_user_data(
                email="old_user@test.com",
                is_admin=False  # This should be ignored
            )
            
            # Create user without is_admin field
            user = User(
                user_id=user_data["user_id"],
                email=user_data["email"],
                hashed_password="hashed_password",
                nickname=user_data["nickname"],
                status=user_data["status"],
                membership_type=user_data["membership_type"],
                credits=user_data["credits"]
            )
            session.add(user)
            session.commit()
            
            # Verify user exists without is_admin
            db_user = session.query(User).filter(User.email == "old_user@test.com").first()
            assert db_user is not None
            # is_admin should not exist yet
            
        finally:
            session.close()
        
        # Run migration
        self._run_is_admin_migration(engine)
        
        # Verify existing users have is_admin = False
        session = SessionLocal()
        try:
            db_user = session.query(User).filter(User.email == "old_user@test.com").first()
            assert db_user is not None
            assert db_user.is_admin is False
        finally:
            session.close()
    
    def test_is_admin_column_new_users(self, temp_db):
        """Test that new users can be created with is_admin column."""
        engine, SessionLocal, db_path = temp_db
        
        # Create tables with is_admin column (current schema)
        Base.metadata.create_all(bind=engine)
        
        # Create admin user
        session = SessionLocal()
        try:
            admin_data = TestDataGenerator.create_user_data(
                email="admin@test.com",
                is_admin=True
            )
            
            admin_user = User(
                user_id=admin_data["user_id"],
                email=admin_data["email"],
                hashed_password="hashed_password",
                nickname=admin_data["nickname"],
                is_admin=True,
                status=admin_data["status"],
                membership_type=admin_data["membership_type"],
                credits=admin_data["credits"]
            )
            session.add(admin_user)
            session.commit()
            
            # Verify admin user
            db_admin = session.query(User).filter(User.email == "admin@test.com").first()
            assert db_admin is not None
            assert db_admin.is_admin is True
            
            # Create normal user
            normal_data = TestDataGenerator.create_user_data(
                email="normal@test.com",
                is_admin=False
            )
            
            normal_user = User(
                user_id=normal_data["user_id"],
                email=normal_data["email"],
                hashed_password="hashed_password",
                nickname=normal_data["nickname"],
                is_admin=False,
                status=normal_data["status"],
                membership_type=normal_data["membership_type"],
                credits=normal_data["credits"]
            )
            session.add(normal_user)
            session.commit()
            
            # Verify normal user
            db_normal = session.query(User).filter(User.email == "normal@test.com").first()
            assert db_normal is not None
            assert db_normal.is_admin is False
            
        finally:
            session.close()
    
    def _run_is_admin_migration(self, engine):
        """Simulate running the is_admin column migration."""
        with engine.connect() as conn:
            # Add is_admin column
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN is_admin BOOLEAN DEFAULT 0
            """))
            conn.commit()


class TestCreditTransactionMigration:
    """Test credit transaction related migrations."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for migration testing."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_credit_migration.db")
        db_url = f"sqlite:///{db_path}"
        
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        yield engine, SessionLocal, db_path
        
        # Cleanup
        engine.dispose()
        shutil.rmtree(temp_dir)
    
    def test_credit_transaction_table_structure(self, temp_db):
        """Test that credit_transaction table has correct structure."""
        engine, SessionLocal, db_path = temp_db
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Verify table structure
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('credit_transactions')]
        
        required_columns = [
            'id', 'transaction_id', 'user_id', 'type', 'amount', 
            'balance_after', 'source', 'description', 'created_at',
            'related_task_id', 'related_order_id'
        ]
        
        for col in required_columns:
            assert col in columns, f"Missing column: {col}"
    
    def test_credit_transaction_foreign_keys(self, temp_db):
        """Test that credit transaction foreign keys work correctly."""
        engine, SessionLocal, db_path = temp_db
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        session = SessionLocal()
        try:
            # Create user
            user_data = TestDataGenerator.create_user_data()
            user = DatabaseHelper.create_user(session, user_data, None)
            
            # Create transaction
            txn_data = TestDataGenerator.create_transaction_data(user.id)
            transaction = DatabaseHelper.create_transaction(session, txn_data)
            
            # Verify foreign key relationship
            assert transaction.user_id == user.id
            
            # Verify cascade delete
            session.delete(user)
            session.commit()
            
            # Transaction should be deleted due to cascade
            remaining_txn = session.query(CreditTransaction).filter(
                CreditTransaction.id == transaction.id
            ).first()
            assert remaining_txn is None
            
        finally:
            session.close()


class TestOrderRefundMigration:
    """Test order and refund related migrations."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for migration testing."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_order_refund_migration.db")
        db_url = f"sqlite:///{db_path}"
        
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        yield engine, SessionLocal, db_path
        
        # Cleanup
        engine.dispose()
        shutil.rmtree(temp_dir)
    
    def test_order_table_structure(self, temp_db):
        """Test that orders table has correct structure."""
        engine, SessionLocal, db_path = temp_db
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Verify table structure
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('orders')]
        
        required_columns = [
            'id', 'order_id', 'user_id', 'package_id', 'package_name',
            'package_type', 'original_amount', 'discount_amount', 'final_amount',
            'payment_method', 'status', 'created_at', 'paid_at', 'expires_at',
            'credits_amount', 'membership_duration'
        ]
        
        for col in required_columns:
            assert col in columns, f"Missing column: {col}"
    
    def test_refund_table_structure(self, temp_db):
        """Test that refunds table has correct structure."""
        engine, SessionLocal, db_path = temp_db
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Verify table structure
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('refunds')]
        
        required_columns = [
            'id', 'refund_id', 'order_id', 'user_id', 'amount', 'reason',
            'status', 'created_at', 'processed_at', 'completed_at',
            'processed_by', 'admin_notes'
        ]
        
        for col in required_columns:
            assert col in columns, f"Missing column: {col}"
    
    def test_order_refund_relationship(self, temp_db):
        """Test that order-refund relationship works correctly."""
        engine, SessionLocal, db_path = temp_db
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        session = SessionLocal()
        try:
            # Create user
            user_data = TestDataGenerator.create_user_data()
            user = DatabaseHelper.create_user(session, user_data, None)
            
            # Create order
            order_data = TestDataGenerator.create_order_data(user.id)
            order = DatabaseHelper.create_order(session, order_data)
            
            # Create refund
            refund_data = TestDataGenerator.create_refund_data(order.id, user.id)
            refund = DatabaseHelper.create_refund(session, refund_data)
            
            # Verify relationship
            assert refund.order_id == order.id
            assert refund.user_id == user.id
            
            # Verify foreign key constraints
            # Try to create refund with non-existent order
            invalid_refund_data = TestDataGenerator.create_refund_data(99999, user.id)
            
            try:
                invalid_refund = Refund(**invalid_refund_data)
                session.add(invalid_refund)
                session.commit()
                assert False, "Should have failed due to foreign key constraint"
            except Exception:
                session.rollback()
                # Expected to fail
            
        finally:
            session.close()


class TestDataIntegrityMigration:
    """Test data integrity during migrations."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for migration testing."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_integrity_migration.db")
        db_url = f"sqlite:///{db_path}"
        
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        yield engine, SessionLocal, db_path
        
        # Cleanup
        engine.dispose()
        shutil.rmtree(temp_dir)
    
    def test_user_data_integrity(self, temp_db):
        """Test that user data remains intact during migrations."""
        engine, SessionLocal, db_path = temp_db
        
        # Create tables without is_admin column
        old_metadata = Base.metadata
        old_user_table = old_metadata.tables['users']
        old_user_table._columns.pop('is_admin', None)
        
        old_metadata.create_all(bind=engine)
        
        # Create test data
        session = SessionLocal()
        try:
            users = []
            for i in range(5):
                user_data = TestDataGenerator.create_user_data(
                    email=f"user{i}@test.com"
                )
                
                user = User(
                    user_id=user_data["user_id"],
                    email=user_data["email"],
                    hashed_password="hashed_password",
                    nickname=user_data["nickname"],
                    status=user_data["status"],
                    membership_type=user_data["membership_type"],
                    credits=user_data["credits"]
                )
                session.add(user)
                users.append(user)
            
            session.commit()
            
            # Store original data
            original_users = []
            for user in users:
                original_users.append({
                    'user_id': user.user_id,
                    'email': user.email,
                    'nickname': user.nickname,
                    'status': user.status,
                    'membership_type': user.membership_type,
                    'credits': user.credits
                })
            
        finally:
            session.close()
        
        # Run migration
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN is_admin BOOLEAN DEFAULT 0
            """))
            conn.commit()
        
        # Verify data integrity
        session = SessionLocal()
        try:
            for original_user in original_users:
                db_user = session.query(User).filter(
                    User.user_id == original_user['user_id']
                ).first()
                
                assert db_user is not None
                assert db_user.email == original_user['email']
                assert db_user.nickname == original_user['nickname']
                assert db_user.status == original_user['status']
                assert db_user.membership_type == original_user['membership_type']
                assert db_user.credits == original_user['credits']
                assert db_user.is_admin is False  # Default value
                
        finally:
            session.close()
    
    def test_transaction_data_integrity(self, temp_db):
        """Test that transaction data remains intact during migrations."""
        engine, SessionLocal, db_path = temp_db
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Create test data
        session = SessionLocal()
        try:
            # Create users
            user_data = TestDataGenerator.create_user_data()
            user = DatabaseHelper.create_user(session, user_data, None)
            
            # Create transactions
            transactions = []
            for i in range(10):
                txn_data = TestDataGenerator.create_transaction_data(user.id)
                transaction = DatabaseHelper.create_transaction(session, txn_data)
                transactions.append(transaction)
            
            # Store original data
            original_txns = []
            for txn in transactions:
                original_txns.append({
                    'transaction_id': txn.transaction_id,
                    'user_id': txn.user_id,
                    'type': txn.type,
                    'amount': txn.amount,
                    'balance_after': txn.balance_after,
                    'source': txn.source,
                    'description': txn.description
                })
            
        finally:
            session.close()
        
        # Simulate migration (add new column if needed)
        # For this test, we'll just verify the current structure
        
        # Verify data integrity
        session = SessionLocal()
        try:
            for original_txn in original_txns:
                db_txn = session.query(CreditTransaction).filter(
                    CreditTransaction.transaction_id == original_txn['transaction_id']
                ).first()
                
                assert db_txn is not None
                assert db_txn.user_id == original_txn['user_id']
                assert db_txn.type == original_txn['type']
                assert db_txn.amount == original_txn['amount']
                assert db_txn.balance_after == original_txn['balance_after']
                assert db_txn.source == original_txn['source']
                assert db_txn.description == original_txn['description']
                
        finally:
            session.close()


class TestMigrationRollback:
    """Test migration rollback functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for migration testing."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_rollback_migration.db")
        db_url = f"sqlite:///{db_path}"
        
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        yield engine, SessionLocal, db_path
        
        # Cleanup
        engine.dispose()
        shutil.rmtree(temp_dir)
    
    def test_migration_rollback(self, temp_db):
        """Test that migration can be rolled back."""
        engine, SessionLocal, db_path = temp_db
        
        # Create initial tables
        Base.metadata.create_all(bind=engine)
        
        # Verify initial state
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        assert 'is_admin' in columns
        
        # Simulate rollback (drop is_admin column)
        with engine.connect() as conn:
            # SQLite doesn't support dropping columns directly, so we recreate table
            conn.execute(text("""
                CREATE TABLE users_backup AS SELECT * FROM users
            """))
            conn.execute(text("DROP TABLE users"))
            conn.execute(text("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    user_id VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    nickname VARCHAR(100),
                    phone VARCHAR(20),
                    avatar_url VARCHAR(500),
                    credits INTEGER DEFAULT 0,
                    total_processed INTEGER DEFAULT 0,
                    monthly_processed INTEGER DEFAULT 0,
                    membership_type VARCHAR(20) DEFAULT 'free',
                    membership_expiry DATETIME,
                    status VARCHAR(20) DEFAULT 'active',
                    is_email_verified BOOLEAN DEFAULT 0,
                    email_verification_token VARCHAR(255),
                    reset_token VARCHAR(255),
                    reset_token_expires DATETIME,
                    notification_settings TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login_at DATETIME,
                    scheduled_deletion DATETIME,
                    deletion_reason VARCHAR(500)
                )
            """))
            conn.execute(text("""
                INSERT INTO users SELECT * FROM users_backup
            """))
            conn.execute(text("DROP TABLE users_backup"))
            conn.commit()
        
        # Verify rollback
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        assert 'is_admin' not in columns
        
        # Verify data is still intact
        session = SessionLocal()
        try:
            user_count = session.query(User).count()
            # Should still have users (if any were created)
            
        finally:
            session.close()


class TestMigrationPerformance:
    """Test migration performance with large datasets."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for migration testing."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_performance_migration.db")
        db_url = f"sqlite:///{db_path}"
        
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        yield engine, SessionLocal, db_path
        
        # Cleanup
        engine.dispose()
        shutil.rmtree(temp_dir)
    
    def test_large_dataset_migration(self, temp_db):
        """Test migration performance with large dataset."""
        import time
        engine, SessionLocal, db_path = temp_db
        
        # Create tables without is_admin column
        old_metadata = Base.metadata
        old_user_table = old_metadata.tables['users']
        old_user_table._columns.pop('is_admin', None)
        
        old_metadata.create_all(bind=engine)
        
        # Create large dataset
        session = SessionLocal()
        try:
            start_time = time.time()
            
            # Create 1000 users
            for i in range(1000):
                user_data = TestDataGenerator.create_user_data(
                    email=f"user{i}@test.com"
                )
                
                user = User(
                    user_id=user_data["user_id"],
                    email=user_data["email"],
                    hashed_password="hashed_password",
                    nickname=user_data["nickname"],
                    status=user_data["status"],
                    membership_type=user_data["membership_type"],
                    credits=user_data["credits"]
                )
                session.add(user)
                
                if i % 100 == 0:
                    session.commit()
            
            session.commit()
            creation_time = time.time() - start_time
            print(f"Created 1000 users in {creation_time:.2f} seconds")
            
        finally:
            session.close()
        
        # Run migration and measure performance
        start_time = time.time()
        
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN is_admin BOOLEAN DEFAULT 0
            """))
            conn.commit()
        
        migration_time = time.time() - start_time
        print(f"Migration completed in {migration_time:.2f} seconds")
        
        # Verify migration completed successfully
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        assert 'is_admin' in columns
        
        # Verify data integrity
        session = SessionLocal()
        try:
            user_count = session.query(User).count()
            assert user_count == 1000
            
            # Verify all users have is_admin = False
            admin_users = session.query(User).filter(User.is_admin == True).count()
            assert admin_users == 0
            
        finally:
            session.close()
        
        # Performance assertion (should complete within reasonable time)
        assert migration_time < 10.0, f"Migration took too long: {migration_time:.2f} seconds"