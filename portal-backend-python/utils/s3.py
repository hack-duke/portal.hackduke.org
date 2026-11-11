import os

import aioboto3
from fastapi import UploadFile


def get_s3_client():
    return aioboto3.Session().client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


async def upload_file_to_s3(file: UploadFile, s3_key: str) -> str:
    file_content = await file.read()

    async with get_s3_client() as s3_client:
        await s3_client.put_object(
            Bucket=os.getenv("S3_BUCKET_NAME"),
            Key=s3_key,
            Body=file_content,
            ContentType=file.content_type,
        )

    return s3_key
