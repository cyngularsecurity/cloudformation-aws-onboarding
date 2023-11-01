#!/usr/bin/env bash
set -eu

GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
RESET="\033[0m"

ClientRegions="eu-west-2,eu-west-1"
CyngularAccountId="468159710337"
OrganizationId="o-6lc0p6io84" # 418853915347,781158784220
# RootOUid="r-ozfr"

# Stack1URL="https://onboarding-stacks.s3.eu-west-2.amazonaws.com/stack1.yaml"
# Stack2URL="https://onboarding-stacks.s3.eu-west-2.amazonaws.com/stack2.yaml"
# StackSet1URL="https://onboarding-stacks.s3.eu-west-2.amazonaws.com/stackset_child1.yaml"
# StackSet2URL="https://onboarding-stacks.s3.eu-west-2.amazonaws.com/stackset_child2.yaml"

read -rp "Enter the Client Name: " ClientName
read -rp "Enter the Stack Name prefix: " STACK_NAME_PREFIX

echo -e "${BLUE}Starting CloudFormation Stack Deployment with Rain...${RESET}"
# rain info
echo -e "\n${YELLOW}Press Enter to continue with creating the stack, or Ctrl+C to cancel.${RESET}"
read -r

rain deploy Stacks/stack1.yaml "$STACK_NAME_PREFIX-$ClientName" -y --debug \
  --params "ClientName=$ClientName,ClientRegions=$ClientRegions,CyngularAccountId=$CyngularAccountId,OrganizationId=$OrganizationId"
echo -e "${GREEN}Stack created successfully.${RESET}"

# rain fmt
# rain log --chart



# ---------------
# quick create stack url:

https://console.aws.amazon.com/cloudformation/home?region=eu-west-2#/stacks/create/review?stackName=cyngular-onboarding&templateURL=s3://cyngular-onboarding-templates/stack1.yaml&CyngularAccountId=468159710337