#!/usr/bin/env python3
"""
Script to add a user to the admin allowlist.
Usage: python add_admin.py <auth0_id>
"""
import sys
import asyncio
from sqlalchemy import select
from db import SessionLocal
from models.user import User
from models.admin_user import AdminUser

async def add_admin_async(auth0_id: str):
    """Add a user to the admin allowlist."""
    db = SessionLocal()
    
    try:
        # Get or create the user
        user = await db.scalar(select(User).where(User.auth0_id == auth0_id))
        if not user:
            # Create user entry (same logic as application submission)
            user = User(auth0_id=auth0_id)
            db.add(user)
            await db.flush()
            print(f"Created new user entry for auth0_id '{auth0_id}'")
        
        # Check if already an admin
        admin_user = await db.scalar(select(AdminUser).where(AdminUser.user_id == user.id))
        if admin_user:
            print(f"User {auth0_id} is already an admin!")
            return True
        
        # Add to admin allowlist
        admin_user = AdminUser(user_id=user.id)
        db.add(admin_user)
        await db.commit()
        
        print(f"✓ Successfully added {auth0_id} to admin allowlist!")
        print(f"  User ID: {user.id}")
        print(f"  Admin ID: {admin_user.id}")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        await db.rollback()
        return False
    finally:
        await db.close()

def add_admin(auth0_id: str):
    return asyncio.run(add_admin_async(auth0_id))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python add_admin.py <auth0_id>")
        print("Example: python add_admin.py google-oauth2|113033060705795781005")
        sys.exit(1)
    
    auth0_id = sys.argv[1]
    success = add_admin(auth0_id)
    sys.exit(0 if success else 1)
