"""Role management endpoints and utilities."""

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
from uuid import UUID
from pydantic import BaseModel

from auth import VerifyToken
from db import get_db
from models.user import User
from models.user_role import UserRole, RoleEnum
from services.auth0_management import search_users_by_email


router = APIRouter()
auth = VerifyToken()


# ============================================================================
# Helper Functions (for use in other routers)
# ============================================================================


async def user_has_role(db: AsyncSession, user_id: UUID, role: RoleEnum) -> bool:
    """Check if a user has a specific role."""
    return (
        (await db.scalars(select(UserRole).where(UserRole.user_id == user_id, UserRole.role == role).limit(1))).first()
        is not None
    )


async def user_has_any_role(db: AsyncSession, user_id: UUID, roles: List[RoleEnum]) -> bool:
    """Check if a user has any of the specified roles."""
    return (
        (await db.scalars(select(UserRole).where(UserRole.user_id == user_id, UserRole.role.in_(roles)).limit(1))).first()
        is not None
    )


async def get_user_roles(db: AsyncSession, user_id: UUID) -> List[RoleEnum]:
    """Get all roles for a user."""
    user_roles = (await db.scalars(select(UserRole).where(UserRole.user_id == user_id))).all()
    return [ur.role for ur in user_roles]


async def require_role(db: AsyncSession, user_id: UUID, role: RoleEnum) -> None:
    """Raise HTTPException if user doesn't have the required role."""
    if not await user_has_role(db, user_id, role):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


async def require_admin(db: AsyncSession, user_id: UUID) -> None:
    """Raise HTTPException if user is not an admin."""
    if not await user_has_role(db, user_id, RoleEnum.ADMIN):
        raise HTTPException(status_code=403, detail="Admin access required")


async def require_check_in(db: AsyncSession, user_id: UUID) -> None:
    """Allow dedicated check-in staff and full administrators to scan passes."""
    if not await user_has_any_role(db, user_id, [RoleEnum.CHECK_IN, RoleEnum.ADMIN]):
        raise HTTPException(status_code=403, detail="Check-in access required")


# ============================================================================
# Request/Response Models
# ============================================================================


class Auth0UserInfo(BaseModel):
    auth0_id: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None


class SearchUserResponse(BaseModel):
    auth0_users: List[Auth0UserInfo]


class UserWithRoles(BaseModel):
    user_id: str
    auth0_id: str
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    roles: List[str]


class GrantRoleRequest(BaseModel):
    auth0_id: str
    email: str
    role: str  # 'admin' or 'check_in'
    name: str


class RevokeRoleRequest(BaseModel):
    user_id: str
    role: str


class RoleActionResponse(BaseModel):
    success: bool
    message: str
    user: Optional[UserWithRoles] = None


class UsersWithRolesResponse(BaseModel):
    users: List[UserWithRoles]
    total: int


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/search-user", response_model=SearchUserResponse)
async def search_user_by_email(
    email: str,
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: AsyncSession = Depends(get_db),
):
    """
    Search for a user in Auth0 by email.
    Only accessible by admins.
    """
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    user = (await db.scalars(select(User).where(User.auth0_id == auth0_id).limit(1))).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    await require_admin(db, user.id)

    try:
        auth0_users = await search_users_by_email(email)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search Auth0: {str(e)}")

    result = []
    for au in auth0_users:
        result.append(
            Auth0UserInfo(
                auth0_id=au.get("user_id", ""),
                email=au.get("email", ""),
                name=au.get("name"),
                picture=au.get("picture"),
            )
        )

    return SearchUserResponse(auth0_users=result)


@router.post("/grant", response_model=RoleActionResponse)
async def grant_role(
    request: GrantRoleRequest,
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: AsyncSession = Depends(get_db),
):
    """
    Grant a role to a user.
    Creates the user in our DB if they don't exist.
    Only accessible by admins.
    """
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    granter = (await db.scalars(select(User).where(User.auth0_id == auth0_id).limit(1))).first()
    if not granter:
        raise HTTPException(status_code=401, detail="User not found")

    await require_admin(db, granter.id)

    # Validate role
    try:
        role = RoleEnum(request.role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {request.role}")

    # Find or create the target user
    target_user = (await db.scalars(select(User).where(User.auth0_id == request.auth0_id).limit(1))).first()
    name = request.name.split(" ")
    if not target_user:
        target_user = User(
            auth0_id=request.auth0_id,
            email=request.email,
            first_name=name[0],
            last_name=name[1] if len(name) > 1 else "",
        )
        db.add(target_user)
        await db.flush()

    # Check if role already exists
    existing_role = (
        (await db.scalars(select(UserRole).where(UserRole.user_id == target_user.id, UserRole.role == role).limit(1))).first()
    )

    if existing_role:
        return RoleActionResponse(
            success=True,
            message=f"User already has {role.value} role",
            user=await _build_user_with_roles(target_user, db),
        )

    # Grant the role
    user_role = UserRole(user_id=target_user.id, role=role, granted_by=granter.id)
    db.add(user_role)
    await db.commit()

    return RoleActionResponse(
        success=True,
        message=f"Granted {role.value} role",
        user=await _build_user_with_roles(target_user, db),
    )


@router.post("/revoke", response_model=RoleActionResponse)
async def revoke_role(
    request: RevokeRoleRequest,
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: AsyncSession = Depends(get_db),
):
    """
    Revoke a role from a user.
    Only accessible by admins.
    """
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    admin_user = (await db.scalars(select(User).where(User.auth0_id == auth0_id).limit(1))).first()
    if not admin_user:
        raise HTTPException(status_code=401, detail="User not found")

    await require_admin(db, admin_user.id)

    # Validate role
    try:
        role = RoleEnum(request.role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {request.role}")

    # Find the target user
    try:
        target_user_id = UUID(request.user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    target_user = (await db.scalars(select(User).where(User.id == target_user_id).limit(1))).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from revoking their own admin role
    if target_user.id == admin_user.id and role == RoleEnum.ADMIN:
        raise HTTPException(status_code=400, detail="Cannot revoke your own admin role")

    # Find and delete the role
    user_role = (
        (await db.scalars(select(UserRole).where(UserRole.user_id == target_user.id, UserRole.role == role).limit(1))).first()
    )

    if not user_role:
        return RoleActionResponse(
            success=True,
            message=f"User does not have {role.value} role",
            user=await _build_user_with_roles(target_user, db),
        )

    await db.delete(user_role)
    await db.commit()

    return RoleActionResponse(
        success=True,
        message=f"Revoked {role.value} role",
        user=await _build_user_with_roles(target_user, db),
    )


@router.get("/users", response_model=UsersWithRolesResponse)
async def list_users_with_roles(
    auth_payload: Dict[str, Any] = Security(auth.verify),
    db: AsyncSession = Depends(get_db),
):
    """
    List all users who have at least one role.
    Only accessible by admins.
    """
    auth0_id = auth_payload.get("sub")
    if not auth0_id:
        raise HTTPException(status_code=401, detail="Auth0 ID not found in token")

    user = (await db.scalars(select(User).where(User.auth0_id == auth0_id).limit(1))).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    await require_admin(db, user.id)

    # Get all users with roles
    users_with_roles = (
        (await db.scalars(select(User).join(UserRole, User.id == UserRole.user_id).distinct())).all()
    )

    result = []
    for u in users_with_roles:
        result.append(await _build_user_with_roles(u, db))

    return UsersWithRolesResponse(users=result, total=len(result))


async def _build_user_with_roles(user: User, db: AsyncSession) -> UserWithRoles:
    """Helper to build UserWithRoles response."""
    roles = await get_user_roles(db, user.id)
    return UserWithRoles(
        user_id=str(user.id),
        auth0_id=user.auth0_id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        roles=[r.value for r in roles],
    )
