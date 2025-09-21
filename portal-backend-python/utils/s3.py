import boto3
import os
from typing import Optional
from fastapi import UploadFile

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")


def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )


async def upload_file_to_s3(file: UploadFile, s3_key: str) -> Optional[str]:
    s3_client = get_s3_client()

    file_content = await file.read()

    s3_client.put_object(
        Bucket=AWS_BUCKET_NAME,
        Key=s3_key,
        Body=file_content,
        ContentType=file.content_type,
    )

    return s3_key
