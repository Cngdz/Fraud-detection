from datetime import datetime, timezone
from typing import Dict
from sns_publisher import publish_alert   # chuẩn bị sẵn, dù phần 1 chưa gửi thật

def lambda_handler(event: dict) -> dict:
    # Trường hợp event đến trực tiếp từ Lambda_FraudScoring
    transaction_id: str = event.get("transaction_id", "unknown")
    user_id: str = event.get("user_id", "unknown")
    timestamp: datetime = event.get("timestamp", datetime.now(timezone.utc).isoformat())
    score: str = event.get("score", "N/A")
    label: str = event.get("label", "N/A")
    violations: Dict[str, str] = event.get("violations", {}) # list các vi phạm (maybe nếu cần)

    violated_rules: list = [k for k, v in violations.items() if v]
    violated_text: str = ", ".join(violated_rules) if violated_rules else "Không có"

    # Format nội dung cảnh báo (SNS chỉ chấp nhận là string)
    alert_message: str = (
        f"CẢNH BÁO GIAO DỊCH GIAN LẬN\n"
        f"-------------------------------------\n"
        f"User ID: {user_id}\n"
        f"Transaction ID: {transaction_id}\n"
        f"Thời gian: {timestamp}\n"
        f"Điểm AI: {score}\n"
        f"Đánh giá: {label.upper()}\n"
        f"Quy tắc vi phạm: {violated_text}\n"
        f"-------------------------------------\n"
        f"Hệ thống phát hiện gian lận tự động."
    )

    success = publish_alert(alert_message)

    if not success:
        return {
            "statusCode": 500,
            "body": {
                "error": "Không gửi được thông báo SNS"
            }
        }

    return {
        "statusCode": 200,
        "body": {
            "message": "Gửi thông báo thành công",
            "alert_text": alert_message
        }
    }
