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
    user: str = transaction_data.get("nameOrig", "unknown")
    device: str = transaction_data.get("nameDest", "unknown")
    file_name: str = f"{S3_PREFIX}{user}_{device}.json"

    print(f"[S3] Region={AWS_REGION} | Bucket={S3_BUCKET_NAME} | Key={file_name}")

    try:
         # ===== Kiểm tra bucket tồn tại và quyền truy cập =====
        s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
        print(f"[S3] Bucket exists and Lambda has access permission.")

        # Chuyển sang JSON string
        json_data: str = json.dumps(transaction_data, ensure_ascii=False)

        # Upload lên S3
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=file_name,
            Body=json_data.encode("utf-8"),
            ContentType="application/json"
        )

        print(f"[S3] Upload successful at: {S3_BUCKET_NAME}/{file_name}")

    except ClientError as e:
        raise RuntimeError(f"[S3] ERROR: Unexpected exception: {e}")
        
