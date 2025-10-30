import sys
import os
import pytest
from unittest.mock import patch

# Đưa thư mục gốc (~/src/lambda_alert) vào sys.path để có thể gọi import
# Do mặc định khi chạy python thuần sẽ coi thư mục chứa file là root nên phải thêm/đổi root (khá tù)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/lambda_alert"))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from lambda_function import lambda_handler

''' Test nhưng bỏ qua việc push lên SNS AWS'''

# ------------------------------
# Fixture mock publish_alert
# ------------------------------
@pytest.fixture
def mock_publish():
    ''' 
        Thay thế tạm thời một hàm hoặc biến trong module bằng một mock object 
        Ở đây thay thế hàm publish_alert trong file lambda_function.py và biến mock_fn sẽ đại diện cho nó
        Mỗi lần gọi lambda_function.publish_alert(...) trong test sẽ không chạy thật, mà đi qua mock này
    '''
    with patch("lambda_function.publish_alert") as mock_fn: # đúng file
        yield mock_fn # Hàm publish_alert
        # yield ở fixture giống như return, nhưng pytest cho phép fixture này dọn dẹp sau khi test xong (context manager).
        # Tức là sau khi testcase kết thúc, pytest thực hiện phần code sau yield để kết thúc.

''' 
# ------------------------------
# Có thể thay thế patch bằng magicMock() nhưng phức tạp hơn, cần khôi phục hàm gốc
# ------------------------------
@pytest.fixture 
def mock_publish():d
    original = lambda_function.publish_alert  # lưu hàm gốc
    lambda_function.publish_alert = MagicMock()
    yield lambda_function.publish_alert  # trả mock cho test dùng
    lambda_function.publish_alert = original  # phục hồi hàm gốc sau testcase hoàn tất
'''

# ------------------------------
# Test cases
# ------------------------------

def test_lambda_handler_success(mock_publish):
    mock_publish.return_value = True # Giả lập hàm publish_alert luôn trả về True
    event = {
        "transaction_id": "t1",
        "user_id": "u1",
        "timestamp": "2025-10-30T10:00:00Z",
        "score": "0.95",
        "label": "fraud",
        "violations": {"blacklist": True, "country_block": False}
    }
    result = lambda_handler(event)
    assert result["statusCode"] == 200
    assert "Gửi thông báo thành công" in result["body"]["message"]
    assert "blacklist" in result["body"]["alert_text"]

def test_lambda_handler_no_violations(mock_publish):
    mock_publish.return_value = True
    event = {
        "transaction_id": "t2",
        "user_id": "u2",
        "timestamp": "2025-10-30T10:05:00Z",
        "score": "0.1",
        "label": "safe",
        "violations": {}
    }
    result = lambda_handler(event)
    assert result["statusCode"] == 200
    assert "Không có" in result["body"]["alert_text"]

def test_lambda_handler_missing_fields(mock_publish):
    mock_publish.return_value = True
    event = {}  # empty event
    result = lambda_handler(event)
    assert result["statusCode"] == 200
    assert "unknown" in result["body"]["alert_text"]

def test_lambda_handler_publish_fail(mock_publish):
    mock_publish.return_value = False
    event = {"transaction_id": "t3", "user_id": "u3"}
    result = lambda_handler(event)
    assert result["statusCode"] == 500
    assert "Không gửi được thông báo SNS" in result["body"]["error"]

def test_lambda_handler_multiple_violations(mock_publish):
    mock_publish.return_value = True
    event = {
        "transaction_id": "t4",
        "user_id": "u4",
        "violations": {"blacklist": True, "country_block": True, "rate_limit": True}
    }
    result = lambda_handler(event)
    assert result["statusCode"] == 200
    for rule in ["blacklist", "country_block", "rate_limit"]:
        assert rule in result["body"]["alert_text"]

def test_lambda_handler_timestamp_default(mock_publish):
    mock_publish.return_value = True
    event = {"transaction_id": "t5", "user_id": "u5"}
    result = lambda_handler(event)
    # timestamp phải có dạng ISO string
    assert "Thời gian:" in result["body"]["alert_text"]

def test_lambda_handler_label_uppercase(mock_publish):
    mock_publish.return_value = True
    event = {"transaction_id": "t6", "user_id": "u6", "label": "fraud"}
    result = lambda_handler(event)
    assert "FRAUD" in result["body"]["alert_text"]

def test_lambda_handler_score_default(mock_publish):
    mock_publish.return_value = True
    event = {"transaction_id": "t7", "user_id": "u7"}
    result = lambda_handler(event)
    assert "Điểm AI: N/A" in result["body"]["alert_text"]

def test_lambda_handler_violations_false_values(mock_publish):
    mock_publish.return_value = True
    event = {
        "transaction_id": "t8",
        "user_id": "u8",
        "violations": {"blacklist": False, "country_block": False}
    }
    result = lambda_handler(event)
    assert "Không có" in result["body"]["alert_text"]

def test_lambda_handler_partial_violations(mock_publish):
    mock_publish.return_value = True
    event = {
        "transaction_id": "t9",
        "user_id": "u9",
        "violations": {"blacklist": True, "country_block": False}
    }
    result = lambda_handler(event)
    assert "blacklist" in result["body"]["alert_text"]
    assert "country_block" not in result["body"]["alert_text"]

''' 
Để thực thi file pytest chạy lệnh:
    - pytest -v test_lambda_function.py (root ở folder ~tests/test_lambda_alert) # hiển thị chi tiết từng test
    - pytest -s test_lambda_function.py (root ở folder ~tests/test_lambda_alert) # xem cả output print
'''