#!/usr/bin/env python3
"""
Script to grant a user the admin role.
Usage: python add_admin.py <auth0_id>
"""

import sys
from db import SessionLocal
from models.user import User
from models.user_role import UserRole, RoleEnum


def add_admin(auth0_id: str):
    """Grant the admin role used by the portal's authorization checks."""
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.auth0_id == auth0_id).first()
        if not user:
            user = User(auth0_id=auth0_id)
            db.add(user)
            db.flush()
            print(f"Created new user entry for auth0_id '{auth0_id}'")

        admin_role = (
            db.query(UserRole)
            .filter(UserRole.user_id == user.id, UserRole.role == RoleEnum.ADMIN)
            .first()
        )
        if admin_role:
            print(f"User {auth0_id} is already an admin!")
            return True

        admin_role = UserRole(user_id=user.id, role=RoleEnum.ADMIN)
        db.add(admin_role)
        db.commit()

        print(f"✓ Successfully granted {auth0_id} the admin role!")
        print(f"  User ID: {user.id}")
        print(f"  Role ID: {admin_role.id}")
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
