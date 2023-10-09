#!/usr/bin/env bash
set -eu

GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
RESET="\033[0m"

# brew install rain

# ClientName="jokers"
# STACK_NAME="onboarding-$ClientName"
# TEMPLATE_FILE="stack1.yaml"
BUCKET_NAME="onboarding-templates-dvir-london"

ClientRegions="eu-west-2,eu-west-1"
# CyngularSideStagingAccountId="468159710337"
# SideStagingOrganizationId="o-1do00dkwuu" #468159710337
# OrganizationId="o-1do00dkwuu" #468159710337

CyngularAccountId="468159710337"

OrganizationId="o-6lc0p6io84" # 418853915347,781158784220
RootOUid="r-ozfr"

# Stack1URL=" https://$BUCKET_NAME.s3.eu-west-2.amazonaws.com/stack1.yaml"
Stack2URL="https://$BUCKET_NAME.s3.eu-west-2.amazonaws.com/stack2.yaml"
StackSet1URL="https://$BUCKET_NAME.s3.eu-west-2.amazonaws.com/stackset_child1.yaml"
StackSet2URL="https://$BUCKET_NAME.s3.eu-west-2.amazonaws.com/stackset_child2.yaml"

read -p "Enter the Client Name: " ClientName
read -p "Enter the Stack Name prefix: " STACK_NAME_PREFIX

# read -p "Enter the S3 Bucket Name: " S3_BUCKET
# read -p "Enter the AWS Account ID: " AWS_ACCOUNT_ID
# read -p "Enter the Organization ID: " ORG_ID

echo -e "${BLUE}Starting CloudFormation Stack Deployment with Rain...${RESET}"

rain info
if rain ls | grep -q "$STACK_NAME_PREFIX"; then
  echo -e "${YELLOW}Stack already exists, updating the stack...${RESET}"
  # Pause and wait for user confirmation
  echo -e "${YELLOW}Press Enter to continue with updating the stack, or Ctrl+C to cancel.${RESET}"
  read -r
  echo -e "${YELLOW}Doing nothing${RESET}"
  # rain deploy \
  #     --params "ClientName=$ClientName,ClientRegions=$ClientRegions,\
  #     CyngularAccountId=$CyngularAccountId,OrganizationId=$OrganizationId,\
  #     RootOUid=$RootOUid,StackSet1URL=$StackSet1URL,\
  #     Stack2URL=$Stack2URL,StackSet2URL=$StackSet2URL" \
  #     "$Stack1URL" "$STACK_NAME"
  echo -e "\n${GREEN}Stack updated successfully.${RESET}"
else
  echo -e "\n${YELLOW}Stack does not exist, creating a new stack...${RESET}"
  echo -e "\n${YELLOW}Press Enter to continue with creating the stack, or Ctrl+C to cancel.${RESET}"
  read -r

  rain deploy \
    --params "ClientName=$ClientName,ClientRegions=$ClientRegions,CyngularAccountId=$CyngularAccountId,OrganizationId=$OrganizationId,RootOUid=$RootOUid,StackSet1URL=$StackSet1URL,Stack2URL=$Stack2URL,StackSet2URL=$StackSet2URL" \
    stack1.yaml "$STACK_NAME_PREFIX-$ClientName"

  echo -e "${GREEN}Stack created successfully.${RESET}"
fi

# rain fmt
# rain log --chart