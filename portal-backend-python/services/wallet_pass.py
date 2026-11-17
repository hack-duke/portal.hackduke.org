"""Apple/Google Wallet check-in passes via WalletWallet.

API reference: https://www.walletwallet.dev/docs/

The pass barcode is the applicant's user_id, which is exactly what the
existing check-in scanner (POST /check_in/log_user) already reads from the
on-screen QR code, so scanning the Wallet pass checks the attendee in.
"""

import logging
import os
from typing import Any, Dict, Optional

import httpx
from sqlalchemy.orm import Session

from models.application import Application

logger = logging.getLogger(__name__)

WALLETWALLET_PASSES_URL = "https://api.walletwallet.dev/api/passes"
EVENT_NAME = "HackDuke: Code for Good 2027"
# End of Feb 8, 2027 in Eastern time; WalletWallet requires an RFC 3339 offset.
EVENT_END = "2027-02-08T23:59:00-05:00"
REQUEST_TIMEOUT_SECONDS = 10


def _attendee_name(application: Application) -> str:
    submission = application.submission_json or {}
    name = f"{submission.get('first_name', '')} {submission.get('last_name', '')}"
    return name.strip() or "Attendee"


def create_check_in_pass(user_id: str, attendee_name: str) -> Optional[Dict[str, Any]]:
    """Create a pass and return WalletWallet's JSON, or None if no API key is set."""
    api_key = os.getenv("WALLETWALLET_API_KEY", "").strip()
    if not api_key:
        logger.warning("WALLETWALLET_API_KEY is not set; skipping Wallet pass creation")
        return None

    response = httpx.post(
        WALLETWALLET_PASSES_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "barcodeValue": user_id,
            "barcodeFormat": "QR",
            "logoText": EVENT_NAME,
            "organizationName": "HackDuke",
            "description": f"{EVENT_NAME} check-in pass",
            "primaryFields": [{"label": "ATTENDEE", "value": attendee_name}],
            "secondaryFields": [{"label": "CHECK-IN", "value": "Show this QR at the door"}],
            "expirationDate": EVENT_END,
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def issue_pass_for_application(db: Session, application: Application) -> None:
    """Create and store a check-in pass for an accepted application.

    Does nothing if the application already has a pass. Never raises, so a
    WalletWallet outage cannot block an admin's acceptance decision.
    """
    if application.wallet_pass_serial:
        return

    try:
        data = create_check_in_pass(str(application.user_id), _attendee_name(application))
    except (httpx.HTTPError, ValueError):
        logger.exception("Wallet pass creation failed for application %s", application.id)
        return

    if not data or not data.get("serialNumber"):
        return

    try:
        application.wallet_pass_serial = data["serialNumber"]
        application.wallet_pass_url = data.get("shareUrl")
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to save Wallet pass for application %s", application.id)
