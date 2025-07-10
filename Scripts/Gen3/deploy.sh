#!/usr/bin/env bash
set -eu

# Gen3 Deployment Script for Cyngular Client Onboarding
# This script deploys the Gen3 architecture with managed StackSet

# Configuration
CyngularAccountId="851565895544"
OrganizationId=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RESET='\033[0m'

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${RESET}"
}

print_status $BLUE "=== Cyngular Gen3 Client Onboarding Deployment ==="
print_status $BLUE "Architecture: Managed StackSet with Service Manager"
echo

# Collect user input
read -rp "Enter the Client Name (lowercase, alphanumeric): " ClientName
read -rp "Enter the Stack Name prefix (optional, default: CyngularOnBoarding): " STACK_NAME_PREFIX
STACK_NAME_PREFIX=${STACK_NAME_PREFIX:-"CyngularOnBoarding"}

# Validate client name
if [[ ! $ClientName =~ ^[a-z0-9]+$ ]]; then
    print_status $RED "Error: Client name must be lowercase alphanumeric characters only"
    exit 1
fi

# Ask for organization ID
print_status $YELLOW "Is this an organization deployment? (y/n)"
read -rp "> " IS_ORG

if [[ $IS_ORG == "y" || $IS_ORG == "Y" ]]; then
    read -rp "Enter Organization ID: " OrganizationId
fi

# Ask for CloudTrail configuration
print_status $YELLOW "Do you have an existing CloudTrail bucket? (y/n)"
read -rp "> " HAS_CLOUDTRAIL

CloudTrailBucket=""
if [[ $HAS_CLOUDTRAIL == "y" || $HAS_CLOUDTRAIL == "Y" ]]; then
    read -rp "Enter CloudTrail bucket name: " CloudTrailBucket
fi

# Ask for service configuration
print_status $YELLOW "Service Configuration:"
echo

read -rp "Enable DNS logging? (y/n, default: y): " ENABLE_DNS
ENABLE_DNS=${ENABLE_DNS:-y}
EnableDNS="true"
if [[ $ENABLE_DNS == "n" || $ENABLE_DNS == "N" ]]; then
    EnableDNS="false"
fi

read -rp "Enable EKS logging? (y/n, default: y): " ENABLE_EKS
ENABLE_EKS=${ENABLE_EKS:-y}
EnableEKS="true"
if [[ $ENABLE_EKS == "n" || $ENABLE_EKS == "N" ]]; then
    EnableEKS="false"
fi

read -rp "Enable VPC Flow Logs? (y/n, default: y): " ENABLE_VFL
ENABLE_VFL=${ENABLE_VFL:-y}
EnableVPCFlowLogs="true"
if [[ $ENABLE_VFL == "n" || $ENABLE_VFL == "N" ]]; then
    EnableVPCFlowLogs="false"
fi

# Display configuration summary
print_status $BLUE "=== Deployment Configuration ==="
echo "Client Name: $ClientName"
echo "Stack Name: $STACK_NAME_PREFIX-$ClientName"
echo "Organization ID: ${OrganizationId:-Not set}"
echo "CloudTrail Bucket: ${CloudTrailBucket:-Will be created}"
echo "DNS Logging: $EnableDNS"
echo "EKS Logging: $EnableEKS"
echo "VPC Flow Logs: $EnableVPCFlowLogs"
echo "Cyngular Account: $CyngularAccountId"
echo

# Confirm deployment
print_status $YELLOW "Do you want to proceed with the deployment? (y/n)"
read -rp "> " CONFIRM

if [[ $CONFIRM != "y" && $CONFIRM != "Y" ]]; then
    print_status $RED "Deployment cancelled."
    exit 0
fi

# Check if rain is installed
if ! command -v rain &> /dev/null; then
    print_status $RED "Error: rain CLI is not installed. Please install it first:"
    print_status $YELLOW "  brew install rain"
    exit 1
fi

# Check if aws CLI is installed and configured
if ! command -v aws &> /dev/null; then
    print_status $RED "Error: AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    print_status $RED "Error: AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

# Check current region
CURRENT_REGION=$(aws configure get region 2>/dev/null || echo "us-east-1")
print_status $BLUE "Deploying to region: $CURRENT_REGION"

# Deploy the stack
print_status $GREEN "Starting deployment..."
echo

# Build parameters
PARAMS="ClientName=$ClientName"
PARAMS="$PARAMS,CyngularAccountId=$CyngularAccountId"
PARAMS="$PARAMS,EnableDNS=$EnableDNS"
PARAMS="$PARAMS,EnableEKS=$EnableEKS"
PARAMS="$PARAMS,EnableVPCFlowLogs=$EnableVPCFlowLogs"

if [[ -n $OrganizationId ]]; then
    PARAMS="$PARAMS,OrganizationId=$OrganizationId"
fi

if [[ -n $CloudTrailBucket ]]; then
    PARAMS="$PARAMS,CloudTrailBucket=$CloudTrailBucket"
fi

# Deploy using rain with Master stack
print_status $YELLOW "Deploying CloudFormation master stack..."
if rain deploy CFN/Gen3/Master.yaml "$STACK_NAME_PREFIX-$ClientName" -y --debug \
    --params "$PARAMS"; then
    print_status $GREEN "✓ Master stack deployed successfully!"
else
    print_status $RED "✗ Master stack deployment failed!"
    exit 1
fi

# Get stack outputs
print_status $BLUE "Retrieving stack outputs..."
STACK_OUTPUTS=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME_PREFIX-$ClientName" \
    --query 'Stacks[0].Outputs' \
    --output table 2>/dev/null || echo "No outputs available")

echo
print_status $GREEN "=== Deployment Complete ==="
echo "Stack Name: $STACK_NAME_PREFIX-$ClientName"
echo "Region: $CURRENT_REGION"
echo
print_status $BLUE "Stack Outputs:"
echo "$STACK_OUTPUTS"
echo

# Show monitoring commands
print_status $BLUE "=== Monitoring Commands ==="
echo "View master stack events:"
echo "  rain log $STACK_NAME_PREFIX-$ClientName --chart"
echo
echo "Check master stack status:"
echo "  aws cloudformation describe-stacks --stack-name $STACK_NAME_PREFIX-$ClientName"
echo
echo "Check nested stacks:"
echo "  aws cloudformation list-stack-resources --stack-name $STACK_NAME_PREFIX-$ClientName"
echo
echo "Monitor Service Manager Lambda:"
echo "  aws logs tail /aws/lambda/cyngular-service-manager-$ClientName --follow"
echo
echo "Monitor Region Processor Lambda:"
echo "  aws logs tail /aws/lambda/cyngular-region-processor-$ClientName --follow"
echo

print_status $GREEN "=== Next Steps ==="
echo "1. The Service Manager will automatically start processing services across regions"
echo "2. Monitor the Lambda logs to ensure all services are configured correctly"
echo "3. Check the StackSet instances to verify member account deployment"
echo "4. Contact Cyngular support if you encounter any issues"
echo

print_status $GREEN "Deployment completed successfully! 🎉"