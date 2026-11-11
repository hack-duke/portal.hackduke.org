from unittest.mock import AsyncMock, patch

import jwt
import pytest
from fastapi.security import HTTPAuthorizationCredentials

from auth import VerifyToken, UnauthorizedException, UnauthenticatedException


@pytest.mark.asyncio
@patch.object(VerifyToken, "_get_signing_key", new_callable=AsyncMock)
@patch("auth.jwt.decode")
async def test_verify_success(mock_decode, mock_get_signing_key):
    fake_token = "fake.jwt.token"
    fake_payload = {"sub": "123", "scope": "read:stuff"}
    mock_get_signing_key.return_value = "fake_key"
    mock_decode.return_value = fake_payload

    verifier = VerifyToken()
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=fake_token)

    payload = await verifier.verify(security_scopes=[], token=creds)

    assert payload == fake_payload
    mock_get_signing_key.assert_awaited_once_with(fake_token)
    mock_decode.assert_called_once()


@pytest.mark.asyncio
async def test_verify_unauthenticated():
    verifier = VerifyToken()
    with pytest.raises(UnauthenticatedException):
        await verifier.verify(security_scopes=[], token=None)


@pytest.mark.asyncio
@patch.object(VerifyToken, "_get_signing_key", new_callable=AsyncMock)
async def test_verify_bad_signing_key(mock_get_signing_key):
    mock_get_signing_key.side_effect = jwt.PyJWKClientError("No signing key")

    verifier = VerifyToken()
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad.jwt")

    with pytest.raises(UnauthorizedException):
        await verifier.verify(security_scopes=[], token=creds)


@pytest.mark.asyncio
@patch.object(VerifyToken, "_get_signing_key", new_callable=AsyncMock)
@patch("auth.jwt.decode", side_effect=Exception())
async def test_verify_invalid_token(_mock_decode, mock_get_signing_key):
    mock_get_signing_key.return_value = "fake_key"

    verifier = VerifyToken()
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="fake.jwt")

    with pytest.raises(UnauthorizedException):
        await verifier.verify(security_scopes=[], token=creds)
