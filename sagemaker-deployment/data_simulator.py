import boto3
import random
import uuid
import time
from decimal import Decimal
from datetime import datetime
from faker import Faker # Thư viện tạo dữ liệu giả

# --- CẤU HÌNH ---
TABLE_NAME = "fraud-results"       # Tên bảng DynamoDB của bạn
REGION = "ap-southeast-2"    # Thay bằng Region của bạn
NUM_ITEMS_TO_CREATE = 50     # Số lượng bản ghi muốn giả lập
# --- KẾT THÚC CẤU HÌNH ---

# Khởi tạo
dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(TABLE_NAME)
fake = Faker()

print(f"Bắt đầu giả lập {NUM_ITEMS_TO_CREATE} bản ghi vào bảng '{TABLE_NAME}'...")

for i in range(NUM_ITEMS_TO_CREATE):
    
    # 1. Giả lập dữ liệu giao dịch cơ bản
    is_fraud = random.choice([True, False]) # 50% cơ hội là gian lận
    tx_type = random.choice(['PAYMENT', 'TRANSFER', 'CASH_OUT'])
    amount = round(random.uniform(100.0, 99999.0), 2)
    name_orig = f"C{fake.numerify(text='#########')}"
    name_dest = f"M{fake.numerify(text='#########')}"

    # 2. Giả lập kết quả AI (dựa trên is_fraud)
    if is_fraud:
        ai_prediction_label = 1
        ai_probability = round(random.uniform(0.75, 0.99), 5)
        print(f"  -> Đang tạo [GIAN LẬN] {name_orig}...")
    else:
        ai_prediction_label = 0
        ai_probability = round(random.uniform(0.01, 0.30), 5)
        print(f"  -> Đang tạo [TỐT] {name_orig}...")

    # 3. Tạo item đầy đủ (giống hệt output của L_COLD)
    # QUAN TRỌNG: DynamoDB yêu cầu số thực (float) phải được
    # chuyển đổi sang kiểu Decimal.
    item = {
        'transactionId': str(uuid.uuid4()), # Partition Key
        'step': random.randint(1, 100),
        'type': tx_type,
        'amount': Decimal(str(amount)), # Chuyển đổi sang Decimal
        'nameOrig': name_orig,
        'nameDest': name_dest,
        'oldbalanceOrg': Decimal(str(random.uniform(0.0, 100000.0))),
        'newbalanceOrig': Decimal(str(random.uniform(0.0, 100000.0))),
        'oldbalanceDest': Decimal(str(random.uniform(0.0, 100000.0))),
        'newbalanceDest': Decimal(str(random.uniform(0.0, 100000.0))),
        
        # Kết quả AI
        'ai_prediction_label': ai_prediction_label,
        'ai_probability': Decimal(str(ai_probability)), # Chuyển đổi sang Decimal
        'cold_path_processed_utc': datetime.utcnow().isoformat()
    }

    # 4. Lưu vào DynamoDB
    try:
        table.put_item(Item=item)
        
    except Exception as e:
        print(f"LỖI khi ghi vào DynamoDB: {e}")
    
    # Tạm dừng một chút để không làm quá tải
    time.sleep(0.1) 

print(f"\nHoàn tất! Đã lưu {NUM_ITEMS_TO_CREATE} bản ghi.")
print("Bây giờ hãy kiểm tra Dashboard OpenSearch (nếu đã bật Stream).")