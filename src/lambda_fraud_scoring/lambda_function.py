# src/lambda_fraud_scoring/lambda_function.py
import json
import base64
import logging
import os
from datetime import datetime

# Import các module tùy chỉnh
from sagemaker_client import get_fraud_prediction
from dynamo_writer import write_transaction_result
from alert_invoker import trigger_alert

# Cấu hình logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Hàm xử lý chính, được trigger bởi Kinesis Data Stream.
    Xử lý một batch record từ Kinesis.
    """
    processed_records = 0
    failed_records = 0

    # 1. Lặp qua từng record trong batch Kinesis
    for record in event.get('Records', []):
        try:
            # 2. Giải mã (decode) data từ Kinesis
            payload_str = base64.b64decode(record['kinesis']['data']).decode('utf-8')
            transaction_data = json.loads(payload_str) # Đây là JSON thô
            
            customer_id = transaction_data.get('nameOrig', 'unknown_id')
            logger.info(f"Đang xử lý record cho: {customer_id}")

            # 3. Gọi SageMaker để chấm điểm (từ sagemaker_client.py)
            # Gửi thẳng JSON thô, nhận về {"prediction": 1, "probability": 0.95}
            sagemaker_result = get_fraud_prediction(transaction_data)

            # 4. Chuẩn bị data để lưu vào DynamoDB
            # Gộp data gốc và kết quả AI
            item_to_save = transaction_data.copy()
            item_to_save['ai_prediction'] = sagemaker_result.get('prediction', -1)
            item_to_save['ai_probability'] = sagemaker_result.get('probability', -1.0)
            item_to_save['cold_path_processed_utc'] = datetime.utcnow().isoformat()
            
            # 5. Ghi kết quả vào DynamoDB (từ dynamo_writer.py)
            write_transaction_result(item_to_save)

            # 6. Kiểm tra gian lận và gửi cảnh báo (nếu cần)
            # Tin tưởng vào kết quả 'prediction' mà model đã xử lý
            if sagemaker_result.get('prediction') == 1:
                probability = sagemaker_result.get('probability')
                logger.warning(f"PHÁT HIỆN GIAN LẬN: {customer_id} | Probability: {probability}")
                
                # Chuẩn bị payload cho Lambda Alert
                alert_payload = {
                    "nameOrig": customer_id,
                    "nameDest": transaction_data.get('nameDest'),
                    "amount": transaction_data.get('amount'),
                    "type": transaction_data.get('type'),
                    "step": transaction_data.get('step'),
                    "ai_probability": probability,
                    "message": f"Nghi ngờ gian lận (Prob: {probability*100:.2f}%) cho KH {customer_id}."
                }
                # Kích hoạt Lambda Alert (từ alert_invoker.py)
                trigger_alert(alert_payload)
            
            processed_records += 1

        except Exception as e:
            logger.error(f"XỬ LÝ THẤT BẠI: {e}")
            logger.error(f"Record data (base64): {record.get('kinesis', {}).get('data')}")
            failed_records += 1
    
    # Hoàn tất
    summary = f"Hoàn tất xử lý batch. Thành công: {processed_records}, Thất bại: {failed_records}"
    logger.info(summary)
    
    return {
        'statusCode': 200,
        'body': json.dumps(summary)
    }