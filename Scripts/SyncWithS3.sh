#!/usr/bin/env bash
set -eu

RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
BLUE=$(tput setaf 4)
RESET=$(tput sgr0)

BRANCH=$(git branch --show-current)
BUCKET_NAME="cyngular-onboarding-templates"
LOCAL_FILE_PATH="CFN"

aws s3 sync "$LOCAL_FILE_PATH" "s3://$BUCKET_NAME/stacks" --profile prod
aws s3 sync "$LOCAL_FILE_PATH" "s3://$BUCKET_NAME/$BRANCH/stacks" --profile prod
echo -e "${GREEN}synced new On Boarding files with  ----> s3://${BLUE}$BUCKET_NAME/${RED}$BRANCH/${RESET}stacks"
