#!/usr/bin/env bash
set -eu

# Gen3 Offboarding Script for Cyngular Client
# This script removes the Gen3 architecture and cleans up resources

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

print_status $BLUE "=== Cyngular Gen3 Client Offboarding ==="
print_status $YELLOW "WARNING: This will remove all Cyngular monitoring infrastructure!"
echo

# Collect user input
read -rp "Enter the Client Name (must match deployment): " ClientName
read -rp "Enter the Stack Name prefix (default: cyngular-onboarding): " STACK_NAME_PREFIX
read -rp "Enter the AWS Region (default: none): " AWS_REGION
STACK_NAME_PREFIX=${STACK_NAME_PREFIX:-cyngular-onboarding}

STACK_NAME="$STACK_NAME_PREFIX-$ClientName"
export AWS_REGION=${AWS_REGION:-none}

# Validate client name
if [[ ! "$ClientName" =~ ^[a-z0-9]+$ ]]; then
    print_status $RED "Error: Client name must be lowercase alphanumeric characters only"
    exit 1
fi

# Check if stack exists
if ! aws cloudformation describe-stacks --stack-name "$STACK_NAME" &> /dev/null; then
    print_status $RED "Error: Stack $STACK_NAME not found"
    exit 1
fi

# Display what will be removed
print_status $BLUE "=== Resources to be removed ==="
echo "- Main CloudFormation stack: $STACK_NAME"
echo "- StackSet: cyngular-member-accounts-$ClientName"
echo "- Lambda functions: Service Manager and Region Processor"
echo "- IAM roles and policies"
echo "- S3 bucket: cyngular-$ClientName-bucket-* (if empty)"
echo "- CloudTrail: cyngular-cloudtrail (if created by Cyngular)"
echo "- Admin and Execution roles stacks"
echo

print_status $YELLOW "Are you sure you want to proceed? Type 'DELETE' to confirm:"
read -rp "> " CONFIRM

if [[ $CONFIRM != "DELETE" ]]; then
    print_status $RED "Offboarding cancelled."
    exit 0
fi

# Check if rain is installed
if ! command -v rain &> /dev/null; then
    print_status $RED "Error: rain CLI is not installed. Please install it first:"
    print_status $YELLOW "  brew install rain"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    print_status $RED "Error: AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

print_status $GREEN "Starting offboarding process..."
echo

# Step 1: Stop scheduled events
print_status $BLUE "Step 1: Disabling scheduled events..."
SERVICE_MANAGER_RULE="cyngular-service-manager-$ClientName-rule"
if aws events describe-rule --name "$SERVICE_MANAGER_RULE" &> /dev/null; then
    aws events disable-rule --name "$SERVICE_MANAGER_RULE" || true
    print_status $GREEN "✓ Disabled scheduled rule: $SERVICE_MANAGER_RULE"
else
    print_status $YELLOW "! Scheduled rule not found: $SERVICE_MANAGER_RULE"
fi

# Step 2: Remove StackSet instances
print_status $BLUE "Step 2: Removing StackSet instances..."
STACKSET_NAME="cyngular-member-accounts-$ClientName"
if aws cloudformation describe-stack-set --stack-set-name "$STACKSET_NAME" &> /dev/null; then
    # List stack instances
    STACK_INSTANCES=$(aws cloudformation list-stack-instances \
        --stack-set-name "$STACKSET_NAME" \
        --query 'Summaries[].{Account:Account,Region:Region}' \
        --output json 2>/dev/null || echo "[]")
    
    if [[ "$STACK_INSTANCES" != "[]" ]]; then
        print_status $YELLOW "Found StackSet instances. Removing..."
        
        # Remove all instances
        aws cloudformation delete-stack-instances \
            --stack-set-name "$STACKSET_NAME" \
            --retain-stacks false \
            --regions $(echo "$STACK_INSTANCES" | jq -r '.[].Region' | sort -u | tr '\n' ' ') \
            --accounts $(echo "$STACK_INSTANCES" | jq -r '.[].Account' | sort -u | tr '\n' ' ') \
            --no-cli-pager || true
        
        print_status $YELLOW "Waiting for StackSet instances to be removed..."
        sleep 30
    fi
    
    print_status $GREEN "✓ StackSet instances removal initiated"
else
    print_status $YELLOW "! StackSet not found: $STACKSET_NAME"
fi

# Step 3: Delete the main stack
print_status $BLUE "Step 3: Deleting main CloudFormation stack..."
if rain rm "$STACK_NAME" -y; then
    print_status $GREEN "✓ Main stack deletion initiated: $STACK_NAME"
else
    print_status $RED "✗ Failed to delete main stack: $STACK_NAME"
    print_status $YELLOW "You may need to manually delete the stack from the AWS console"
fi

# Step 4: Clean up admin and execution role stacks
print_status $BLUE "Step 4: Cleaning up admin and execution role stacks..."

ADMIN_STACK="CyngularCloudFormationStackSetAdministrationRole"
if aws cloudformation describe-stacks --stack-name "$ADMIN_STACK" &> /dev/null; then
    print_status $YELLOW "Deleting admin role stack..."
    aws cloudformation delete-stack --stack-name "$ADMIN_STACK" || true
    print_status $GREEN "✓ Admin role stack deletion initiated"
else
    print_status $YELLOW "! Admin role stack not found"
fi

EXEC_STACK="CyngularCloudFormationStackSetExecutionRole"
if aws cloudformation describe-stacks --stack-name "$EXEC_STACK" &> /dev/null; then
    print_status $YELLOW "Deleting execution role stack..."
    aws cloudformation delete-stack --stack-name "$EXEC_STACK" || true
    print_status $GREEN "✓ Execution role stack deletion initiated"
else
    print_status $YELLOW "! Execution role stack not found"
fi

# Step 5: Manual cleanup instructions
print_status $BLUE "Step 5: Manual cleanup instructions"
echo
print_status $YELLOW "The following resources may need manual cleanup:"
echo
echo "1. S3 Bucket: cyngular-$ClientName-bucket-*"
echo "   - Empty the bucket contents first, then delete the bucket"
echo "   - Command: aws s3 rm s3://cyngular-$ClientName-bucket-* --recursive"
echo
echo "2. VPC Flow Logs in member accounts:"
echo "   - Check each member account for VPC Flow Logs with tag 'Cyngular-vpc-flowlogs'"
echo "   - Delete them manually if needed"
echo
echo "3. Route 53 Resolver Query Log Configs:"
echo "   - Check each region for 'cyngular_dns' query log configs"
echo "   - Delete them manually if needed"
echo
echo "4. EKS Access Entries:"
echo "   - Check EKS clusters for Cyngular role access entries"
echo "   - Remove them manually if needed"
echo
echo "5. EC2 Instance Audit Configurations:"
echo "   - Auditd configurations on EC2 instances will remain"
echo "   - Remove /etc/audit/rules.d/audit.rules if needed"
echo

# Step 6: Verification
print_status $BLUE "Step 6: Verification commands"
echo
print_status $YELLOW "Use these commands to verify cleanup:"
echo
echo "Check stack deletion status:"
echo "  aws cloudformation describe-stacks --stack-name $STACK_NAME"
echo
echo "Check StackSet status:"
echo "  aws cloudformation describe-stack-set --stack-set-name $STACKSET_NAME"
echo
echo "List remaining Lambda functions:"
echo "  aws lambda list-functions --query 'Functions[?contains(FunctionName, \`cyngular-$ClientName\`)].FunctionName'"
echo
echo "Check S3 buckets:"
echo "  aws s3 ls | grep cyngular-$ClientName"
echo

print_status $GREEN "=== Offboarding Process Complete ==="
print_status $YELLOW "Note: CloudFormation stack deletion may take several minutes to complete."
print_status $YELLOW "Please monitor the AWS console for final deletion status."
print_status $BLUE "Contact Cyngular support if you need assistance with manual cleanup."
echo