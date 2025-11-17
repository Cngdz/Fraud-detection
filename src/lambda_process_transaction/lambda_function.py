import json
from typing import Any, Dict
import redis
import os
from rules_engine import validate_transaction, check_rules
from kinesis_publisher import publish_transaction
from dotenv import load_dotenv
from save_s3 import save_to_s3

load_dotenv()

# Biến môi trường
REDIS_HOST: str = os.getenv("REDIS_HOST", "fraud-cache.xxxxxx.ng.0001.use1.cache.amazonaws.com")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))

# Elasticache
redis_client: redis.Redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True, ssl=True)

def lambda_handler(event: dict, context: Any = None)-> Dict[str, Any]: # gọi qua api gateway thì event thường là 1 dict chứa json data
    print("Lambda start")
    print(f"[ELASTICACHE] Connecting to Elasticache at host: {REDIS_HOST} in port {REDIS_PORT}")
    try:
        # Thử ping để kiểm tra kết nối thực tế
        ping_response = redis_client.ping()
        print(f"[ELASTICACHE] Redis connection test: {'Success' if ping_response else 'Failed'}")

        # Parse event
        transaction: dict = json.loads(event.get("body", event)) # lấy giá trị body, nếu không có thì trả về toàn bộ event
        
        # Validate cơ bản
        validate_transaction(transaction) # kiểm tra sơ khởi định dạng và value của transaction
        
        # Kiểm tra blacklist / rule (ElastiCache)
        rule_result = check_rules(redis_client, transaction) 

        print(rule_result)

        # Nếu bất kỳ rule nào False → lỗi
        if any(rule_result.values()):
            save_to_s3(transaction)
            
            print("[TRANSACTION] transaction failed")
            return {
                "statusCode": 400,
                "status": "Declined",
                # phần body này Api gateway bắt buộc yêu cầu là kiểu string => phải dumps để convert từ dict qua json
                "body": json.dumps({ 
                    "message": "Transaction failed due to rule violation",
                    "rule_result": rule_result
                })
            }

        # Fire-and-forget: Kinesis
        publish_transaction(transaction)    
        print("[TRANSACTION] transaction sucessful")
        
        return {
            "statusCode": 200,
            "status": "Approved",
            "headers": { "Content-Type": "application/json" },
            "body": json.dumps({
                "message": "Transaction processed successfully",
                "rule_result": rule_result
            },default=str)
        }

    except (KeyError, ValueError, TypeError) as e:
        return {
            "statusCode": 400, 
            "status": "Declined",
            "headers": { "Content-Type": "application/json" },
            "body": json.dumps({"error": str(e)},default=str)
        }

    except redis.RedisError as e:
        return {
            "statusCode": 500, 
            "status": "Declined",
            "headers": { "Content-Type": "application/json" },
            "body": json.dumps({"error": f"Elasticache connection failed {e}"}, default=str)
        }

    except Exception as e:
        return {
            "statusCode": 500, 
            "status": "Declined",
            "headers": { "Content-Type": "application/json" },
            "body": json.dumps({"error": str(e)},default=str)
        }
    



"""
{
  "body": "{\"transaction_id\": \"t1\", \"user_id\": \"u1\", \"country\": \"US\", \"amount\": 100, \"timestamp\": \"2025-10-30T10:00:00Z\"}"
}
"""