# src/lambda_fraud_scoring/sagemaker_client.py
import boto3
import os
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Khởi tạo client bên ngoài handler để tái sử dụng
try:
    sagemaker_runtime = boto3.client('sagemaker-runtime')
    # Lấy tên Endpoint từ biến môi trường
    SAGEMAKER_ENDPOINT_NAME = os.environ['SAGEMAKER_ENDPOINT_NAME']
except KeyError:
    logger.error("!!! Lỗi: Biến môi trường 'SAGEMAKER_ENDPOINT_NAME' chưa được set.")
    raise

def get_fraud_prediction(transaction_data):
    """
    Gửi dữ liệu giao dịch (JSON thô) đến SageMaker Endpoint.
    Endpoint sẽ tự xử lý pre-processing.
    """
    
    # Payload chính là JSON thô mà ta nhận được
    payload = json.dumps(transaction_data)

    try:
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=SAGEMAKER_ENDPOINT_NAME,
            ContentType='application/json',
            Body=payload
        )
        
        # Đọc kết quả
        result_body = response['Body'].read().decode('utf-8')
        result_dict = json.loads(result_body)
        
        # Kết quả trả về (do inference.py định nghĩa): 
        # {"prediction": 0, "probability": 0.0012}
        logger.info(f"SageMaker result: {result_dict}")
        return result_dict

    except Exception as e:
        logger.error(f"Lỗi khi gọi SageMaker cho nameOrig {transaction_data.get('nameOrig')}: {e}")
        # Trả về kết quả mặc định nếu lỗi
        return {"prediction": -1, "probability": -1.0, "error_message": str(e)}