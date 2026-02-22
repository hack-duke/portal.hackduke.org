"""Google Sheets integration for exporting applicant data."""
import json
import os
from datetime import datetime
from typing import List, Dict, Any

from google.oauth2 import service_account
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1Q7aS2iA2rDywbJX7EaVLMXJj_wxAcslD4qLKcDaQWkE"


def get_sheets_service():
    """Create and return a Google Sheets service instance."""
    creds_json = os.environ.get("GOOGLE_CLOUD_CREDS_JSON")
    if not creds_json:
        raise ValueError("GOOGLE_CLOUD_CREDS_JSON environment variable not set")

    creds_dict = json.loads(creds_json)
    credentials = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=SCOPES
    )
    return build("sheets", "v4", credentials=credentials)


def export_applicants_to_sheets(
    accepted_applicants: List[Dict[str, Any]],
    rejected_applicants: List[Dict[str, Any]],
    confirmed_applicants: List[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """
    Export accepted, rejected, and confirmed applicants to Google Sheets.

    Creates new tabs:
    - "Accepted as of MM/DD"
    - "Rejected as of MM/DD"
    - "Confirmed as of MM/DD" (if confirmed_applicants provided)

    Each tab has columns: id, Email, Email Sent

    Args:
        accepted_applicants: List of dicts with 'user_id' and 'email' keys
        rejected_applicants: List of dicts with 'user_id' and 'email' keys
        confirmed_applicants: List of dicts with 'user_id' and 'email' keys (optional)

    Returns:
        Dict with tab names and counts
    """
    if confirmed_applicants is None:
        confirmed_applicants = []

    service = get_sheets_service()

    now = datetime.now()
    today = now.strftime("%m/%d")
    epoch = int(now.timestamp())

    accepted_tab_name = f"Accepted as of {today} ({epoch})"
    rejected_tab_name = f"Rejected as of {today} ({epoch})"
    confirmed_tab_name = f"Confirmed as of {today} ({epoch})"

    # Create the new tabs
    requests = [
        {
            "addSheet": {
                "properties": {
                    "title": accepted_tab_name,
                }
            }
        },
        {
            "addSheet": {
                "properties": {
                    "title": rejected_tab_name,
                }
            }
        },
        {
            "addSheet": {
                "properties": {
                    "title": confirmed_tab_name,
                }
            }
        }
    ]

    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={"requests": requests}
    ).execute()

    # Prepare data for accepted tab
    accepted_data = [["id", "Email", "Email Sent"]]  # Header row
    for applicant in accepted_applicants:
        accepted_data.append([applicant["user_id"], applicant["email"], ""])

    # Prepare data for rejected tab
    rejected_data = [["id", "Email", "Email Sent"]]  # Header row
    for applicant in rejected_applicants:
        rejected_data.append([applicant["user_id"], applicant["email"], ""])

    # Prepare data for confirmed tab
    confirmed_data = [["id", "Email", "Email Sent"]]  # Header row
    for applicant in confirmed_applicants:
        confirmed_data.append([applicant["user_id"], applicant["email"], ""])

    # Write data to accepted tab
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{accepted_tab_name}'!A1",
        valueInputOption="RAW",
        body={"values": accepted_data}
    ).execute()

    # Write data to rejected tab
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{rejected_tab_name}'!A1",
        valueInputOption="RAW",
        body={"values": rejected_data}
    ).execute()

    # Write data to confirmed tab
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{confirmed_tab_name}'!A1",
        valueInputOption="RAW",
        body={"values": confirmed_data}
    ).execute()

    return {
        "accepted_tab": accepted_tab_name,
        "rejected_tab": rejected_tab_name,
        "confirmed_tab": confirmed_tab_name,
        "accepted_count": len(accepted_applicants),
        "rejected_count": len(rejected_applicants),
        "confirmed_count": len(confirmed_applicants),
    }
