import boto3
import json
import logging

sns_client = boto3.client("sns", region_name="us-east-1")  # ⬅ 你用的 region

TOPIC_ARN = "arn:aws:sns:us-east-1:408485681593:animal-threat-alert"

def publish_threat_alert(message: dict):
    try:
        response = sns_client.publish(
            TopicArn=TOPIC_ARN,
            Subject="⚠️ Animal Threat Detected",
            Message=json.dumps(message, indent=2)
        )
        logging.info("SNS MessageId: %s", response["MessageId"])
    except Exception as e:
        logging.error("❌ Failed to publish SNS message: %s", e)
        

message = {"msg": "There is a tiger nearby you"}
publish_threat_alert(message)