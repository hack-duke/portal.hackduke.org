import os

import boto3


def get_sender_email() -> str:
    """Verified SES sender, e.g. "HackDuke <team@hackduke.org>"."""
    sender = os.getenv("SES_SENDER_EMAIL")
    if not sender:
        raise RuntimeError("SES_SENDER_EMAIL is not configured")
    return sender


def get_ses_client():
    return boto3.client(
        "ses",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


def send_email(to: str, subject: str, html_body: str, client=None) -> dict:
    """Send a single HTML email to one recipient via AWS SES."""
    ses_client = client or get_ses_client()
    return ses_client.send_email(
        Source=get_sender_email(),
        Destination={"ToAddresses": [to]},
        Message={
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {"Html": {"Data": html_body, "Charset": "UTF-8"}},
        },
    )
