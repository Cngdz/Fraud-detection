from typing import Any, Dict, List
import redis
import time

def validate_transaction(txn: Dict[str, Any]) -> None:
    required: List[str] = ["transaction_id", "user_id", "country", "amount", "timestamp"]

    # kiểm tra đầu vào transaction có chuẩn format required không
    for key in required:
        if key not in txn:
            raise KeyError(f"missing field: {key}")

    # tiền phải > 0
    amount: int = txn["amount"]
    if not isinstance(amount, (int, float)):
        raise TypeError("amount must be numeric")
    if amount <= 0:
        raise ValueError("amount must be positive")

def check_rules(redis_client: redis.Redis, txn: Dict[str, Any]) -> Dict[str, Any]:
    user_id: str = str(txn["user_id"])
    country: str = str(txn["country"])

    result: Dict[str, Any] = {
        "blacklist": False,
        "country_block": False,
        "rate_limit": False,
    }

    # blacklist
    try:
        if redis_client.sismember("blacklist_users", user_id): # nếu có nằm trong danh sách đen thì set mode blacklist = true
            result["blacklist"] = True
    except redis.RedisError as e:
        raise RuntimeError(f"Redis error when checking blacklist_users for user_id={user_id}: {e}") from e

    # banned country
    try:
        if redis_client.sismember("banned_countries", country): # nếu có nằm trong danh sách đen thì set mode country_black = true
            result["country_block"] = True
    except redis.RedisError as e:
        raise RuntimeError(f"Redis error when checking banned_countries for country={country}: {e}") from e 

    # tạo giới hạn 5 lần giao dịch trong 1 giây
    try:
        now_sec: int = int(time.time()) # lấy thời gian hiện tại tính bằng giây
        counter_key: str = f"txn_count:{user_id}:{now_sec}"
        
        count: int = redis_client.incr(counter_key) # type: ignore 
        
        if count == 1: # nếu key vừa được tạo mới lần đầu sẽ set ttl là 2 giây
            redis_client.expire(counter_key, 2) 
        if count > 5: # nếu > 5 thì set mode limit = true
            result["rate_limit"] = True
    except redis.RedisError as e:
        raise RuntimeError(f"Redis error when incrementing txn_count for user_id={user_id}: {e}") from e

    return result




