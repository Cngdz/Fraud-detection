import asyncio
import json
from src.lambda_process_transaction.lambda_function import lambda_handler

event = {
    "body": json.dumps({"user_id": "u1", "transaction_id": "t1", "amount": 100, "timestamp": "2025-10-29T00:00:00Z"})
}

result = asyncio.run(lambda_handler(event))
print(result)