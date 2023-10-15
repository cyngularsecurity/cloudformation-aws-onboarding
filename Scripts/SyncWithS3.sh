#!/usr/bin/env bash
set -eu

GREEN="\033[32m"
BLUE="\033[34m"
RESET="\033[0m"

BUCKET_NAME="onboarding-stacks"
LOCAL_FILE_PATH="../Stacks"

echo -e "${BLUE}Uploading stacks to S3...${RESET}"
aws s3 sync "$LOCAL_FILE_PATH" "s3://$BUCKET_NAME/"
echo -e "${GREEN}successfully synced with s3://$BUCKET_NAME/${RESET}"
