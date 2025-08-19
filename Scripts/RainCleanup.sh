#!/usr/bin/env bash
set -eu

# Deploy Cleanup Lambda Functions Template
# This script deploys the cleanup Lambda functions needed for offboarding

if [[ ! -d "Scripts" ]] || [[ ! -d "CFN" ]] || [[ ! -f ".env" ]]; then
  echo "Error: This script must be run from the root of the project where Scripts and CFN directories exist"
  echo "Current directory: $(pwd)"
  exit 1
fi

source .env

CLEANUP_PARAMS="ClientName=$CLIENT_NAME"

echo "Deploying Cleanup Lambda Functions with the parameters:"
echo "  CLEANUP_PARAMS: $CLEANUP_PARAMS"
echo "  Region: $RUNTIME_REGION"
echo "  Profile: $RUNTIME_PROFILE"
echo ""

# Deploy Cleanup stack
echo "Deploying Cleanup stack..."
rain deploy ./CFN/Cleanup.yaml "${CLIENT_NAME}-cleanup" \
    --region $RUNTIME_REGION \
    --profile $RUNTIME_PROFILE \
    --params "$CLEANUP_PARAMS" \
    --ignore-unknown-params \
    --yes --keep

echo ""
echo "Cleanup Lambda functions deployed successfully!"
echo "Functions created:"
echo "  - cyngular-remove-dns-${CLIENT_NAME}"
echo "  - cyngular-remove-vfl-${CLIENT_NAME}"
echo ""
echo "These functions can now be invoked manually across client accounts for offboarding."