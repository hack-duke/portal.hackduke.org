import httpx
import pytest

from services import wallet_pass


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "error", request=httpx.Request("POST", wallet_pass.WALLETWALLET_PASSES_URL), response=None
            )

    def json(self):
        return self._payload


def test_create_pass_sends_user_id_as_qr(monkeypatch):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured.update(url=url, headers=headers, json=json)
        return FakeResponse(payload={"serialNumber": "s1", "shareUrl": "https://pass.walletwallet.dev/p/s1"})

    monkeypatch.setenv("WALLETWALLET_API_KEY", "ww_live_test")
    monkeypatch.setattr(wallet_pass.httpx, "post", fake_post)

    result = wallet_pass.create_check_in_pass("user-123", "Ada Lovelace")

    assert result["serialNumber"] == "s1"
    assert captured["url"] == "https://api.walletwallet.dev/api/passes"
    assert captured["headers"] == {"Authorization": "Bearer ww_live_test"}
    body = captured["json"]
    assert body["barcodeValue"] == "user-123"
    assert body["barcodeFormat"] == "QR"
    assert body["primaryFields"] == [{"label": "ATTENDEE", "value": "Ada Lovelace"}]
    assert body["expirationDate"] == "2027-02-08T23:59:00-05:00"
    assert body["colorPreset"] == "blue"


def test_create_pass_skips_without_api_key(monkeypatch):
    monkeypatch.delenv("WALLETWALLET_API_KEY", raising=False)
    monkeypatch.setattr(wallet_pass.httpx, "post", lambda *a, **k: pytest.fail("should not call API"))

    assert wallet_pass.create_check_in_pass("user-123", "Ada") is None


def test_create_pass_raises_on_api_error(monkeypatch):
    monkeypatch.setenv("WALLETWALLET_API_KEY", "ww_live_test")
    monkeypatch.setattr(wallet_pass.httpx, "post", lambda *a, **k: FakeResponse(status_code=429))

    with pytest.raises(httpx.HTTPStatusError):
        wallet_pass.create_check_in_pass("user-123", "Ada")
