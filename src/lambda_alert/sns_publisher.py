import boto3
import os
import json

sns = boto3.client("sns", region_name=os.getenv("AWS_REGION"))
TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "")

def publish_alert(event):
    sns.publish(
        TopicArn=TOPIC_ARN,
        Message=json.dumps(event),
        Subject="Fraud Alert"
    )
