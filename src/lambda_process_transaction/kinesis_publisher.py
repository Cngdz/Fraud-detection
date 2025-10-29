import os
import json
import boto3
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Biến môi trường
AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
KINESIS_STREAM: str= os.getenv("KINESIS_STREAM", "fraud-transactions")
FIREHOSE_STREAM: str = os.getenv("FIREHOSE_STREAM", "fraud-firehose")

# Kinesis Data Stream
kinesis_client = boto3.client("kinesis", region_name=AWS_REGION)

# Firehose (push raw log vào S3)
firehose_client = boto3.client("firehose", region_name=AWS_REGION)

def publish_transaction(transaction: Dict[str, Any]) -> None:
    """
    Fire-and-forget: vừa đẩy Kinesis Data Stream (cho Lambda thứ 3),
    vừa đẩy Firehose (auto lưu raw log vào S3)
    """
    payload_bytes: bytes = json.dumps(transaction).encode("utf-8")

    # Push vào Kinesis Data Stream
    kinesis_client.put_record(
        StreamName=KINESIS_STREAM,
        Data=payload_bytes,
        PartitionKey=str(transaction.get("user_id", "unknown"))
    )

    # Push vào Firehose (raw log S3)
    firehose_client.put_record(
        DeliveryStreamName=FIREHOSE_STREAM,
        Record={"Data": payload_bytes}
    )
