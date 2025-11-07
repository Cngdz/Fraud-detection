import sagemaker
from sagemaker.xgboost import XGBoostModel

region = 'ap-southeast-2'   # thay region của bạn
sagemaker_session = sagemaker.Session()
role = sagemaker.get_execution_role()  # thay role ARN

model_s3_path = 's3://fraud-model-buckets/modell.tar.gz'

xgb_model = XGBoostModel(
    model_data=model_s3_path,         # tar.gz chứa inference.py + các .pkl
    role=role,
    entry_point='inference.py',       # file xử lý input/output
    framework_version='1.7-1',        # phiên bản XGBoost container
    sagemaker_session=sagemaker_session
)

# Deploy endpoint
endpoint_name = 'fraud-detection-endpoint-1'   # đổi nếu trùng
predictor = xgb_model.deploy(
    initial_instance_count=1,
    instance_type='ml.t2.medium',
    endpoint_name=endpoint_name
)

print("Endpoint deployed:", endpoint_name)
