#!/usr/bin/env bash
set -eu

GREEN="\033[32m"
# BLUE="\033[34m"
RESET="\033[0m"

aws_region="$(aws configure list | grep region | tr -s " " | cut -d" " -f3)"

PROD_BUCKET_NAME="cyngular-onboarding-templates"
DEV_BUCKET_NAME="cyngular-onboarding-templates-dev"
LOCAL_FILE_PATH="../Stacks"

BRANCH=$(git branch --show-current)

aws s3 sync "$LOCAL_FILE_PATH" "s3://$PROD_BUCKET_NAME/stacks" --profile "prod"
echo -e "${GREEN}successfully synced with s3://$PROD_BUCKET_NAME/${RESET}"

aws s3 sync "$LOCAL_FILE_PATH" "s3://$DEV_BUCKET_NAME/stacks" --profile "prod" --region il-central-1
echo -e "${GREEN}successfully synced with s3://$DEV_BUCKET_NAME/${RESET}"
