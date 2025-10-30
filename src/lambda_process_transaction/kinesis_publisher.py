import os
import json
import boto3
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Biến môi trường
AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
KINESIS_STREAM_NAME: str= os.getenv("KINESIS_STREAM_NAME", "fraud-transactions")

# Kinesis Data Stream
kinesis_client = boto3.client("kinesis", region_name=AWS_REGION)

def publish_transaction(transaction: Dict[str, Any]) -> None:
    """
    Fire-and-forget: vừa đẩy Kinesis Data Stream (cho Lambda thứ 3),
    vừa đẩy Firehose (auto lưu raw log vào S3)
    """
    payload_bytes: bytes = json.dumps(transaction).encode("utf-8")

    # Push vào Kinesis Data Stream
    kinesis_client.put_record(
        StreamName=KINESIS_STREAM_NAME,
        Data=payload_bytes,
        PartitionKey=str(transaction.get("user_id", "unknown"))
    )

