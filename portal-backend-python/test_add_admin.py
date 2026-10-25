from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

import add_admin as admin_script
from models.admin_user import AdminUser
from models.user import User
from models.user_role import RoleEnum, UserRole


@pytest.fixture
def admin_sessions(test_sessionmaker, monkeypatch):
    """Keep script commits inside a transaction on the disposable test database."""
    engine = test_sessionmaker.kw["bind"]
    with engine.connect() as connection:
        transaction = connection.begin()
        sessions = sessionmaker(
            bind=connection, autoflush=False, join_transaction_mode="create_savepoint"
        )
        monkeypatch.setattr(admin_script, "SessionLocal", sessions)
        try:
            yield sessions
        finally:
            transaction.rollback()


def test_add_admin_creates_user_and_current_admin_role(admin_sessions):
    auth0_id = f"auth0|{uuid4()}"

    assert admin_script.add_admin(auth0_id) is True

    with admin_sessions() as db:
        user = db.query(User).filter_by(auth0_id=auth0_id).one()
        role = db.query(UserRole).filter_by(user_id=user.id).one()
        assert role.role == RoleEnum.ADMIN
        assert db.query(AdminUser).filter_by(user_id=user.id).count() == 0


def test_add_admin_upgrades_legacy_allowlist_entry(admin_sessions):
    auth0_id = f"auth0|{uuid4()}"
    with admin_sessions.begin() as db:
        user = User(auth0_id=auth0_id)
        db.add(user)
        db.flush()
        db.add(AdminUser(user_id=user.id))

    assert admin_script.add_admin(auth0_id) is True

    with admin_sessions() as db:
        user = db.query(User).filter_by(auth0_id=auth0_id).one()
        assert db.query(UserRole).filter_by(
            user_id=user.id, role=RoleEnum.ADMIN
        ).count() == 1
        assert db.query(AdminUser).filter_by(user_id=user.id).count() == 1


@pytest.mark.parametrize("existing_role", [RoleEnum.CHECK_IN, RoleEnum.ADMIN])
def test_add_admin_preserves_roles_and_is_idempotent(admin_sessions, existing_role):
    auth0_id = f"auth0|{uuid4()}"
    with admin_sessions.begin() as db:
        user = User(auth0_id=auth0_id)
        db.add(user)
        db.flush()
        db.add(UserRole(user_id=user.id, role=existing_role))

    assert admin_script.add_admin(auth0_id) is True
    assert admin_script.add_admin(auth0_id) is True

    with admin_sessions() as db:
        user = db.query(User).filter_by(auth0_id=auth0_id).one()
        roles = db.query(UserRole).filter_by(user_id=user.id).all()
        assert len(roles) == len({existing_role, RoleEnum.ADMIN})
        assert {role.role for role in roles} == {existing_role, RoleEnum.ADMIN}
