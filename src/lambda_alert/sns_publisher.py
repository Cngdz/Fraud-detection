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
        print("[SNS Publisher] ALERT_TOPIC_ARN is not configured")
        return False

    try:
        sns_client.publish(
            TopicArn=topic_arn,
            Subject="FRAUD ALERT",
            Message=message
        )
        print(f"[SNS Publisher] Alert sent to SNS topic: {topic_arn}")
        return True
    except Exception as e:
        print(f"[SNS Publisher] Failed to send SNS alert: {e}")
        return False

