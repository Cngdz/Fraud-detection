import os
import json
import requests
from requests.auth import HTTPBasicAuth
from boto3.dynamodb.types import TypeDeserializer
from datetime import datetime

# Environment variables
OS_HOST = os.environ['OS_HOST']           # ví dụ: search-fraud-dashboard-domain-xxxx.es.amazonaws.com
OS_INDEX_NAME = "fraud_index"
OS_USER = os.environ['OS_USER']           # master username từ Fine-grained access control
OS_PASSWORD = os.environ['OS_PASSWORD']   # master password

deserializer = TypeDeserializer()

def unmarshall(dynamo_obj):
    print("Unmarshalling DynamoDB object...")
    result = {k: deserializer.deserialize(v) for k, v in dynamo_obj.items()}

    # Chuyển created_utc sang ISO8601 date
    if 'created_utc' in result:
        # Dynamo gửi string như "2025-11-15T14:04:00Z"
        try:
            dt = datetime.strptime(result['created_utc'], "%Y-%m-%dT%H:%M:%SZ")
            # Chuyển thành "2025-11-15T14:04:00" hoặc giữ Z nếu muốn UTC
            result['created_utc'] = dt.isoformat() + "Z"
        except Exception as e:
            print(f"WARNING: cannot parse created_utc: {result['created_utc']} -> {e}")

    print("Unmarshalled:", result)
    return result

def lambda_handler(event, context):
    print("===== Lambda START =====")
    print("Event received:")
    print(json.dumps(event, indent=2))

    headers = {"Content-Type": "application/json"}

    try:
        for record in event.get('Records', []):
            print("\n--- Processing new record ---")
            event_name = record.get('eventName')
            print("Event Name:", event_name)

            if event_name == 'INSERT':
                print("INSERT event detected")

                new_image = record['dynamodb']['NewImage']
                print("NewImage raw:", new_image)

                doc = unmarshall(new_image)
                doc_id = doc.get('transactionId')

                if not doc_id:
                    print("ERROR: transactionId not found in document")
                    continue

                url = f"https://{OS_HOST}/{OS_INDEX_NAME}/_doc/{doc_id}"
                print(f"Final request URL: {url}")
                print(f"Sending document to OpenSearch: {doc}")

                response = requests.put(
                    url,
                    auth=HTTPBasicAuth(OS_USER, OS_PASSWORD),
                    json=doc,
                    headers=headers
                )

                print("OpenSearch Response:")
                print(response.text)

    except Exception as e:
        print(f"Lambda ERROR: {e}")

    print("===== Lambda END =====")
    return {"status": "done"}


# fraud-dashboard-domain