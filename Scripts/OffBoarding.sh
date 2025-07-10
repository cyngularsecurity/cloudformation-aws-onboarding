#!/usr/bin/env bash
set -eo pipefail

export ACCOUNT_ID="528757810539"

export REGION="eu-west-1"
# export REGION="us-west-2"
# export REGION="il-central-1"
# export REGION="eu-north-1"
# export REGION="ca-central-1"
# export REGION="ap-south-1"
# export REGION="sa-east-1"
# export REGION="eu-west-3" ## "us-east-1"
# export REGION="us-west-1" # "ap-southeast-1"
# export REGION="eu-central-1"

export LAMBDA_FUNCTION_1="cyngular-lambda-remove-dns"
export LAMBDA_FUNCTION_2="cyngular-lambda-remove-vpcflowlogs"

export STACKSET_1="cyngular-stackset-mgmt-regional"
export STACKSET_2="cyngular-stackset-2"
export STACKSET_3="cyngular-stackset-1"
export STACKSET_4="cyngular-execution-role-stackset"

# STACK_NAMES=("CyngularOnboarding" "Admin" "Exec")
# STACK_NAMES=("cyngular-onboarding-nemo")

# export AWS_DEFAULT_REGION=$REGION
# assume client_mgmt
echo "Started and region set to $REGION"

RULE_NAME_1="cyngular-lambda-config-dns-rule"
RULE_NAME_2="cyngular-lambda-config-vpcflowlogs-rule"

RULE_EXISTS_1=$(aws events list-rules --name-prefix $RULE_NAME_1 --region $REGION --query 'Rules[?Name==`'$RULE_NAME_1'`].Name' --output text)
RULE_EXISTS_2=$(aws events list-rules --name-prefix $RULE_NAME_2 --region $REGION --query 'Rules[?Name==`'$RULE_NAME_2'`].Name' --output text)

# Check if the EventBridge rule is enabled only if it exists
if [ "$RULE_EXISTS_1" == "$RULE_NAME_1" ]; then
  RULE_STATE_1=$(aws events describe-rule --name $RULE_NAME_1 --region $REGION --query 'State' --output text)
  if [ "$RULE_STATE_1" == "ENABLED" ]; then
    echo "Invoking Lambda function $LAMBDA_FUNCTION_1..."
    aws lambda invoke \
      --region $REGION \
      --function-name $LAMBDA_FUNCTION_1 \
      --payload '{}' /dev/null > /dev/null
    #   --payload '{}'  "${LAMBDA_FUNCTION_1}response.json" > /dev/null
  fi
else
  echo "Rule $RULE_NAME_1 does not exist. Skipping invocation."
fi

if [ "$RULE_EXISTS_2" == "$RULE_NAME_2" ]; then
  RULE_STATE_2=$(aws events describe-rule --name $RULE_NAME_2 --region $REGION --query 'State' --output text)
  if [ "$RULE_STATE_2" == "ENABLED" ]; then
    echo "Invoking Lambda function $LAMBDA_FUNCTION_2..."
    aws lambda invoke \
      --region $REGION \
      --function-name $LAMBDA_FUNCTION_2 \
      --payload '{}' /dev/null > /dev/null
  fi
else
  echo "Rule $RULE_NAME_2 does not exist. Skipping invocation."
fi

echo "Deleting stack instances from StackSets..."
ROOT_ID=$(aws organizations list-roots --query "Roots[0].Id" --output text)
echo "Root ID: $ROOT_ID"

for STACKSET in "$STACKSET_1" "$STACKSET_2" "$STACKSET_3" "$STACKSET_4"
do
    STACKSET_DESCRIPTION=$(aws cloudformation describe-stack-set \
                            --stack-set-name $STACKSET \
                            --query "StackSet.StackSetName" \
                            --output text --region $REGION || echo "")
    
    if [ -z "$STACKSET_DESCRIPTION" ]; then
        echo "StackSet $STACKSET does not exist. Skipping."
        continue
    fi
    
    REGIONS=$(aws cloudformation list-stack-instances \
                --stack-set-name $STACKSET \
                --query "Summaries[].Region" \
                --output text --region $REGION | tr '\t' '\n')
    
    for STACK_INSTANCE_REGION in $REGIONS
    do
      # if REGIONS is empty
      if [ -z "$REGIONS" ]; then
          echo "No stack instances found for $STACKSET. Skipping deletion."
          echo "Deleting empty StackSet $STACKSET..."
          aws cloudformation delete-stack-set --stack-set-name $STACKSET --region $REGION > /dev/null
      fi
      PERMISSION_MODEL=$(aws cloudformation describe-stack-set \
                          --stack-set-name $STACKSET \
                          --query "StackSet.PermissionModel" \
                          --output text --region $REGION)

      if [[ "$PERMISSION_MODEL" == "SERVICE_MANAGED" ]]; then
            operation_in_progress=true
            while $operation_in_progress; do
                echo "Deleting stack instances for SERVICE_MANAGED permission model in StackSet $STACKSET, Region $STACK_INSTANCE_REGION targeting root OU - $ROOT_ID."
                aws cloudformation delete-stack-instances \
                  --stack-set-name $STACKSET \
                  --regions $STACK_INSTANCE_REGION \
                  --deployment-targets OrganizationalUnitIds=$ROOT_ID \
                  --no-retain-stacks \
                  --operation-preferences RegionConcurrencyType=PARALLEL \
                  --region $REGION > /dev/null || {
                    if [ $? -eq 255 ]; then
                        echo "Operation in progress. Waiting for 30 seconds before retrying..."
                        sleep 30
                    else
                        operation_in_progress=false
                    fi
                }
                if [ $? -eq 0 ]; then
                    operation_in_progress=false
                fi
            done
        else
            aws cloudformation delete-stack-instances --stack-set-name $STACKSET --accounts $ACCOUNT_ID --regions $STACK_INSTANCE_REGION --no-retain-stacks --region $REGION > /dev/null
        fi
    done
    
    while :
    do
        INSTANCE_COUNT=$(aws cloudformation list-stack-instances --stack-set-name $STACKSET --query 'Summaries | length(@)' --output text --region $REGION)
        if [ "$INSTANCE_COUNT" -eq 0 ]; then
            echo "All stack instances for $STACKSET are deleted. Proceeding to delete the stack set."
            aws cloudformation delete-stack-set --stack-set-name $STACKSET --region $REGION > /dev/null
            break
        else
            echo "Waiting for stack instances to be deleted for $STACKSET..."
            sleep 30
        fi
    done
done

# for stack in "${STACK_NAMES[@]}"; do
#   aws cloudformation delete-stack --stack-name "$stack" --region $REGION
# done
# echo "Deleting stacks using rain..."
# for STACK in $STACK_1 $STACK_2
# do
#     rain rm $STACK -y
# done