#!/usr/bin/env python3
"""
Migration script to update the User model for phone-based authentication.

This script:
1. Makes phone number required and unique
2. Makes email optional
3. Updates existing users to have a temporary phone number if they don't have one
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db, engine, Base
from app.models.user import User
from sqlalchemy import text
import uuid


def migrate():
    """Run the migration"""
    print("Starting migration for phone-based authentication...")
    
    # Create a database session
    db = next(get_db())
    
    try:
        # Check if phone column already has unique constraint
        result = db.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.table_constraints 
            WHERE table_name = 'users' 
            AND constraint_name = 'ix_users_phone'
            AND constraint_type = 'UNIQUE'
        """))
        
        has_unique_constraint = result.fetchone()[0] > 0
        
        # Step 1: Update existing users without phone numbers
        print("Updating existing users without phone numbers...")
        users_without_phone = db.query(User).filter(User.phone.is_(None)).all()
        
        for user in users_without_phone:
            # Generate a temporary phone number based on user ID
            temp_phone = f"TMP{user.id:010d}"  # e.g., TMP0000000001
            user.phone = temp_phone
            print(f"Updated user {user.email or user.user_id} with temporary phone: {temp_phone}")
        
        db.commit()
        
        # Step 2: Check for duplicate phone numbers and resolve them
        print("Checking for duplicate phone numbers...")
        duplicate_phones = db.execute(text("""
            SELECT phone, COUNT(*) as count 
            FROM users 
            WHERE phone IS NOT NULL 
            GROUP BY phone 
            HAVING COUNT(*) > 1
        """)).fetchall()
        
        for phone, count in duplicate_phones:
            print(f"Found {count} users with phone {phone}")
            
            # Get all users with this phone number
            users = db.query(User).filter(User.phone == phone).all()
            
            # Keep the first user's phone as is, update the rest
            for i, user in enumerate(users[1:], 1):
                new_phone = f"{phone}_{i}"
                user.phone = new_phone
                print(f"Updated user {user.email or user.user_id} phone to: {new_phone}")
        
        db.commit()
        
        # Step 3: If phone column doesn't have unique constraint, add it
        if not has_unique_constraint:
            print("Adding unique constraint to phone column...")
            
            # First, make sure all phone numbers are unique
            db.execute(text("""
                UPDATE users 
                SET phone = CONCAT(phone, '_', id) 
                WHERE phone IN (
                    SELECT phone FROM users 
                    WHERE phone IS NOT NULL 
                    GROUP BY phone 
                    HAVING COUNT(*) > 1
                ) AND id NOT IN (
                    SELECT MIN(id) FROM users 
                    WHERE phone IS NOT NULL 
                    GROUP BY phone 
                    HAVING COUNT(*) > 1
                )
            """))
            
            db.commit()
            
            # Add the unique constraint
            db.execute(text("""
                CREATE UNIQUE INDEX ix_users_phone ON users(phone)
            """))
            
            db.commit()
            print("Unique constraint added to phone column")
        
        # Step 4: Make email column nullable if it's not already
        print("Checking if email column is nullable...")
        result = db.execute(text("""
            SELECT is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'email'
        """))
        
        is_nullable = result.fetchone()[0]
        
        if is_nullable.upper() == 'NO':
            print("Making email column nullable...")
            
            # First, update any NULL emails to empty string to avoid constraint violations
            db.execute(text("""
                UPDATE users 
                SET email = NULL 
                WHERE email = ''
            """))
            
            db.commit()
            
            # Make the column nullable
            db.execute(text("""
                ALTER TABLE users 
                ALTER COLUMN email DROP NOT NULL
            """))
            
            db.commit()
            print("Email column is now nullable")
        else:
            print("Email column is already nullable")
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()