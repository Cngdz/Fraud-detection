import json
from sns_publisher import publish_alert

def lambda_handler(event, context):
    """
    Lambda_Alert: nhận event từ Lambda_FraudScoring và gửi SNS
    """
    try:
        publish_alert(event)
        return {"statusCode": 200, "body": json.dumps({"message": "Alert sent"})}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}