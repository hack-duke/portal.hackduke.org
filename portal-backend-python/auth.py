"""Async Auth0 JWT verification."""

import asyncio
import os
import time
from typing import Optional

import httpx2
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    SecurityScopes,
)


auth0_domain = os.getenv("AUTH0_DOMAIN")
auth0_api_audience = os.getenv("AUTH0_API_AUDIENCE")
auth0_issuer = os.getenv("AUTH0_ISSUER")
auth0_algorithms = os.getenv("AUTH0_ALGORITHMS")


class UnauthorizedException(HTTPException):
    def __init__(self, detail: str, **kwargs):
        super().__init__(status.HTTP_403_FORBIDDEN, detail=detail)


class UnauthenticatedException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Requires authentication"
        )


class VerifyToken:
    JWKS_CACHE_SECONDS = 300

    def __init__(self):
        self.jwks_url = f"https://{auth0_domain}/.well-known/jwks.json"
        self._jwks: jwt.PyJWKSet | None = None
        self._jwks_fetched_at = 0.0
        self._jwks_lock = asyncio.Lock()

    async def _get_jwks(self, *, force_refresh: bool = False) -> jwt.PyJWKSet:
        now = time.monotonic()
        if (
            not force_refresh
            and self._jwks is not None
            and now - self._jwks_fetched_at < self.JWKS_CACHE_SECONDS
        ):
            return self._jwks

        async with self._jwks_lock:
            now = time.monotonic()
            if (
                not force_refresh
                and self._jwks is not None
                and now - self._jwks_fetched_at < self.JWKS_CACHE_SECONDS
            ):
                return self._jwks

            async with httpx2.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.jwks_url)
            response.raise_for_status()
            self._jwks = jwt.PyJWKSet.from_dict(response.json())
            self._jwks_fetched_at = time.monotonic()
            return self._jwks

    async def _get_signing_key(self, token: str) -> object:
        header = jwt.get_unverified_header(token)
        key_id = header.get("kid")
        if not isinstance(key_id, str) or not key_id:
            raise jwt.PyJWKClientError("Token is missing a key ID")

        jwks = await self._get_jwks()
        signing_key = self._find_signing_key(jwks, key_id)
        if signing_key is None:
            # Auth0 may have rotated signing keys since the cached JWKS was read.
            jwks = await self._get_jwks(force_refresh=True)
            signing_key = self._find_signing_key(jwks, key_id)
        if signing_key is None:
            raise jwt.PyJWKClientError("Unable to find a signing key for this token")
        return signing_key.key

    @staticmethod
    def _find_signing_key(jwks: jwt.PyJWKSet, key_id: str) -> jwt.PyJWK | None:
        return next(
            (
                key
                for key in jwks.keys
                if key.key_id == key_id and key.public_key_use in (None, "sig")
            ),
            None,
        )

    async def verify(
        self,
        security_scopes: SecurityScopes,
        token: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer()),
    ):
        if token is None:
            raise UnauthenticatedException

        try:
            signing_key = await self._get_signing_key(token.credentials)
        except Exception as error:
            raise UnauthorizedException(str(error))

        try:
            return jwt.decode(
                token.credentials,
                signing_key,
                algorithms=auth0_algorithms,
                audience=auth0_api_audience,
                issuer=auth0_issuer,
            )
        except Exception as error:
            raise UnauthorizedException(str(error))
