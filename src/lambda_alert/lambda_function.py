from datetime import datetime, timezone
import time
from typing import Any, Dict
from sns_publisher import publish_alert   # chuẩn bị sẵn, dù phần 1 chưa gửi thật

def lambda_handler(event: dict, context: Any = None) -> dict:
    # Event đến trực tiếp từ Lambda_FraudScoring
    device: str = event.get("nameDest", "unknown")
    user: str = event.get("nameOrig", "unknown")
    score: str = event.get("score", "N/A")
    label: str = event.get("label", "N/A")
    violations: Dict[str, str] = event.get("violations", {}) # list các vi phạm (maybe nếu cần)

    violated_rules: list = [k for k, v in violations.items() if v]
    violated_text: str = ", ".join(violated_rules) if violated_rules else "None"

    # Format nội dung cảnh báo (SNS chỉ chấp nhận là string)

    alert_message: str = (
        f"FRAUD ALERT\n"
        f"-------------------------------------\n"
        f"Type: {type}\n"
        f"User: {user}\n"
        f"Device =: {device}\n"
        f"AI Score: {score}\n"
        f"Label: {label.upper()}\n"
        f"Violated Rules: {violated_text}\n"
        f"-------------------------------------\n"
        f"This transaction was flagged by the automated fraud detection system."
    )

    print("Lambda start")

    # Publish notify to SNS
    success = publish_alert(alert_message)

    if not success:
        print("[SNS Publisher] SNS publish failed")
        return {
            "statusCode": 500,
            "body": {
                "error": "Failed to send SNS alert"
            }
        }

    print("[SNS Publisher] SNS publish succeeded")
    return {
        "statusCode": 200,
        "body": {
            "message": "SNS alert sent successfully",
            "alert_text": alert_message
        }
    }
