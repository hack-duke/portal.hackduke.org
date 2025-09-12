import pytest
from unittest.mock import patch, MagicMock
from fastapi.security import HTTPAuthorizationCredentials

from auth import VerifyToken, UnauthorizedException, UnauthenticatedException
from jwt.exceptions import PyJWKClientError


@pytest.mark.asyncio
@patch("auth.jwt.decode")
@patch("auth.jwt.PyJWKClient")
async def test_verify_success(mock_jwks_cls, mock_decode):
    fake_token = "fake.jwt.token"
    fake_payload = {"sub": "123", "scope": "read:stuff"}

    mock_client = MagicMock()
    mock_client.get_signing_key_from_jwt.return_value.key = "fake_key"
    mock_jwks_cls.return_value = mock_client
    mock_decode.return_value = fake_payload

    verifier = VerifyToken()
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=fake_token)

    payload = await verifier.verify(security_scopes=[], token=creds)

    assert payload == fake_payload
    mock_jwks_cls.assert_called_once()
    mock_client.get_signing_key_from_jwt.assert_called_once_with(fake_token)
    mock_decode.assert_called_once()


@pytest.mark.asyncio
async def test_verify_unauthenticated():
    verifier = VerifyToken()
    with pytest.raises(UnauthenticatedException):
        await verifier.verify(security_scopes=[], token=None)


@pytest.mark.asyncio
@patch("auth.jwt.PyJWKClient")
async def test_verify_bad_signing_key(mock_jwks_cls):
    mock_client = MagicMock()
    mock_client.get_signing_key_from_jwt.side_effect = PyJWKClientError()
    mock_jwks_cls.return_value = mock_client

    verifier = VerifyToken()
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad.jwt")

    with pytest.raises(UnauthorizedException):
        await verifier.verify(security_scopes=[], token=creds)


@pytest.mark.asyncio
@patch("auth.jwt.decode", side_effect=Exception())
@patch("auth.jwt.PyJWKClient")
async def test_verify_invalid_token(mock_jwks_cls, mock_decode):
    mock_client = MagicMock()
    mock_client.get_signing_key_from_jwt.return_value.key = "fake_key"
    mock_jwks_cls.return_value = mock_client

    verifier = VerifyToken()
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="fake.jwt")

    with pytest.raises(UnauthorizedException):
        await verifier.verify(security_scopes=[], token=creds)
