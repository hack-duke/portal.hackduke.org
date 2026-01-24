#!/usr/bin/env python3
"""
Script to add a user to the admin allowlist.
Usage: python add_admin.py <auth0_id>
"""
import sys
from db import SessionLocal
from models.user import User
from models.admin_user import AdminUser

def add_admin(auth0_id: str):
    """Add a user to the admin allowlist."""
    db = SessionLocal()
    
    try:
        # Get or create the user
        user = db.query(User).filter(User.auth0_id == auth0_id).first()
        if not user:
            # Create user entry (same logic as application submission)
            user = User(auth0_id=auth0_id)
            db.add(user)
            db.flush()
            print(f"Created new user entry for auth0_id '{auth0_id}'")
        
        # Check if already an admin
        admin_user = db.query(AdminUser).filter(AdminUser.user_id == user.id).first()
        if admin_user:
            print(f"User {auth0_id} is already an admin!")
            return True
        
        # Add to admin allowlist
        admin_user = AdminUser(user_id=user.id)
        db.add(admin_user)
        db.commit()
        
        print(f"✓ Successfully added {auth0_id} to admin allowlist!")
        print(f"  User ID: {user.id}")
        print(f"  Admin ID: {admin_user.id}")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python add_admin.py <auth0_id>")
        print("Example: python add_admin.py google-oauth2|113033060705795781005")
        sys.exit(1)
    
    auth0_id = sys.argv[1]
    success = add_admin(auth0_id)
    sys.exit(0 if success else 1)
