#!/usr/bin/env bash
set -eu

# rain fmt
# rain log --chart

if [[ ! -d "Scripts" ]] || [[ ! -d "CFN" ]] || [[ ! -f ".env" ]]; then
  echo "Error: This script must be run from the root of the project where Scripts and CFN directories exist"
  echo "Current directory: $(pwd)"
  exit 1
fi

source .env

STACK_PARAMS="ClientName=$CLIENT_NAME,\
CyngularAccountId=${CYNGULAR_ACCOUNT_ID:-"851565895544"},\
OrganizationId=${ORGANIZATION_ID:-""},\
ExcludedRegions=${ExcludedRegions:-""},\
CloudTrailBucket=${CloudTrailBucket:-""},\
EnableDNS=${EnableDNS:-"true"},\
EnableEKS=${EnableEKS:-"true"},\
EnableVPCFlowLogs=${EnableVPCFlowLogs:-"true"},\
EnableBucketPolicyManager=${EnableBucketPolicyManager:-"true"},\
ServiceManagerOverride=${ServiceManagerOverride:-"1"},\
ClientMgmtAccountId=${ClientMgmtAccountId:-""}"

echo "Deploying with the parameters:"
echo "  STACK_PARAMS:"
echo "$(echo $STACK_PARAMS | sed 's/,/,\n    /g')"
echo "  Region: $RUNTIME_REGION"
echo "  Profile: $RUNTIME_PROFILE"
echo ""

#### Install zip with templates to local dir:
# curl -s https://raw.githubusercontent.com/Cyngular/Devops/main/Scripts/zip.sh | bash
#### Install rain cli
# brew install rain
#### for dev
# rain is dynamic, idempotent

# Deploy ReadonlyRole stack
echo "Deploying ReadonlyRole stack..."
# rain forecast --experimental CFN/ReadonlyRole.yaml ${ClientName}-ro-role \
#     --params ClientName=${ClientName}

rain deploy ./CFN/ReadonlyRole.yaml "${CLIENT_NAME}-ro-role" \
    --region $RUNTIME_REGION \
    --profile $RUNTIME_PROFILE \
    --params "$STACK_PARAMS" \
    --ignore-unknown-params \
    --yes --keep

# Deploy Core stack
echo "Deploying Core stack..."
rain deploy ./CFN/Core.yaml "${CLIENT_NAME}-core" \
    --region $RUNTIME_REGION \
    --profile $RUNTIME_PROFILE \
    --params "$STACK_PARAMS" \
    --ignore-unknown-params \
    --yes --keep

# Deploy Services stack
echo "Deploying Services stack..."
rain deploy ./CFN/Services.yaml "${CLIENT_NAME}-services" \
    --region $RUNTIME_REGION \
    --profile $RUNTIME_PROFILE \
    --params "$STACK_PARAMS" \
    --ignore-unknown-params \
    --yes --keep


### Stacksets [does not currently support 'ignore-unknown-params']
#### All in single region deployment

### ReadonlyRole StackSet
ROLE_STACKSET_PARAMS="ClientName=$CLIENT_NAME,\
CyngularAccountId=${CYNGULAR_ACCOUNT_ID:-"851565895544"}"

aws cloudformation create-stack-set \
  --stack-set-name "${CLIENT_NAME}-role" \
  --template-body file://./CFN/ReadonlyRole.yaml \
  --parameters \
    ParameterKey=ClientName,ParameterValue="$CLIENT_NAME" \
    ParameterKey=CyngularAccountId,ParameterValue="${CYNGULAR_ACCOUNT_ID:-"851565895544"}" \
  --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
  --permission-model SERVICE_MANAGED \
  --auto-deployment Enabled=true,RetainStacksOnAccountRemoval=false \
  --managed-execution Active=true \
  --description "cyngular stackset for readonly role" \
  --region $RUNTIME_REGION \
  --profile $RUNTIME_PROFILE

# Create stack instances
aws cloudformation create-stack-instances \
  --stack-set-name "${CLIENT_NAME}-role" \
  --deployment-targets OrganizationalUnitIds="$ORGANIZATIONAL_UNIT_IDS" \
  --regions $RUNTIME_REGION \
  --operation-preferences RegionConcurrencyType=PARALLEL \
  --region $RUNTIME_REGION \
  --profile $RUNTIME_PROFILE


### Services StackSet

ExcludedRegions="\"${ExcludedRegions}\""

# update-stack-set

aws cloudformation create-stack-set \
  --stack-set-name "${CLIENT_NAME}-services" \
  --template-body file://./CFN/Services.yaml \
  --parameters \
    ParameterKey=ClientName,ParameterValue="$CLIENT_NAME" \
    ParameterKey=EnableDNS,ParameterValue="${EnableDNS:-true}" \
    ParameterKey=EnableVPCFlowLogs,ParameterValue="${EnableVPCFlowLogs:-true}" \
    ParameterKey=EnableEKS,ParameterValue="${EnableEKS:-true}" \
    ParameterKey=ServiceManagerOverride,ParameterValue="${ServiceManagerOverride:-1}" \
    ParameterKey=ExcludedRegions,ParameterValue="${ExcludedRegions}" \
    ParameterKey=ClientMgmtAccountId,ParameterValue="${CLIENT_MGMT_ACCOUNT_ID:-""}" \
  --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
  --permission-model SERVICE_MANAGED \
  --auto-deployment Enabled=true,RetainStacksOnAccountRemoval=false \
  --managed-execution Active=true \
  --description "cyngular stackset for services" \
  --region $RUNTIME_REGION \
  --profile $RUNTIME_PROFILE

# Set deployment parallelism and tolerance parameters with defaults if not provided in environment
# These control how CloudFormation deploys across multiple accounts in an organization
FAILURE_TOLERANCE_PERCENTAGE=${FAILURE_TOLERANCE_PERCENTAGE:-25}  # % of accounts that can fail before stopping deployment
MAX_CONCURRENT_PERCENTAGE=${MAX_CONCURRENT_PERCENTAGE:-50}        # % of accounts to deploy to simultaneously

# Create stack instances
# Note on operation preferences:
# - RegionConcurrencyType=PARALLEL: Deploy to all regions simultaneously
# - FailureTolerancePercentage: Controls fault tolerance - higher values allow more failures before stopping
# - MaxConcurrentPercentage: Controls deployment speed - higher values deploy to more accounts at once
#
# Relationship: These two parameters work together to balance speed vs. reliability
# - For critical deployments: Use lower MaxConcurrentPercentage (25-50%) and lower FailureTolerancePercentage (10-25%)
# - For faster deployments: Use higher MaxConcurrentPercentage (75-100%) with moderate FailureTolerancePercentage (25-50%)
# - For maximum reliability: Keep MaxConcurrentPercentage low (25%) and FailureTolerancePercentage high (50%)
aws cloudformation create-stack-instances \
  --stack-set-name "${CLIENT_NAME}-services" \
  --deployment-targets OrganizationalUnitIds="$ORGANIZATIONAL_UNIT_IDS" \
  --regions $RUNTIME_REGION \
  --operation-preferences RegionConcurrencyType=PARALLEL,FailureTolerancePercentage=${FAILURE_TOLERANCE_PERCENTAGE},MaxConcurrentPercentage=${MAX_CONCURRENT_PERCENTAGE} \
  --region $RUNTIME_REGION \
  --profile $RUNTIME_PROFILE