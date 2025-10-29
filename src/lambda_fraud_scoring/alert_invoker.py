# src/lambda_fraud_scoring/alert_invoker.py
import boto3
import os
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Khởi tạo client
try:
    lambda_client = boto3.client('lambda')
    ALERT_LAMBDA_NAME = os.environ['ALERT_LAMBDA_NAME']
except KeyError:
    logger.error("!!! Lỗi: Biến môi trường 'ALERT_LAMBDA_NAME' chưa được set.")
    raise

def trigger_alert(alert_payload):
    """
    Kích hoạt Lambda_Alert (bất đồng bộ).
    """
    try:
        lambda_client.invoke(
            FunctionName=ALERT_LAMBDA_NAME,
            InvocationType='Event', # Bất đồng bộ (fire-and-forget)
            Payload=json.dumps(alert_payload)
        )
        logger.info(f"Đã kích hoạt Lambda_Alert cho: {alert_payload.get('nameOrig')}")
    
    except Exception as e:
        logger.error(f"Lỗi khi kích hoạt Lambda_Alert: {e}")