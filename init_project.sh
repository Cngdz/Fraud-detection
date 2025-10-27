#!/bin/bash
# Script này tự động tạo cấu trúc thư mục và file cho dự án fraud-detection-service

echo "Bắt đầu tạo cấu trúc dự án..."
echo "------------------------------------------------"

# --- 1. Tạo các thư mục chính ---
echo "[TẠO] Các thư mục chính (docs, infra, scripts, src, tests)..."
mkdir -p docs
mkdir -p infra/iam_roles
mkdir -p scripts
mkdir -p src
mkdir -p tests

# --- 2. Tạo cấu trúc thư mục SRC cho Lambdas ---
echo "[TẠO] Cấu trúc src/ cho các Lambdas..."
mkdir -p src/lambda_process_transaction
mkdir -p src/lambda_fraud_scoring
mkdir -p src/lambda_alert

# --- 3. Tạo cấu trúc thư mục TESTS ---
echo "[TẠO] Cấu trúc tests/..."
mkdir -p tests/test_lambda_process_transaction
mkdir -p tests/test_lambda_fraud_scoring
mkdir -p tests/test_lambda_alert

# --- 4. Tạo các file ở thư mục gốc (root) ---
echo "[TẠO] Các file ở thư mục gốc..."
touch .gitignore
touch README.md
touch requirements-dev.txt

# --- 5. Tạo các file trong /docs ---
echo "[TẠO] Các file trong docs/..."
touch docs/architecture.png
touch docs/api_spec.md
touch docs/runbook.md

# --- 6. Tạo các file trong /infra ---
echo "[TẠO] Các file trong infra/..."
touch infra/iam_roles/lambda_process_role.json
touch infra/iam_roles/lambda_scoring_role.json

# --- 7. Tạo các file trong /scripts ---
echo "[TẠO] Các file trong scripts/..."
touch scripts/load_redis_rules.py
touch scripts/test_api_gw.py
touch scripts/package_lambda.sh

# --- 8. Tạo các file cho src/lambda_process_transaction (Luồng Nóng) ---
echo "[TẠO] File cho 'lambda_process_transaction'..."
touch src/lambda_process_transaction/lambda_function.py
touch src/lambda_process_transaction/rules_engine.py
touch src/lambda_process_transaction/kinesis_publisher.py
touch src/lambda_process_transaction/requirements.txt

# --- 9. Tạo các file cho src/lambda_fraud_scoring (Luồng Lạnh) ---
echo "[TẠO] File cho 'lambda_fraud_scoring'..."
touch src/lambda_fraud_scoring/lambda_function.py
touch src/lambda_fraud_scoring/sagemaker_client.py
touch src/lambda_fraud_scoring/dynamo_writer.py
touch src/lambda_fraud_scoring/alert_invoker.py
touch src/lambda_fraud_scoring/requirements.txt

# --- 10. Tạo các file cho src/lambda_alert (Cảnh báo) ---
echo "[TẠO] File cho 'lambda_alert'..."
touch src/lambda_alert/lambda_function.py
touch src/lambda_alert/sns_publisher.py
touch src/lambda_alert/requirements.txt

# --- 11. Tạo các file cho /tests ---
echo "[TẠO] Các file Unit Test..."
touch tests/test_lambda_process_transaction/test_lambda_function.py
touch tests/test_lambda_process_transaction/test_rules_engine.py

touch tests/test_lambda_fraud_scoring/test_lambda_function.py
touch tests/test_lambda_fraud_scoring/test_sagemaker_client.py

touch tests/test_lambda_alert/test_lambda_function.py

# --- 12. Cấp quyền thực thi cho script đóng gói ---
echo "[CẤP QUYỀN] +x cho scripts/package_lambda.sh"
chmod +x scripts/package_lambda.sh

echo "------------------------------------------------"
echo "✅ Hoàn tất! Cấu trúc dự án đã được tạo thành công."
echo "Hãy kiểm tra lại bằng lệnh 'tree' (nếu bạn đã cài) hoặc 'ls -R'."