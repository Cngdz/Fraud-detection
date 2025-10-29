import joblib
import pandas as pd
import json
import os

# Load artifacts
model = joblib.load("/opt/ml/model/xgb_fraud_model.pkl")
scaler = joblib.load("/opt/ml/model/scaler.pkl")
feature_columns = joblib.load("/opt/ml/model/feature_columns.pkl")

# Preprocess JSON input
def preprocess(df):
    # One-hot encode 'type'
    df = pd.get_dummies(df, columns=['type'], drop_first=True)
    
    for col in feature_columns:
        if col not in df.columns:
            df[col] = 0
    
    df = df[feature_columns]  
    X_scaled = scaler.transform(df)
    return X_scaled

# SageMaker handler functions
def model_fn(model_dir):
    return model

def input_fn(request_body, content_type='application/json'):
    if content_type == 'application/json':
        input_json = json.loads(request_body)
        df = pd.DataFrame([input_json])
        return df
    raise ValueError(f"Unsupported content type: {content_type}")

def predict_fn(input_object, model):
    X = preprocess(input_object)
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:,1]
    return {"prediction": int(y_pred[0]), "probability": float(y_prob[0])}

def output_fn(prediction, content_type='application/json'):
    return json.dumps(prediction)
