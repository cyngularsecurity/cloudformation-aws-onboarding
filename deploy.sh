#!/usr/bin/env bash
set -eu

GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
RESET="\033[0m"

# brew install rain
ClientRegions="eu-west-2,eu-west-1"
CyngularAccountId="468159710337"
OrganizationId="o-6lc0p6io84" # 418853915347,781158784220
RootOUid="r-ozfr"

# Stack1URL="https://onboarding-stacks.s3.eu-west-2.amazonaws.com/Stacks/stack1.yaml"
Stack2URL="https://onboarding-stacks.s3.eu-west-2.amazonaws.com/Stacks/stack2.yaml"
StackSet1URL="https://onboarding-stacks.s3.eu-west-2.amazonaws.com/Stacks/stackset_child1.yaml"
StackSet2URL="https://onboarding-stacks.s3.eu-west-2.amazonaws.com/Stacks/stackset_child2.yaml"

read -rp "Enter the Client Name: " ClientName
read -rp "Enter the Stack Name prefix: " STACK_NAME_PREFIX

echo -e "${BLUE}Starting CloudFormation Stack Deployment with Rain...${RESET}"
# rain info
echo -e "\n${YELLOW}Press Enter to continue with creating the stack, or Ctrl+C to cancel.${RESET}"
read -r

rain deploy \
  --params "ClientName=$ClientName,ClientRegions=$ClientRegions,CyngularAccountId=$CyngularAccountId,OrganizationId=$OrganizationId,RootOUid=$RootOUid,StackSet1URL=$StackSet1URL,Stack2URL=$Stack2URL,StackSet2URL=$StackSet2URL" \
  Stacks/stack1.yaml "$STACK_NAME_PREFIX-$ClientName"
echo -e "${GREEN}Stack created successfully.${RESET}"
# rain fmt
# rain log --chart