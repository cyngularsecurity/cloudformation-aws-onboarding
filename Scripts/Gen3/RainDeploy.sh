#!/usr/bin/env bash
set -eu

# Source environment variables
source .env

# Common deployment parameters
REGION="ap-northeast-3"
RUNTIME_PROFILE="client_mgmt"

# Validate required parameters
if [[ -z "${ClientName:-}" ]]; then
  echo "Error: ClientName is required in .env file"
  exit 1
fi

# Create temporary directory for secrets with proper permissions
LOCAL_ARTIFACTS_PATH="${LOCAL_ARTIFACTS_PATH:-"$(mktemp -d)"}"
chmod 700 "${LOCAL_ARTIFACTS_PATH}"
trap 'rm -rf "${LOCAL_ARTIFACTS_PATH}"' EXIT

# Get temporary credentials and store in a secure JSON file
aws sts assume-role \
    --role-arn arn:aws:iam::528757810539:role/GitlabRunnerRole \
    --role-session-name GitlabRunnerSession \
    --duration-seconds 3600 \
    --output json > "${LOCAL_ARTIFACTS_PATH}/credentials.json"

# Export credentials from the JSON file without exposing them in process list
while IFS='=' read -r key value; do
    export "${key}"="${value}"
done < <(jq -r '.Credentials | {"AWS_ACCESS_KEY_ID":.AccessKeyId, "AWS_SECRET_ACCESS_KEY":.SecretAccessKey, "AWS_SESSION_TOKEN":.SessionToken} | to_entries | .[] | "\(.key)=\(.value)"' "${LOCAL_ARTIFACTS_PATH}/credentials.json")

# Verify identity with the new credentials
aws sts get-caller-identity --profile $RUNTIME_PROFILE

STACK_PARAMS="ClientName=$ClientName,\
CyngularAccountId=${CyngularAccountId:-"851565895544"},\
OrganizationId=${OrganizationId:-""},\
CloudTrailBucket=${CloudTrailBucket:-""},\
EnableDNS=${EnableDNS:-"true"},\
EnableEKS=${EnableEKS:-"true"},\
EnableVPCFlowLogs=${EnableVPCFlowLogs:-"true"},\
ServiceManagerOverride=${ServiceManagerOverride:-"1"}"


# Display deployment configuration
echo "Deploying with the parameters:"
echo "  ClientName: $ClientName"
echo "  CyngularAccountId: $CyngularAccountId"
echo "  OrganizationId: ${OrganizationId:-'<not set>'}"
echo "  CloudTrailBucket: ${CloudTrailBucket:-'<will be created>'}"
echo "  EnableDNS: $EnableDNS"
echo "  EnableEKS: $EnableEKS"
echo "  EnableVPCFlowLogs: $EnableVPCFlowLogs"
echo "  ServiceManagerOverride: $ServiceManagerOverride"
echo "  Region: $REGION"
echo "  Profile: $RUNTIME_PROFILE"
echo ""

#### Install zip with templates to local dir:
# curl -s https://raw.githubusercontent.com/Cyngular/Devops/main/Scripts/Gen3/zip.sh | bash
#### Install rain cli
# brew install rain
#### for dev
# rain is dynamic, idempotent

# Deploy ReadonlyRole stack
echo "Deploying ReadonlyRole stack..."
rain deploy ./CFN/Gen3/ReadonlyRole.yaml clipper-ro-role \
    --region ap-northeast-3 \
    --profile $RUNTIME_PROFILE \
    --params "$STACK_PARAMS" \
    --ignore-unknown-params

# Deploy Core stack
echo "Deploying Core stack..."
rain deploy ./CFN/Gen3/Core.yaml clipper-core \
    --region ap-northeast-3 \
    --profile $RUNTIME_PROFILE \
    --params "$STACK_PARAMS" \
    --ignore-unknown-params

# Deploy Services stack
echo "Deploying Services stack..."
rain deploy ./CFN/Gen3/Services.yaml clipper-services \
    --region ap-northeast-3 \
    --profile $RUNTIME_PROFILE \
    --params "$STACK_PARAMS" \
    --ignore-unknown-params
