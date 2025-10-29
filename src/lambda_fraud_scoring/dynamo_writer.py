# src/lambda_fraud_scoring/dynamo_writer.py
import boto3
import os
import logging
from decimal import Decimal
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Hàm trợ giúp để chuyển đổi float sang Decimal
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, float):
            # Chuyển đổi float sang string rồi sang Decimal
            return Decimal(str(obj))
        return super(DecimalEncoder, self).default(obj)

# Khởi tạo client bên ngoài
try:
    dynamodb = boto3.resource('dynamodb')
    TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']
    table = dynamodb.Table(TABLE_NAME)
except KeyError:
    logger.error("!!! Lỗi: Biến môi trường 'DYNAMODB_TABLE_NAME' chưa được set.")
    raise

def write_transaction_result(item_to_save):
    """
    Ghi 1 item vào DynamoDB, xử lý float -> Decimal.
    """
    try:
        # Sử dụng json.loads với DecimalEncoder để chuyển đổi toàn bộ dict
        # Cách này xử lý tất cả các giá trị float (amount, balances...)
        item_decimal = json.loads(json.dumps(item_to_save), parse_float=Decimal)
        
        # Dùng nameOrig + step làm Primary Key (ví dụ)
        # Bạn cần định nghĩa Primary Key khi tạo bảng DynamoDB
        # Ở đây tôi giả định 'nameOrig' là Partition Key và 'step' là Sort Key
        table.put_item(Item=item_decimal)
        logger.info(f"Đã ghi vào DynamoDB: {item_decimal.get('nameOrig')} tại step {item_decimal.get('step')}")
    
    except Exception as e:
        logger.error(f"Lỗi khi ghi vào DynamoDB cho item {item_to_save.get('nameOrig')}: {e}")
        # Không raise, để các record khác trong batch tiếp tục được xử lý