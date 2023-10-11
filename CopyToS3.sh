#!/usr/bin/env bash
set -eu

GREEN="\033[32m"
BLUE="\033[34m"
RESET="\033[0m"

BUCKET_NAME="Src"
REGION="us-east-1"
LOCAL_FILE_PATH="/path/to/local/file"
TARGET_S3_KEY="path/in/s3/object"
# KEY_PATH_FOR_LATER="path/in/s3/for_later"

echo -e "${BLUE}Creating S3 bucket: ${BUCKET_NAME}${RESET}"
# aws s3 mb s3://$BUCKET_NAME --region $REGION
aws s3 mb --bucket $BUCKET_NAME --region $REGION --create-bucket-configuration LocationConstraint=$REGION
echo -e "${GREEN}S3 bucket ${BUCKET_NAME} created successfully.${RESET}"

echo -e "${BLUE}Uploading stacks to S3...${RESET}"
aws s3 cp $LOCAL_FILE_PATH s3://$BUCKET_NAME/$TARGET_S3_KEY
echo -e "${GREEN}uploaded successfully to s3://$BUCKET_NAME/$TARGET_S3_KEY${RESET}"
