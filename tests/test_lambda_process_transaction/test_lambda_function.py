import sys
import os
import json
import pytest
from unittest.mock import patch, MagicMock

# Thêm thư mục src vào sys.path để import module
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/lambda_process_transaction"))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from lambda_function import lambda_handler

# ------------------------------
# Fixture mock publish_transaction (Kinesis)
# ------------------------------
@pytest.fixture
def mock_publish():
    with patch("lambda_function.publish_transaction") as mock_fn:
        yield mock_fn

# ------------------------------
# Fixture mock save_to_s3 (S3)
# ------------------------------
@pytest.fixture
def mock_s3():
    with patch("lambda_function.save_to_s3") as mock_fn:
        yield mock_fn

# ------------------------------
# Fixture mock redis client
# ------------------------------
@pytest.fixture
def mock_redis():
    mock_client = MagicMock()
    with patch("lambda_function.redis_client", mock_client):
        yield mock_client

# ------------------------------
# Test cases
# ------------------------------

def test_successful_transaction(mock_publish, mock_s3, mock_redis):
    # Không vi phạm rule
    mock_redis.sismember.return_value = False
    mock_redis.incr.return_value = 1
    event = {
        "transaction_id": "t1",
        "user_id": "u1",
        "country": "US",
        "amount": 100,
        "timestamp": "2025-10-30T10:00:00Z"
    }
    result = lambda_handler({"body": json.dumps(event)})
    assert result["statusCode"] == 200
    assert "Approved" in result["status"]
    

def test_transaction_violation_blacklist(mock_publish, mock_s3, mock_redis):
    # user nằm trong blacklist
    def sismember_side_effect(key, val):
        return val=="u2"
    mock_redis.sismember.side_effect = sismember_side_effect
    mock_redis.incr.return_value = 1  # rate limit không vi phạm

    event = {
        "transaction_id": "t2",
        "user_id": "u2",
        "country": "US",
        "amount": 50,
        "timestamp": "2025-10-30T10:01:00Z"
    }
    result = lambda_handler({"body": json.dumps(event)})
    assert result["statusCode"] == 400
    assert result["status"] == "Declined"

def test_transaction_violation_country_block(mock_publish, mock_s3, mock_redis):
    # country bị banned
    def sismember_side_effect(key, val):
        return val=="CN"
    mock_redis.sismember.side_effect = sismember_side_effect
    mock_redis.incr.return_value = 1

    event = {
        "transaction_id": "t3",
        "user_id": "u3",
        "country": "CN",
        "amount": 75,
        "timestamp": "2025-10-30T10:02:00Z"
    }
    result = lambda_handler({"body": json.dumps(event)})
    assert result["statusCode"] == 400
    assert result["status"] == "Declined"

def test_transaction_rate_limit(mock_publish, mock_s3, mock_redis):
    mock_redis.sismember.return_value = False
    mock_redis.incr.return_value = 6  # quá limit 5
    event = {
        "transaction_id": "t4",
        "user_id": "u4",
        "country": "US",
        "amount": 120,
        "timestamp": "2025-10-30T10:03:00Z"
    }
    result = lambda_handler({"body": json.dumps(event)})
    assert result["statusCode"] == 400

def test_missing_required_field(mock_publish, mock_s3, mock_redis):
    event = {
        "user_id": "u5",  # thiếu transaction_id
        "country": "US",
        "amount": 50,
        "timestamp": "2025-10-30T10:04:00Z"
    }
    result = lambda_handler({"body": json.dumps(event)})
    assert result["statusCode"] == 400
    assert "missing field" in json.loads(result["body"])["error"]

def test_amount_negative(mock_publish, mock_s3, mock_redis):
    event = {
        "transaction_id": "t6",
        "user_id": "u6",
        "country": "US",
        "amount": -10,
        "timestamp": "2025-10-30T10:05:00Z"
    }
    result = lambda_handler({"body": json.dumps(event)})
    assert result["statusCode"] == 400
    assert "amount must be positive" in json.loads(result["body"])["error"]

def test_amount_non_numeric(mock_publish, mock_s3, mock_redis):
    event = {
        "transaction_id": "t7",
        "user_id": "u7",
        "country": "US",
        "amount": "abc",
        "timestamp": "2025-10-30T10:06:00Z"
    }
    result = lambda_handler({"body": json.dumps(event)})
    assert result["statusCode"] == 400
    assert "amount must be numeric" in json.loads(result["body"])["error"]

def test_redis_connection_error(mock_publish, mock_s3, mock_redis):
    # giả lập RedisError
    mock_redis.sismember.side_effect = Exception("Redis connection failed")
    event = {
        "transaction_id": "t8",
        "user_id": "u8",
        "country": "US",
        "amount": 30,
        "timestamp": "2025-10-30T10:07:00Z"
    }
    result = lambda_handler({"body": json.dumps(event)})
    assert result["statusCode"] == 500
    assert "Redis connection failed" in json.loads(result["body"])["error"]

def test_publish_transaction_exception(mock_publish, mock_s3, mock_redis):
    mock_redis.sismember.return_value = False
    mock_redis.incr.return_value = 1
    mock_publish.side_effect = Exception("Kinesis fail")
    event = {
        "transaction_id": "t9",
        "user_id": "u9",
        "country": "US",
        "amount": 80,
        "timestamp": "2025-10-30T10:08:00Z"
    }
    result = lambda_handler({"body": json.dumps(event)})
    assert result["statusCode"] == 500
    assert "Kinesis fail" in json.loads(result["body"])["error"]

def test_empty_event(mock_publish, mock_s3, mock_redis):
    result = lambda_handler({})
    assert result["statusCode"] == 400
    assert "the JSON object must be str" in json.loads(result["body"])["error"]

''' 
Để thực thi file pytest chạy lệnh:
    - pytest -v test_lambda_function.py (root ở folder ~tests/test_lambda_process_transaction) # hiển thị chi tiết từng test
    - pytest -s test_lambda_function.py (root ở folder ~tests/test_lambda_process_transaction) # xem cả output print
'''