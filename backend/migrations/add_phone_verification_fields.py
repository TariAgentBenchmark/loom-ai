#!/usr/bin/env python3
"""
Migration script to add phone verification fields to the User model.

This script adds the following fields to the users table:
- phone_verification_code: 6位验证码
- phone_verification_expires: 验证码过期时间
- is_phone_verified: 手机是否已验证
- phone_verified_at: 手机验证时间
- last_sms_sent: 上次发送短信时间
- sms_attempts_today: 今日发送次数
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db, engine, Base
from app.models.user import User
from sqlalchemy import text


def migrate():
    """Run the migration"""
    print("Starting migration for phone verification fields...")
    
    # Create a database session
    db = next(get_db())
    
    try:
        # Check if phone_verification_code column already exists
        # SQLite uses PRAGMA table_info to get column information
        result = db.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result.fetchall()]  # Get column names
        column_exists = 'phone_verification_code' in columns
        
        if not column_exists:
            print("Adding phone verification columns...")
            
            # Add phone verification columns
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN phone_verification_code VARCHAR(10)
            """))
            
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN phone_verification_expires TIMESTAMP
            """))
            
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN is_phone_verified BOOLEAN DEFAULT FALSE
            """))
            
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN phone_verified_at TIMESTAMP
            """))
            
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN last_sms_sent TIMESTAMP
            """))
            
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN sms_attempts_today INTEGER DEFAULT 0
            """))
            
            db.commit()
            print("Phone verification columns added successfully")
        else:
            print("Phone verification columns already exist")
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()