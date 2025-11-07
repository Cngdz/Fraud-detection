import boto3, json

runtime = boto3.client('sagemaker-runtime', region_name='ap-southeast-2')

sample_json = {
  "step": 1,
  "type": "TRANSFER",
  "amount": 75000000.00,
  "nameOrig": "C999999999",
  "oldbalanceOrg": 75000000.00,
  "newbalanceOrig": 0.00,
  "nameDest": "C111111111",
  "oldbalanceDest": 15000.00,
  "newbalanceDest": 75015000.00
}

response = runtime.invoke_endpoint(
    EndpointName='fraud-detection-endpoint-1',
    ContentType='application/json',
    Body=json.dumps(sample_json)
)

result = json.loads(response['Body'].read().decode())
print(result)   
