import os
import json
from typing import Any
import boto3
from botocore.exceptions import ClientError


# Biến môi trường
AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "violated-transactions-bucket")
S3_PREFIX: str = os.getenv("S3_PREFIX", "violations/")  # tên root folder trong bucket

s3_client = boto3.client("s3", region_name=AWS_REGION)


def save_to_s3(transaction_data: dict) -> None:

    # Lấy transaction_id hoặc timestamp để đặt tên file
    transaction_id: str = transaction_data.get("transaction_id", "unknown")
    timestamp: Any = transaction_data.get("timestamp")
    file_name: str = f"{S3_PREFIX}{transaction_id}_{timestamp}.json"

    try:
        # Chuyển sang JSON string
        json_data: str = json.dumps(transaction_data, ensure_ascii=False)

        # Upload lên S3
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=file_name,
            Body=json_data.encode("utf-8"),
            ContentType="application/json"
        )

        print(f"Đã lưu giao dịch vi phạm vào S3: {S3_BUCKET_NAME}/{file_name}")

    except ClientError as e:
        raise RuntimeError(f"Lỗi khi ghi lên S3: {e}")
        
