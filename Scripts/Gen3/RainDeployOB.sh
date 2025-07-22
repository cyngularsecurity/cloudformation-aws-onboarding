#!/usr/bin/env bash
set -eu

# Check if script is being run from the project root
if [[ ! -d "Scripts" ]] || [[ ! -d "CFN" ]] || [[ ! -f ".env" ]]; then
  echo "Error: This script must be run from the root of the project where Scripts and CFN directories exist"
  echo "Current directory: $(pwd)"
  exit 1
fi

source .env

readonly RUNTIME_REGION="ap-northeast-3"
readonly RUNTIME_PROFILE="client_mgmt"

if [[ -z "${ClientName:-}" ]]; then
  echo "Error: ClientName is required in .env file"
  exit 1
fi



# LOCAL_ARTIFACTS_PATH="${LOCAL_ARTIFACTS_PATH:-"$(mktemp -d)"}"
# chmod 700 "${LOCAL_ARTIFACTS_PATH}"
# trap 'rm -rf "${LOCAL_ARTIFACTS_PATH}"' EXIT

# aws sts assume-role \
#     --role-arn arn:aws:iam::528757810539:role/GitlabRunnerRole \
#     --role-session-name GitlabRunnerSession \
#     --duration-seconds 3600 \
#     --output json > "${LOCAL_ARTIFACTS_PATH}/credentials.json"

# Verify identity with the new credentials
aws sts get-caller-identity --profile $RUNTIME_PROFILE

STACK_PARAMS="ClientName=$ClientName,\
CyngularAccountId=${CyngularAccountId:-"851565895544"},\
OrganizationId=${OrganizationId:-""},\
ExcludedRegions=${ExcludedRegions:-""},\
CloudTrailBucket=${CloudTrailBucket:-""},\
EnableDNS=${EnableDNS:-"true"},\
EnableEKS=${EnableEKS:-"true"},\
EnableVPCFlowLogs=${EnableVPCFlowLogs:-"true"},\
ServiceManagerOverride=${ServiceManagerOverride:-"1"}"

echo "Deploying with the parameters:"
echo "  STACK_PARAMS:"
echo "$(echo $STACK_PARAMS | sed 's/,/,\n    /g')"
echo "  Region: $RUNTIME_REGION"
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
# rain forecast --experimental CFN/Gen3/ReadonlyRole.yaml ${ClientName}-ro-role \
#     --params ClientName=${ClientName}

rain deploy ./CFN/Gen3/ReadonlyRole.yaml "${ClientName}-ro-role" \
    --region $RUNTIME_REGION \
    --profile $RUNTIME_PROFILE \
    --params "$STACK_PARAMS" \
    --ignore-unknown-params

# Deploy Core stack
echo "Deploying Core stack..."
rain deploy ./CFN/Gen3/Core.yaml "${ClientName}-core" \
    --region $RUNTIME_REGION \
    --profile $RUNTIME_PROFILE \
    --params "$STACK_PARAMS" \
    --ignore-unknown-params

# Deploy Services stack
echo "Deploying Services stack..."
rain deploy ./CFN/Gen3/Services.yaml "${ClientName}-services" \
    --region $RUNTIME_REGION \
    --profile $RUNTIME_PROFILE \
    --params "$STACK_PARAMS" \
    --ignore-unknown-params