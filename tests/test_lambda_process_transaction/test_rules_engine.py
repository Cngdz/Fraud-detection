import sys
import os
import pytest
from unittest.mock import MagicMock

import redis

# Đưa thư mục gốc (~/src/lambda_process_transaction) vào sys.path để có thể gọi import
# Do mặc định khi chạy python thuần sẽ coi thư mục chứa file là root nên phải thêm/đổi root (khá tù)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/lambda_process_transaction"))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from rules_engine import validate_transaction, check_rules


# ----------------------------------------------------------------
# TESTS CHO validate_transaction
# ----------------------------------------------------------------

def test_validate_transaction_valid_input():
    txn = {
        "transaction_id": "t1",
        "user_id": "u1",
        "country": "VN",
        "amount": 100,
        "timestamp": 123456789,
    }
    # Không raise exception -> pass
    validate_transaction(txn)

def test_validate_transaction_missing_field():
    txn = {
        "transaction_id": "t1",
        "user_id": "u1",
        "amount": 100,
        "timestamp": 123456789,
    }
    # pytest mong đợi đầu ra sẽ trả về lỗi KeyError kèm message missing field: country thì mới pass
    with pytest.raises(KeyError, match="missing field: country"): 
        validate_transaction(txn)

def test_validate_transaction_negative_amount():
    txn = {
        "transaction_id": "t1",
        "user_id": "u1",
        "country": "VN",
        "amount": -10,
        "timestamp": 123456789,
    }
    with pytest.raises(ValueError, match="amount must be positive"):
        validate_transaction(txn)

def test_validate_transaction_zero_amount():
    txn = {
        "transaction_id": "t2",
        "user_id": "u2",
        "country": "US",
        "amount": 0,
        "timestamp": 123456789,
    }
    with pytest.raises(ValueError):
        validate_transaction(txn)

def test_validate_transaction_non_numeric_amount():
    txn = {
        "transaction_id": "t3",
        "user_id": "u3",
        "country": "US",
        "amount": "abc",
        "timestamp": 123456789,
    }
    with pytest.raises(TypeError, match="amount must be numeric"): 
        validate_transaction(txn)

def test_validate_transaction_extra_fields_allowed():
    txn = {
        "transaction_id": "t4",
        "user_id": "u4",
        "country": "VN",
        "amount": 200,
        "timestamp": 123456789,
        "extra": "ok"
    }
    validate_transaction(txn)

def test_validate_transaction_float_amount():
    txn = {
        "transaction_id": "t5",
        "user_id": "u5",
        "country": "JP",
        "amount": 25.5,
        "timestamp": 123456789,
    }
    validate_transaction(txn)

def test_validate_transaction_type_check_strict():
    txn = {
        "transaction_id": "t6",
        "user_id": "u6",
        "country": "VN",
        "amount": None,
        "timestamp": 123456789,
    }
    with pytest.raises(TypeError):
        validate_transaction(txn)

def test_validate_transaction_invalid_field_name():
    txn = {
        "transaction_id": "t7",
        "user": "u7",
        "country": "VN",
        "amount": 100,
        "timestamp": 123456789,
    }
    with pytest.raises(KeyError): # pytest mong đợi đầu ra sẽ trả về lỗi keyerror thì mới pass
        validate_transaction(txn)

def test_validate_transaction_all_fields_valid():
    txn = {
        "transaction_id": "t8",
        "user_id": "u8",
        "country": "US",
        "amount": 999,
        "timestamp": 123456789,
    }
    validate_transaction(txn)


# ----------------------------------------------------------------
# TESTS CHO check_rules
# ----------------------------------------------------------------

# Fixture là một đối tượng/logic mà bạn muốn tái sử dụng trong nhiều testcase
# Khai báo hàm mock sẽ luôn được chạy đầu tiên trước khi run pytest
@pytest.fixture 
def mock_redis():
    """
        MagicMock() tạo một đối tượng giả (mock object) của Python
        có thể gọi bất kỳ method nào trên mock mà Python không báo lỗi, 
        và có thể định nghĩa trả về giá trị cho từng method.
    """
    mock = MagicMock() # Đại diện cho redis_client
    mock.sismember.return_value = False # mặc định gọi sismember sẽ luôn trả về false (trong magicmock)
    mock.incr.return_value = 1 # mặc định gọi hàm incr sẽ luôn trả về 1
    return mock


def test_check_rules_all_clear(mock_redis):
    txn = {"user_id": "u1", "country": "VN"}
    result = check_rules(mock_redis, txn)
    assert result == {"blacklist": False, "country_block": False, "rate_limit": False}
    # lệnh assert sẽ kiểm tra xem result có trả về đúng {"blacklist": False, "country_block": False, "rate_limit": False} không
    # nếu có thì pass, không thì báo lỗi

def test_check_rules_blacklist(mock_redis):
    # .side_effect sẽ loại bỏ hiệu ứng mặc định luôn trả về false của return_value thay bằng lambda key: key == "blacklist_users"
    mock_redis.sismember.side_effect = lambda key, val: key == "blacklist_users"  # key và val tương ứng với 2 agurment truyền vào hàm sismember trong check_rules()
    txn = {"user_id": "u2", "country": "VN"}
    result = check_rules(mock_redis, txn)
    assert result["blacklist"] is True 
    assert result["country_block"] is False 

def test_check_rules_country_block(mock_redis):
    mock_redis.sismember.side_effect = lambda key, val: key == "banned_countries"
    txn = {"user_id": "u3", "country": "US"}
    result = check_rules(mock_redis, txn)
    assert result["country_block"] is True

def test_check_rules_both_blacklist_and_block(mock_redis):
    mock_redis.sismember.side_effect = lambda key, val: True
    mock_redis.incr.side_effect = lambda value: 6  # (value truyền vào hàm mock_redis.incr trong check_rules() là bao nhiều thì luôn return 6)
    txn = {"user_id": "u4", "country": "US"}
    result = check_rules(mock_redis, txn)
    
    assert result["blacklist"] is True
    assert result["country_block"] is True
    assert result["rate_limit"] is True

def test_check_rules_rate_limit_trigger(mock_redis):
    mock_redis.incr.side_effect = [1, 2, 3, 4, 5, 6]  # 6 lần => vượt ngưỡng
    txn = {"user_id": "u5", "country": "VN"}
    for _ in range(5):
        check_rules(mock_redis, txn)
    result = check_rules(mock_redis, txn)
    assert result["rate_limit"] is True

def test_check_rules_redis_error_blacklist(mock_redis):
    mock_redis.sismember.side_effect = redis.RedisError("Simulated error")
    txn = {"user_id": "u6", "country": "VN"}
    with pytest.raises(RuntimeError, match="Redis error when checking blacklist_users"):
        check_rules(mock_redis, txn)

def test_check_rules_redis_error_country(mock_redis):
    def fake_sismember(key, val):
        if key == "banned_countries":
            raise redis.RedisError("fail")
        return False
    mock_redis.sismember.side_effect = fake_sismember
    txn = {"user_id": "u7", "country": "US"}
    with pytest.raises(RuntimeError, match="Redis error when checking banned_countries"):
        check_rules(mock_redis, txn)

def test_check_rules_redis_error_incr(mock_redis):
    mock_redis.incr.side_effect = redis.RedisError("Increment fail")
    txn = {"user_id": "u8", "country": "VN"}
    with pytest.raises(RuntimeError, match="incrementing txn_count"):
        check_rules(mock_redis, txn)

def test_check_rules_incr_first_time_set_expire(mock_redis):
    txn = {"user_id": "u9", "country": "VN"}
    mock_redis.incr.return_value = 1
    result = check_rules(mock_redis, txn)
    mock_redis.expire.assert_called_once()
    assert result["rate_limit"] is False

def test_check_rules_incr_high_value(mock_redis):
    txn = {"user_id": "u10", "country": "VN"}
    mock_redis.incr.return_value = 10
    result = check_rules(mock_redis, txn)
    assert result["rate_limit"] is True


''' 
Để thực thi file pytest chạy lệnh:
    - pytest -v test_rules_engine.py (root ở folder ~tests/test_lambda_process_transaction) # hiển thị chi tiết từng test
    - pytest -s test_rules_engine.py (root ở folder ~tests/test_lambda_process_transaction) # xem cả output print
'''