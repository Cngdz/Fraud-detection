import os
import json
import pandas as pd
import joblib
import xgboost as xgb

# Load artifacts
MODEL_PATH = "/opt/ml/model/xgb_fraud_model.json"
SCALER_PATH = "/opt/ml/model/scaler.pkl"
FEATURE_COLUMNS_PATH = "/opt/ml/model/feature_columns.pkl"

# Load model XGBoost mới (JSON)
model = xgb.XGBClassifier()
model.load_model(MODEL_PATH)

# Load scaler và feature columns
scaler = joblib.load(SCALER_PATH)
feature_columns = joblib.load(FEATURE_COLUMNS_PATH)

# Preprocess JSON input
def preprocess(df):
    # One-hot encode 'type'
    df = pd.get_dummies(df, columns=['type'], drop_first=True)
    
    # Thêm các cột còn thiếu
    for col in feature_columns:
        if col not in df.columns:
            df[col] = 0
    
    # Đảm bảo thứ tự cột
    df = df[feature_columns]
    
    # Scale dữ liệu
    X_scaled = scaler.transform(df)
    return X_scaled

# SageMaker handler functions
def model_fn(model_dir):
    # Return model đã load sẵn
    return model

def input_fn(request_body, content_type='application/json'):
    if content_type == 'application/json':
        input_json = json.loads(request_body)
        return pd.DataFrame([input_json])
    raise ValueError(f"Unsupported content type: {content_type}")

def predict_fn(input_object, model):
    X = preprocess(input_object)
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1]
    return {"prediction": int(y_pred[0]), "probability": float(y_prob[0])}

def output_fn(prediction, content_type='application/json'):
    return json.dumps(prediction)
