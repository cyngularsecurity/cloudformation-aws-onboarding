#!/usr/bin/env bash
# Cyngular AWS client onboarding.
# Deploys 3 single-account stacks in the client MANAGEMENT account, in order
# (ReadonlyRole -> Core -> Services; Core/Services import ReadonlyRole exports),
# then 2 org-wide SERVICE_MANAGED StackSets (role, then services) across the OU(s).
#
# Uses the native AWS CLI. NOTE: `rain` is intentionally NOT used here — it cannot
# parse these templates (Go-YAML error), whereas the CloudFormation API deploys
# them fine. Run from the repo root with a populated .env (see .env.example).
set -euo pipefail

if [[ ! -d "Scripts" ]] || [[ ! -d "CFN" ]] || [[ ! -f ".env" ]]; then
  echo "Error: run from the repo root (Scripts/ and CFN/ dirs + .env must exist)"
  echo "Current directory: $(pwd)"
  exit 1
fi

source .env

REGION="$RUNTIME_REGION"
PROFILE="$RUNTIME_PROFILE"
CYN_ACCT="${CYNGULAR_ACCOUNT_ID:-851565895544}"
AWS=(aws --region "$REGION" --profile "$PROFILE")

echo "Onboarding client '$CLIENT_NAME'"
echo "  Region:  $REGION | Profile: $PROFILE"
echo "  Cyngular account:    $CYN_ACCT"
echo "  Client mgmt account: ${CLIENT_MGMT_ACCOUNT_ID:-<none>}"
echo "  Organization:        ${ORGANIZATION_ID:-<single-account>}"
echo ""

# ---------------------------------------------------------------------------
# Single-account stacks (management account): ReadonlyRole -> Core -> Services
# Use direct create/update-stack (NOT `aws cloudformation deploy`): deploy is
# change-set-based and the AWS::EarlyValidation::ResourceExistenceCheck hook
# falsely rejects Core's Fn::ImportValue of the ReadonlyRole export. Direct
# create/update-stack does not run that hook.
# ---------------------------------------------------------------------------
deploy_stack() {  # $1=stack-name $2=template ; then ParameterKey=..,ParameterValue=.. pairs
  local name="$1" tmpl="$2"; shift 2
  local status
  status=$("${AWS[@]}" cloudformation describe-stacks --stack-name "$name" \
    --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "NONE")
  if [[ "$status" == "NONE" || "$status" == "REVIEW_IN_PROGRESS" || "$status" == *ROLLBACK_COMPLETE || "$status" == *_FAILED ]]; then
    if [[ "$status" != "NONE" ]]; then
      echo "  existing $name in $status — deleting first"
      "${AWS[@]}" cloudformation delete-stack --stack-name "$name" --deletion-mode FORCE_DELETE_STACK 2>/dev/null \
        || "${AWS[@]}" cloudformation delete-stack --stack-name "$name"
      "${AWS[@]}" cloudformation wait stack-delete-complete --stack-name "$name" 2>/dev/null || true
    fi
    echo "  creating $name"
    "${AWS[@]}" cloudformation create-stack --stack-name "$name" --template-body "file://$tmpl" \
      --capabilities CAPABILITY_NAMED_IAM --parameters "$@" >/dev/null
    "${AWS[@]}" cloudformation wait stack-create-complete --stack-name "$name"
  else
    echo "  updating $name (was $status)"
    if "${AWS[@]}" cloudformation update-stack --stack-name "$name" --template-body "file://$tmpl" \
         --capabilities CAPABILITY_NAMED_IAM --parameters "$@" 2>/tmp/cyn_upd_err >/dev/null; then
      "${AWS[@]}" cloudformation wait stack-update-complete --stack-name "$name"
    elif grep -q "No updates are to be performed" /tmp/cyn_upd_err; then
      echo "  no updates"
    else
      cat /tmp/cyn_upd_err; return 1
    fi
  fi
  echo "  $name OK"
}

echo "==> ReadonlyRole stack (${CLIENT_NAME}-ro-role)"
deploy_stack "${CLIENT_NAME}-ro-role" "./CFN/ReadonlyRole.yaml" \
  ParameterKey=ClientName,ParameterValue="$CLIENT_NAME" \
  ParameterKey=CyngularAccountId,ParameterValue="$CYN_ACCT"

echo "==> Core stack (${CLIENT_NAME}-core)"
deploy_stack "${CLIENT_NAME}-core" "./CFN/Core.yaml" \
  ParameterKey=ClientName,ParameterValue="$CLIENT_NAME" \
  ParameterKey=CyngularAccountId,ParameterValue="$CYN_ACCT" \
  ParameterKey=OrganizationId,ParameterValue="${ORGANIZATION_ID:-}" \
  ParameterKey=EnableCloudTrail,ParameterValue="${EnableCloudTrail:-true}" \
  ParameterKey=EnableBucketPolicyManager,ParameterValue="${EnableBucketPolicyManager:-true}"

echo "==> Services stack (${CLIENT_NAME}-services)"
deploy_stack "${CLIENT_NAME}-services" "./CFN/Services.yaml" \
  ParameterKey=ClientName,ParameterValue="$CLIENT_NAME" \
  ParameterKey=ClientAccountId,ParameterValue="${CLIENT_MGMT_ACCOUNT_ID:-}" \
  ParameterKey=EnableDNS,ParameterValue="${EnableDNS:-true}" \
  ParameterKey=EnableEKS,ParameterValue="${EnableEKS:-true}" \
  ParameterKey=EnableVPCFlowLogs,ParameterValue="${EnableVPCFlowLogs:-true}" \
  ParameterKey=ServiceManagerOverride,ParameterValue="${ServiceManagerOverride:-1}"

if [[ -z "${ORGANIZATIONAL_UNIT_IDS:-}" ]]; then
  echo "No ORGANIZATIONAL_UNIT_IDS set — single-account deployment complete."
  exit 0
fi

# ---------------------------------------------------------------------------
# Org-wide StackSets (SERVICE_MANAGED). The role StackSet MUST complete before
# the services StackSet: services member stacks import
# CyngularSecurity:ReadonlyRoleArn:<client>, created per-account by the role set.
# ---------------------------------------------------------------------------
FAILURE_TOLERANCE_PERCENTAGE=${FAILURE_TOLERANCE_PERCENTAGE:-25}
MAX_CONCURRENT_PERCENTAGE=${MAX_CONCURRENT_PERCENTAGE:-50}
OP_PREFS="RegionConcurrencyType=PARALLEL,FailureTolerancePercentage=${FAILURE_TOLERANCE_PERCENTAGE},MaxConcurrentPercentage=${MAX_CONCURRENT_PERCENTAGE}"

wait_stackset_op() {  # $1=stackset name  $2=operation id
  local ss="$1" op="$2" st
  while :; do
    st=$("${AWS[@]}" cloudformation describe-stack-set-operation \
      --stack-set-name "$ss" --operation-id "$op" \
      --query 'StackSetOperation.Status' --output text 2>/dev/null || echo UNKNOWN)
    echo "    [$ss] op $op: $st"
    case "$st" in
      SUCCEEDED) return 0 ;;
      RUNNING|QUEUED|STOPPING) sleep 10 ;;
      *) echo "    ERROR: StackSet op $op ended in state $st"; return 1 ;;
    esac
  done
}

upsert_stackset() {  # $1=name  $2=template  (then ParameterKey=...,ParameterValue=... pairs)
  local name="$1" tmpl="$2"; shift 2
  local common=(--template-body "file://$tmpl" --parameters "$@"
    --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND
    --permission-model SERVICE_MANAGED
    --auto-deployment Enabled=true,RetainStacksOnAccountRemoval=false
    --managed-execution Active=true)
  if "${AWS[@]}" cloudformation describe-stack-set --stack-set-name "$name" >/dev/null 2>&1; then
    echo "==> Updating StackSet $name"
    "${AWS[@]}" cloudformation update-stack-set --stack-set-name "$name" "${common[@]}" >/dev/null
  else
    echo "==> Creating StackSet $name"
    "${AWS[@]}" cloudformation create-stack-set --stack-set-name "$name" "${common[@]}" \
      --description "cyngular $name" >/dev/null
  fi
}

# --- ReadonlyRole StackSet (deploy + WAIT before services) ---
upsert_stackset "${CLIENT_NAME}-role" "./CFN/ReadonlyRole.yaml" \
  ParameterKey=ClientName,ParameterValue="$CLIENT_NAME" \
  ParameterKey=CyngularAccountId,ParameterValue="$CYN_ACCT"

echo "==> Creating role stack instances (OU=$ORGANIZATIONAL_UNIT_IDS)"
ROLE_OP=$("${AWS[@]}" cloudformation create-stack-instances \
  --stack-set-name "${CLIENT_NAME}-role" \
  --deployment-targets OrganizationalUnitIds="$ORGANIZATIONAL_UNIT_IDS" \
  --regions "$REGION" --operation-preferences "$OP_PREFS" \
  --query OperationId --output text)
wait_stackset_op "${CLIENT_NAME}-role" "$ROLE_OP"

# --- Services StackSet (only after role exports exist in member accounts) ---
upsert_stackset "${CLIENT_NAME}-services" "./CFN/Services.yaml" \
  ParameterKey=ClientName,ParameterValue="$CLIENT_NAME" \
  ParameterKey=ClientAccountId,ParameterValue="${CLIENT_MGMT_ACCOUNT_ID:-}" \
  ParameterKey=EnableDNS,ParameterValue="${EnableDNS:-true}" \
  ParameterKey=EnableVPCFlowLogs,ParameterValue="${EnableVPCFlowLogs:-true}" \
  ParameterKey=EnableEKS,ParameterValue="${EnableEKS:-true}" \
  ParameterKey=ServiceManagerOverride,ParameterValue="${ServiceManagerOverride:-1}" \
  ParameterKey=ExcludedRegions,ParameterValue="${ExcludedRegions:-}"

echo "==> Creating services stack instances (OU=$ORGANIZATIONAL_UNIT_IDS)"
SVC_OP=$("${AWS[@]}" cloudformation create-stack-instances \
  --stack-set-name "${CLIENT_NAME}-services" \
  --deployment-targets OrganizationalUnitIds="$ORGANIZATIONAL_UNIT_IDS" \
  --regions "$REGION" --operation-preferences "$OP_PREFS" \
  --query OperationId --output text)
wait_stackset_op "${CLIENT_NAME}-services" "$SVC_OP"

echo ""
echo "Onboarding complete for '$CLIENT_NAME'."
