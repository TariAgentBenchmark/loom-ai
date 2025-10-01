# Admin Setup Guide

This guide will walk you through setting up the admin functionality for LoomAI, including database migrations, creating the first admin user, and configuring the system.

## Prerequisites

Before you begin, ensure you have:

- LoomAI backend and frontend installed
- Database access (SQLite for development, PostgreSQL for production)
- Admin access to the server/system
- Python 3.8+ and Node.js 16+ installed

## Database Setup

### 1. Initialize Database

First, initialize the database with the required tables:

```bash
cd backend
python init_db.py
```

This will:
- Create all necessary database tables
- Set up initial package data
- Create the default admin user

### 2. Run Admin Migration

The admin functionality requires an `is_admin` column in the users table. Run the migration:

```bash
cd backend
python migrations/add_is_admin_column.py
```

This migration will:
- Add the `is_admin` column to the users table
- Set default value to `False` for existing users
- Update the default admin user if it exists

### 3. Verify Database Setup

Check that the admin column was added successfully:

```bash
sqlite3 database.db ".schema users"
```

You should see the `is_admin` column in the users table schema.

## Creating the First Admin User

### Method 1: Using the Initialization Script (Recommended)

The easiest way to create an admin user is to use the initialization script:

```bash
cd backend
python init_db.py
```

This will create an admin user with the following credentials:
- **Email**: admin@loom-ai.com
- **Password**: admin123456
- **User ID**: admin_loom_ai

> ⚠️ **Security Note**: Change the default password immediately after first login!

### Method 2: Manual Admin User Creation

If you need to create a custom admin user, you can do so programmatically:

```python
# create_admin.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User, MembershipType, UserStatus
from app.services.auth_service import AuthService

def create_admin_user(email, password, nickname=None):
    db = SessionLocal()
    auth_service = AuthService()
    
    try:
        # Check if user already exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"User {email} already exists")
            return
        
        # Create admin user
        admin_user = User(
            user_id=f"admin_{email.split('@')[0]}",
            email=email,
            hashed_password=auth_service.get_password_hash(password),
            nickname=nickname or "Administrator",
            credits=999999,
            membership_type=MembershipType.ENTERPRISE,
            status=UserStatus.ACTIVE,
            is_email_verified=True,
            is_admin=True
        )
        
        db.add(admin_user)
        db.commit()
        
        print(f"✅ Admin user created successfully!")
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {password}")
        
    except Exception as e:
        print(f"❌ Failed to create admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user("your-admin@example.com", "your-secure-password", "Admin Name")
```

Run this script with your custom credentials:

```bash
python create_admin.py
```

### Method 3: Promoting Existing User to Admin

To promote an existing user to admin status:

```python
# promote_to_admin.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User

def promote_user_to_admin(email):
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"User {email} not found")
            return
        
        user.is_admin = True
        db.commit()
        
        print(f"✅ User {email} has been promoted to admin!")
        
    except Exception as e:
        print(f"❌ Failed to promote user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    promote_user_to_admin("existing-user@example.com")
```

## Environment Configuration

### Backend Configuration

Update your `.env` file in the backend directory:

```env
# Admin Configuration
ADMIN_DEFAULT_EMAIL=admin@loom-ai.com
ADMIN_DEFAULT_PASSWORD=admin123456

# JWT Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database Configuration
DATABASE_URL=sqlite:///./database.db
# For production use PostgreSQL:
# DATABASE_URL=postgresql://username:password@localhost/loomai

# Security
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### Frontend Configuration

Update your `.env.local` file in the frontend directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ADMIN_URL=http://localhost:3000/admin
```

## Verification Steps

### 1. Verify Admin User Creation

Check that the admin user was created correctly:

```python
# verify_admin.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User

def verify_admin_users():
    db = SessionLocal()
    
    try:
        admin_users = db.query(User).filter(User.is_admin == True).all()
        
        print(f"Found {len(admin_users)} admin users:")
        for user in admin_users:
            print(f"- {user.email} ({user.user_id}) - Status: {user.status.value}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_admin_users()
```

Run this script:

```bash
python verify_admin.py
```

### 2. Test Admin Login

Start the backend server:

```bash
cd backend
python run_server.py
```

Test admin authentication:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/admin/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@loom-ai.com",
    "password": "admin123456"
  }'
```

You should receive a response with admin tokens:

```json
{
  "success": true,
  "message": "管理员登录成功",
  "data": {
    "accessToken": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refreshToken": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "tokenType": "bearer",
    "expiresIn": 1800,
    "isAdmin": true,
    "adminSession": true,
    "user": {
      "userId": "admin_loom_ai",
      "email": "admin@loom-ai.com",
      "nickname": "管理员",
      "isAdmin": true
    }
  }
}
```

### 3. Access Admin Dashboard

Start the frontend server:

```bash
cd frontend
npm run dev
```

Navigate to the admin login page:

```
http://localhost:3000/admin/login
```

Login with your admin credentials and verify you can access the dashboard.

## Next Steps

After completing the setup:

1. [Change the default admin password](./security-best-practices.md)
2. [Configure the production environment](./deployment-guide.md)
3. [Review the admin dashboard quick start guide](./quick-start-guide.md)
4. [Set up monitoring and logging](./troubleshooting.md)

## Troubleshooting

### Common Issues

**Issue: "Admin user not found" error**
- Solution: Verify the admin user was created by running the verification script
- Check the database for the `is_admin` column

**Issue: "Invalid authentication credentials"**
- Solution: Verify the password is correct
- Check that the user has `is_admin = True`

**Issue: Database migration fails**
- Solution: Ensure you have write permissions to the database file
- Check that the database is not locked by another process

**Issue: Admin login redirects to regular user dashboard**
- Solution: Verify the `adminSession` flag is set in the JWT token
- Check the frontend admin authentication context

For more troubleshooting tips, see the [Admin Troubleshooting Guide](./troubleshooting.md).