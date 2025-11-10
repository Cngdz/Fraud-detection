import json
import base64
import logging
import os
import boto3
from datetime import datetime
from decimal import Decimal
import uuid

# Cấu hình logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# --- Bắt đầu phần code của dynamo_writer.py ---

# Hàm trợ giúp để chuyển đổi float sang Decimal
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, float):
            # Chuyển đổi float sang string rồi sang Decimal
            return Decimal(str(obj))
        return super(DecimalEncoder, self).default(obj)

try:
    dynamodb = boto3.resource('dynamodb')
    DYNAMODB_TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)
except KeyError:
    logger.error("!!! Lỗi: Biến môi trường 'DYNAMODB_TABLE_NAME' chưa được set.")
    raise

def write_transaction_result(item_to_save):
    """
    Ghi 1 item vào DynamoDB, xử lý float -> Decimal.
    """
    try:
        # Sử dụng json.loads với DecimalEncoder để chuyển đổi toàn bộ dict
        item_decimal = json.loads(json.dumps(item_to_save), parse_float=Decimal)
        
        # Giả định 'nameOrig' là Partition Key và 'step' là Sort Key
        table.put_item(Item=item_decimal)
        logger.info(f"Đã ghi vào DynamoDB (PK): {item_decimal.get('transactionId')}")
    
    except Exception as e:
        logger.error(f"Lỗi khi ghi vào DynamoDB cho item (PK: {item_to_save.get('transactionId')}): {e}")
        # Không raise, để các record khác trong batch tiếp tục được xử lý

# --- Kết thúc phần code của dynamo_writer.py ---


# --- Bắt đầu phần code của sagemaker_client.py ---

try:
    sagemaker_runtime = boto3.client('sagemaker-runtime')
    SAGEMAKER_ENDPOINT_NAME = os.environ['SAGEMAKER_ENDPOINT_NAME']
except KeyError:
    logger.error("!!! Lỗi: Biến môi trường 'SAGEMAKER_ENDPOINT_NAME' chưa được set.")
    raise

def get_fraud_prediction(transaction_data):
    """
    Gửi dữ liệu giao dịch (JSON thô) đến SageMaker Endpoint.
    """
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
        # Ví dụ: {"pred_label": 1, "probability": 0.95}
        logger.info(f"SageMaker result: {result_dict}")
        return result_dict

    except Exception as e:
        logger.error(f"Lỗi khi gọi SageMaker cho nameOrig {transaction_data.get('nameOrig')}: {e}")
        # Trả về kết quả mặc định nếu lỗi
        return {"pred_label": -1, "probability": -1.0, "error_message": str(e)}

# --- Kết thúc phần code của sagemaker_client.py ---


# --- Bắt đầu phần code của alert_invoker.py ---

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

# --- Kết thúc phần code của alert_invoker.py ---


# --- Bắt đầu Hàm Handler chính (từ lambda_function.py) ---

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

            # 3. Gọi SageMaker để chấm điểm (dùng hàm nội bộ)
            # Gửi thẳng JSON thô, nhận về {"pred_label": 1, "probability": 0.95}
            sagemaker_result = get_fraud_prediction(transaction_data)

            # 4. Chuẩn bị data để lưu vào DynamoDB
            # Gộp data gốc và kết quả AI
            item_to_save = transaction_data.copy()
            # Tự tạo Partition Key duy nhất (UUID)
            item_to_save['transactionId'] = str(uuid.uuid4())
            # Đọc kết quả từ SageMaker
            pred_label = sagemaker_result.get('prediction', -1)
            probability = sagemaker_result.get('probability', -1.0)
            
            item_to_save['ai_prediction_label'] = pred_label
            item_to_save['ai_probability'] = probability
            item_to_save['cold_path_processed_utc'] = datetime.utcnow().isoformat()
            
            # 5. Ghi kết quả vào DynamoDB (dùng hàm nội bộ)
            write_transaction_result(item_to_save)

            # 6. Kiểm tra gian lận và gửi cảnh báo (nếu cần)
            # *** ĐÃ CẬP NHẬT: Dùng 'pred_label' == 1 ***
            if pred_label == 1:
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
                # Kích hoạt Lambda Alert (dùng hàm nội bộ)
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

# --- Kết thúc Hàm Handler chính ---