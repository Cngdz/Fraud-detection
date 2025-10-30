import os
import boto3

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
sns_client = boto3.client("sns", region_name=AWS_REGION)

def publish_alert(message: str):
    """
    Gửi cảnh báo đến SNS topic thực tế.
    """
    topic_arn = os.getenv("ALERT_TOPIC_ARN")

    if not topic_arn:
        print("[SNS Publisher] ALERT_TOPIC_ARN chưa được cấu hình.")
        return False

    try:
        sns_client.publish(
            TopicArn=topic_arn,
            Subject="CẢNH BÁO GIAO DỊCH GIAN LẬN",
            Message=message
        )
        print(f"[SNS Publisher] Đã gửi cảnh báo đến SNS topic: {topic_arn}")
        return True
    except Exception as e:
        print(f"[SNS Publisher] Lỗi gửi SNS: {e}")
        return False