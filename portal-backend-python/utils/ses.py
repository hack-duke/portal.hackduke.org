import boto3
import os
from typing import List, Optional

SES_SENDER_EMAIL = "22kellyx@gmail.com" #change to whatever email you're using 

def get_ses_client():
    return boto3.client(
        "ses",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


def send_email(
    to: List[str],
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
):
    ses_client = get_ses_client()

    destination = {"ToAddresses": to}
    destination["CcAddresses"] = cc or []
    destination["BccAddresses"] = bcc or []

    response = ses_client.send_email(
        Source=SES_SENDER_EMAIL,
        Destination=destination,
        Message={
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {"Html": {"Data": body, "Charset": "UTF-8"}},
        },
    )

    return response
