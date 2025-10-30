import json
from typing import Any, Dict
import asyncio
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
redis_client: redis.Redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def lambda_handler(event: dict)-> Dict[str, Any]: # gọi qua api gateway thì event thường là 1 dict chứa json data
    try:
        # Parse event
        transaction: dict = json.loads(event.get("body", event)) # lấy giá trị body, nếu không có thì trả về toàn bộ event

        # Validate cơ bản
        validate_transaction(transaction) # kiểm tra sơ khởi định dạng và value của transaction

        # Kiểm tra blacklist / rule (ElastiCache)
        rule_result = check_rules(redis_client, transaction) 

        # Nếu bất kỳ rule nào False → lỗi
        if any(rule_result.values()):
            save_to_s3(transaction)

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
        
        return {
            "statusCode": 200,
            "status": "Approved",
            "body": json.dumps({
                "message": "Transaction processed successfully",
                "rule_result": rule_result
            })
        }

    except (KeyError, ValueError, TypeError) as e:
        return {"statusCode": 400, "body": json.dumps({"error": str(e)})}

    except redis.RedisError:
        return {"statusCode": 500, "body": json.dumps({"error": "Elasticache connection failed"})}

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

