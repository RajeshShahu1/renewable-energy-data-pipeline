import json
import boto3
from decimal import Decimal

# Trigger CI/CD test
git add lambda_function/lambda_function.py
git commit -m "Test GitHub Actions deployment"
git push origin main


# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('energy_data')  

sns = boto3.client('sns')
SNS_TOPIC_ARN = "arn:aws:sns:us-west-2:866174429909:energy-anomaly-alerts"

def lambda_handler(event, context):
    print("Lambda triggered.")

    s3 = boto3.client('s3')

    try:
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            print(f"Processing file: {key} from bucket: {bucket}")

            # Fetch the file content from S3
            obj = s3.get_object(Bucket=bucket, Key=key)
            body = obj['Body'].read().decode('utf-8')

            try:
                data = json.loads(body)
            except json.JSONDecodeError as e:
                print(f"[ERROR] Failed to parse JSON: {str(e)}")
                return {"statusCode": 400, "body": "Invalid JSON format."}

            # Process each record in the file
            for item in data:
                try:
                    site_id = str(item.get('site_id'))
                    timestamp = str(item.get('timestamp'))
                    gen = Decimal(str(item.get('energy_generated_kwh')))
                    con = Decimal(str(item.get('energy_consumed_kwh')))
                    net = gen - con
                    anomaly = gen < 0 or con < 0

                    item_to_insert = {
                        'site_id': site_id,
                        'timestamp': timestamp,
                        'energy_generated_kwh': gen,
                        'energy_consumed_kwh': con,
                        'net_energy_kwh': net,
                        'anomaly': anomaly
                    }
                    
                    print("Inserting item:")
                    print(json.dumps(item_to_insert, indent=2, default=str))

                    response = table.put_item(Item=item_to_insert)
                    print("PutItem response:")
                    print(json.dumps(response, indent=2, default=str))

                    # Send SNS alert if anomaly is detected
                    if anomaly:
                        message = (
                            f"⚠️ Anomaly Detected!\n\n"
                            f"Site ID: {site_id}\n"
                            f"Timestamp: {timestamp}\n"
                            f"Generated: {gen} kWh\n"
                            f"Consumed: {con} kWh\n"
                        )
                        sns.publish(
                            TopicArn=SNS_TOPIC_ARN,
                            Subject="Energy Anomaly Alert",
                            Message=message
                        )
                        print(f"[SNS] Alert sent for site {site_id}")
                        
                except Exception as insert_error:
                    print(f"[ERROR] Failed to insert item: {str(insert_error)}")

        return {"statusCode": 200, "body": "File processed successfully."}

    except Exception as e:
        print(f"[ERROR] Lambda failed: {str(e)}")
        raise e

