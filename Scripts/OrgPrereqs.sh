#!/usr/bin/env bash
# Check (and optionally enable) the AWS Organizations prerequisites required for
# Cyngular client onboarding via SERVICE_MANAGED StackSets + an organization CloudTrail.
#
# Must be run from the organization MANAGEMENT account.
#
#   Scripts/OrgPrereqs.sh                 # read-only check (default)
#   Scripts/OrgPrereqs.sh --apply         # enable anything missing
#   Scripts/OrgPrereqs.sh --profile p --region us-east-1 --apply
#
# Profile/region default to .env (RUNTIME_PROFILE / RUNTIME_REGION) if present,
# else the AWS CLI defaults.
set -euo pipefail

APPLY=false
PROFILE=""
REGION=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=true; shift ;;
    --profile) PROFILE="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

# Fall back to .env (script lives in Scripts/, .env at repo root)
ENV_FILE="$(cd "$(dirname "$0")/.." && pwd)/.env"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  set -a; source "$ENV_FILE"; set +a
fi
PROFILE="${PROFILE:-${RUNTIME_PROFILE:-default}}"
REGION="${REGION:-${RUNTIME_REGION:-us-east-1}}"
AWS=(aws --profile "$PROFILE" --region "$REGION")

# StackSets-with-Organizations service principal + the CloudTrail org principal
STACKSETS_SP="member.org.stacksets.cloudformation.amazonaws.com"
CLOUDTRAIL_SP="cloudtrail.amazonaws.com"

pass()  { printf '  \033[32m✓\033[0m %s\n' "$1"; }
warn()  { printf '  \033[33m!\033[0m %s\n' "$1"; }
info()  { printf '  \033[36m·\033[0m %s\n' "$1"; }

echo "== Cyngular onboarding — Org prerequisites =="
echo "   profile=$PROFILE region=$REGION mode=$([[ $APPLY == true ]] && echo APPLY || echo check)"
echo

# ---------------------------------------------------------------------------
# 0. Must be the management account
# ---------------------------------------------------------------------------
CALLER_ACCT="$("${AWS[@]}" sts get-caller-identity --query Account --output text)"
ORG_JSON="$("${AWS[@]}" organizations describe-organization --output json)"
MGMT_ACCT="$(echo "$ORG_JSON" | python3 -c 'import sys,json;print(json.load(sys.stdin)["Organization"]["MasterAccountId"])')"
ORG_ID="$(echo "$ORG_JSON" | python3 -c 'import sys,json;print(json.load(sys.stdin)["Organization"]["Id"])')"
echo "Organization $ORG_ID (management account $MGMT_ACCT)"
if [[ "$CALLER_ACCT" != "$MGMT_ACCT" ]]; then
  warn "Caller account ($CALLER_ACCT) is NOT the management account ($MGMT_ACCT)."
  warn "Run this from the org management account. Aborting."
  exit 1
fi
pass "Running as management account ($CALLER_ACCT)"
echo

FAILED=false

# ---------------------------------------------------------------------------
# 1. CloudFormation StackSets trusted access (SERVICE_MANAGED)
# ---------------------------------------------------------------------------
echo "[1] CloudFormation StackSets <-> Organizations trusted access"
SS_STATUS="$("${AWS[@]}" cloudformation describe-organizations-access --call-as SELF \
  --query Status --output text 2>/dev/null || echo "UNKNOWN")"
if [[ "$SS_STATUS" == "ENABLED" ]]; then
  pass "StackSets organizations access: ENABLED"
else
  warn "StackSets organizations access: $SS_STATUS"
  if [[ "$APPLY" == true ]]; then
    info "Enabling via cloudformation activate-organizations-access ..."
    "${AWS[@]}" cloudformation activate-organizations-access
    pass "Activated StackSets organizations access"
  else
    FAILED=true
  fi
fi
echo

# ---------------------------------------------------------------------------
# 2. Trusted service access list (CloudTrail + StackSets principals)
# ---------------------------------------------------------------------------
echo "[2] Trusted service access (organizations)"
SVC_LIST="$("${AWS[@]}" organizations list-aws-service-access-for-organization \
  --query 'EnabledServicePrincipals[].ServicePrincipal' --output text 2>/dev/null || echo "")"
check_sp() {
  local sp="$1" label="$2" required="$3"
  if grep -qw "$sp" <<<"$SVC_LIST"; then
    pass "$label trusted access enabled ($sp)"
  else
    warn "$label trusted access NOT enabled ($sp)"
    if [[ "$APPLY" == true ]]; then
      info "Enabling $sp ..."
      "${AWS[@]}" organizations enable-aws-service-access --service-principal "$sp"
      pass "Enabled $sp"
    elif [[ "$required" == true ]]; then
      FAILED=true
    fi
  fi
}
# StackSets SP is normally added automatically by activate-organizations-access; report only.
check_sp "$STACKSETS_SP" "StackSets" false
check_sp "$CLOUDTRAIL_SP" "CloudTrail (org trail)" true
echo

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
if [[ "$FAILED" == true ]]; then
  warn "One or more prerequisites are missing. Re-run with --apply to enable them."
  exit 3
fi
pass "All org prerequisites satisfied."
