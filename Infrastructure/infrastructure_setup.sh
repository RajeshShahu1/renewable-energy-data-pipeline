#!/bin/bash

# AWS CLI-based Infrastructure Setup

# install AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-windows.html

# AWS configured
AWS Access Key ID [****************FBSP]:
AWS Secret Access Key [****************66de]:
Default region name [us-west-2]:
Default output format [JSON]:

# Variables 
REGION="us-west-2"
ACCOUNT_ID="<YOUR_ACCOUNT_ID>"
S3_BUCKET="renewable-energy-data1"
DYNAMODB_TABLE="energy_data"
SNS_TOPIC_NAME="energy-anomaly-alerts"
LAMBDA_ROLE_NAME="lambda-energy-role"
LAMBDA_FUNCTION_NAME="ProcessEnergyData"
ZIP_FILE="lambda_function.zip"

# Create S3 Bucket
echo "Creating S3 bucket..."
aws s3api create-bucket \
    --bucket $S3_BUCKET \
    --region $REGION \
    --create-bucket-configuration LocationConstraint=$REGION

# Create DynamoDB Table 
echo "Creating DynamoDB table..."
aws dynamodb create-table \
    --table-name $DYNAMODB_TABLE \
    --attribute-definitions AttributeName=site_id,AttributeType=S AttributeName=timestamp,AttributeType=S \
    --key-schema AttributeName=site_id,KeyType=HASH AttributeName=timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region $REGION

# Create SNS Topic
echo "Creating SNS topic..."
SNS_TOPIC_ARN=$(aws sns create-topic \
    --name $SNS_TOPIC_NAME \
    --region $REGION \
    --output text)
echo "SNS Topic ARN: $SNS_TOPIC_ARN"

# Create IAM Role for Lambda 
echo "Creating IAM role..."
aws iam create-role \
    --role-name $LAMBDA_ROLE_NAME \
    --assume-role-policy-document file://trust-policy.json

# Attach IAM Policies 
echo "Attaching policies to IAM role..."
aws iam attach-role-policy --role-name $LAMBDA_ROLE_NAME --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam attach-role-policy --role-name $LAMBDA_ROLE_NAME --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
aws iam attach-role-policy --role-name $LAMBDA_ROLE_NAME --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
aws iam attach-role-policy --role-name $LAMBDA_ROLE_NAME --policy-arn arn:aws:iam::aws:policy/AmazonSNSFullAccess
aws iam attach-role-policy --role-name $LAMBDA_ROLE_NAME --policy-arn arn:aws:iam::aws:policy/AmazonAPIGatewayAdministrator

# Deploy Lambda Function 
echo "Packaging Lambda function..."
zip $ZIP_FILE lambda_function.py

echo "Creating Lambda function..."
aws lambda create-function \
    --function-name $LAMBDA_FUNCTION_NAME \
    --runtime python3.13 \
    --role arn:aws:iam::$ACCOUNT_ID:role/$LAMBDA_ROLE_NAME \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://$ZIP_FILE \
    --region $REGION

# Create S3 Event Trigger 
echo "Attaching S3 event trigger to Lambda..."
aws s3api put-bucket-notification-configuration \
    --bucket $S3_BUCKET \
    --notification-configuration file://s3_event.json

echo "Infrastructure setup complete !!"
