"""Provision one DuQuantum organizer and request an Auth0 password reset.

This operator script is streamed into the healthy production backend. It never
prints the recipient, Auth0 identifier, or password reset capability.
"""

from __future__ import annotations

import argparse
from email.utils import parseaddr

import httpx
from sqlalchemy import func

from db import get_local_session
from models import RoleEnum, User, UserRole
from services.auth0_onboarding import Auth0OnboardingClient, Auth0OnboardingSettings


EVENT_SLUG = "duquantum-2026"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recipient-email", required=True)
    parser.add_argument("--recipient-name", required=True)
    parser.add_argument("--confirm-event", required=True)
    parser.add_argument("--auth0-client-id", required=True)
    return parser


def validated_email(value: str) -> str:
    email = value.strip().casefold()
    parsed_name, parsed_email = parseaddr(email)
    if parsed_name or parsed_email != email or "@" not in email or len(email) > 320:
        raise ValueError("a single valid organizer email is required")
    return email


def split_name(value: str) -> tuple[str, str, str]:
    display_name = " ".join(value.split())
    if not display_name or len(display_name) > 255:
        raise ValueError("an organizer name is required")
    first_name, separator, last_name = display_name.partition(" ")
    return display_name, first_name, last_name if separator else ""


def database_user(users, connection: str):
    matches = [
        user
        for user in users
        if any(
            identity.get("connection") == connection
            for identity in user.get("identities", [])
        )
    ]
    if len(matches) > 1:
        raise RuntimeError("multiple Auth0 database organizer accounts matched")
    return matches[0] if matches else None


def run(args: argparse.Namespace) -> str:
    if args.confirm_event != EVENT_SLUG:
        raise ValueError(f"confirmation must exactly match {EVENT_SLUG}")

    email = validated_email(args.recipient_email)
    _, first_name, last_name = split_name(args.recipient_name)
    auth_settings = Auth0OnboardingSettings.from_environment()
    session = get_local_session()
    try:
        with Auth0OnboardingClient(auth_settings) as auth0:
            match = database_user(
                auth0.find_users_by_email(email),
                auth_settings.database_connection,
            )
            if match is None:
                auth0_user_id = auth0.create_user(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                )
                account_result = "created"
            else:
                auth0_user_id = str(match["user_id"])
                account_result = "reused"

            user = (
                session.query(User).filter(User.auth0_id == auth0_user_id).one_or_none()
            )
            email_matches = (
                session.query(User).filter(func.lower(User.email) == email).all()
            )
            conflicts = [
                item for item in email_matches if item.auth0_id != auth0_user_id
            ]
            if conflicts:
                raise RuntimeError(
                    "organizer email conflicts with another portal identity"
                )
            if user is None:
                user = User(
                    auth0_id=auth0_user_id,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                )
                session.add(user)
                session.flush()
            else:
                user.email = email
                user.first_name = first_name
                user.last_name = last_name

            for role in (RoleEnum.ADMIN, RoleEnum.CHECK_IN):
                existing = (
                    session.query(UserRole)
                    .filter(UserRole.user_id == user.id, UserRole.role == role)
                    .one_or_none()
                )
                if existing is None:
                    session.add(UserRole(user_id=user.id, role=role))
            session.commit()
            auth0.request_password_reset(
                email=email,
                client_id=args.auth0_client_id,
            )
        return account_result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        account_result = run(args)
    except httpx.HTTPStatusError as exc:
        response = exc.response
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        error_code = str(
            payload.get("errorCode")
            or payload.get("code")
            or payload.get("error")
            or ""
        )
        safe_code = "".join(
            character
            for character in error_code
            if character.isalnum() or character in "_-"
        )[:80]
        endpoint = exc.request.url.path
        print(
            "Organizer provisioning failed at Auth0 "
            f"{endpoint} (HTTP {response.status_code}"
            f"{f', {safe_code}' if safe_code else ''})"
        )
        return 1
    except Exception as exc:
        print(f"Organizer provisioning failed ({type(exc).__name__})")
        return 1
    print("DuQuantum organizer roles are active")
    print(f"Auth0 database account: {account_result}")
    print("A single-use Auth0 password reset email was requested")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
