from typing import Any, Dict, List
import redis
import time

def validate_transaction(txn: Dict[str, Any]) -> None:
    required: List[str] = [
        "type",
        "nameOrig",
        "nameDest",
        "oldbalanceOrg",
        "newbalanceOrig",
        "amount",
        "oldbalanceDest",
        "newbalanceDest"
    ]

    # kiểm tra đầu vào transaction có chuẩn format required không
    for key in required:
        if key not in txn:
            raise KeyError(f"Missing field: {key}")

def check_rules(redis_client: redis.Redis, txn: Dict[str, Any]) -> Dict[str, Any]:
    user: str = str(txn["nameOrig"])
    device: str = str(txn["nameDest"])
    type: str = str(txn["type"])

    result: Dict[str, Any] = {
        "blackUser": False,
        "blackDevice": False,
        "SpawmOver5PerMinute": False,
    }

    # tiền phải > 0
    amount: int = txn["amount"]
    if not isinstance(amount, (int, float)):
        raise TypeError("Amount must be numeric")
    if amount <= 0:
        raise ValueError("Amount must be positive")

    # black user
    try:
        if redis_client.sismember("blacklist:nameOrig", user): # nếu có nằm trong danh sách đen thì set mode blacklist = true
            result["blackUser"] = True
    except redis.RedisError as e:
        raise RuntimeError(f"Redis error when checking blackUser for user={user}: {e}") from e

    # black device
    try:
        if redis_client.sismember("blacklist:nameDes", device): # nếu có nằm trong danh sách đen thì set mode country_black = true
            result["blackDevice"] = True
    except redis.RedisError as e:
        raise RuntimeError(f"Redis error when checking blackDevice for device={device}: {e}") from e 

    # tạo giới hạn 5 lần giao dịch trong 1 giây
    try:
        counter_key: str = f"{type}:txnCount:{user}:{device}"
        
        count: int = redis_client.incr(counter_key) # type: ignore 
        
        if count == 1: # nếu key vừa được tạo mới lần đầu sẽ set ttl là 60 giây
            redis_client.expire(counter_key, 60) 
        if count > 5: # nếu > 5 thì set mode limit = true
            result["SpawmOver5PerMinute"] = True
    except redis.RedisError as e:
        raise RuntimeError(f"Redis error when incrementing txnCount for user={user}: {e}") from e

    return result