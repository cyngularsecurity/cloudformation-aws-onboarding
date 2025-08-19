#!/bin/bash

# GitHub Actions AWS OIDC Setup Script
# This script automates the creation of AWS OIDC provider and IAM role for GitHub Actions

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
GITHUB_ORG=""
REPO_NAME=""
AWS_ACCOUNT_ID=""
ROLE_NAME="GitHubActionsDevOpsRole"
POLICY_NAME="GitHubActionsDevOpsPolicy"

print_usage() {
    echo "Usage: $0 --org <github-org> --repo <repo-name> --account <aws-account-id>"
    echo ""
    echo "Options:"
    echo "  --org      GitHub organization name"
    echo "  --repo     Repository name"
    echo "  --account  AWS Account ID"
    echo "  --help     Display this help message"
    echo ""
    echo "Example:"
    echo "  $0 --org myorg --repo myrepo --account 123456789012"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --org)
            GITHUB_ORG="$2"
            shift 2
            ;;
        --repo)
            REPO_NAME="$2"
            shift 2
            ;;
        --account)
            AWS_ACCOUNT_ID="$2"
            shift 2
            ;;
        --help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$GITHUB_ORG" || -z "$REPO_NAME" || -z "$AWS_ACCOUNT_ID" ]]; then
    echo -e "${RED}Error: Missing required parameters${NC}"
    print_usage
    exit 1
fi

echo -e "${GREEN}Setting up AWS OIDC for GitHub Actions${NC}"
echo "GitHub Org: $GITHUB_ORG"
echo "Repository: $REPO_NAME"
echo "AWS Account: $AWS_ACCOUNT_ID"
echo "Role Name: $ROLE_NAME"
echo ""

# Step 1: Create OIDC Identity Provider
echo -e "${YELLOW}Step 1: Creating OIDC Identity Provider...${NC}"

OIDC_EXISTS=$(aws iam list-open-id-connect-providers --query "OpenIDConnectProviderList[?contains(Arn, 'token.actions.githubusercontent.com')].Arn" --output text)

if [[ -n "$OIDC_EXISTS" ]]; then
    echo "✅ OIDC Provider already exists: $OIDC_EXISTS"
    OIDC_ARN="$OIDC_EXISTS"
else
    OIDC_ARN=$(aws iam create-open-id-connect-provider \
        --url https://token.actions.githubusercontent.com \
        --client-id-list sts.amazonaws.com \
        --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
        --thumbprint-list 1c58a3a8518e8759bf075b76b750d4f2df264fcd \
        --query 'OpenIDConnectProviderArn' --output text)
    
    echo "✅ Created OIDC Provider: $OIDC_ARN"
fi

# Step 2: Create Trust Policy
echo -e "${YELLOW}Step 2: Creating trust policy...${NC}"

TRUST_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:${GITHUB_ORG}/${REPO_NAME}:*"
        }
      }
    }
  ]
}
EOF
)

echo "$TRUST_POLICY" > /tmp/trust-policy.json
echo "✅ Trust policy created"

# Step 3: Create IAM Role
echo -e "${YELLOW}Step 3: Creating IAM Role...${NC}"

ROLE_EXISTS=$(aws iam get-role --role-name "$ROLE_NAME" 2>/dev/null || echo "")

if [[ -n "$ROLE_EXISTS" ]]; then
    echo "⚠️  Role $ROLE_NAME already exists. Updating trust policy..."
    aws iam update-assume-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-document file:///tmp/trust-policy.json
    echo "✅ Updated trust policy for existing role"
else
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file:///tmp/trust-policy.json \
        --description "GitHub Actions role for DevOps pipeline"
    echo "✅ Created IAM Role: $ROLE_NAME"
fi

ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${ROLE_NAME}"

# Step 4: Create Custom Policy
echo -e "${YELLOW}Step 4: Creating custom policy...${NC}"

CUSTOM_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "s3:GetBucketLocation",
        "s3:GetBucketVersioning"
      ],
      "Resource": [
        "arn:aws:s3:::*",
        "arn:aws:s3:::*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:UpdateFunctionCode",
        "lambda:PublishLayerVersion",
        "lambda:GetLayerVersion",
        "lambda:ListLayers",
        "lambda:ListLayerVersions"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:ValidateTemplate",
        "cloudformation:DescribeStacks",
        "cloudformation:ListStacks"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sts:AssumeRole",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
EOF
)

echo "$CUSTOM_POLICY" > /tmp/custom-policy.json

POLICY_EXISTS=$(aws iam get-policy --policy-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${POLICY_NAME}" 2>/dev/null || echo "")

if [[ -n "$POLICY_EXISTS" ]]; then
    echo "⚠️  Policy $POLICY_NAME already exists. Creating new version..."
    aws iam create-policy-version \
        --policy-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${POLICY_NAME}" \
        --policy-document file:///tmp/custom-policy.json \
        --set-as-default
    echo "✅ Updated policy version"
else
    aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document file:///tmp/custom-policy.json \
        --description "Custom policy for GitHub Actions DevOps pipeline"
    echo "✅ Created custom policy: $POLICY_NAME"
fi

POLICY_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${POLICY_NAME}"

# Step 5: Attach Policy to Role
echo -e "${YELLOW}Step 5: Attaching policy to role...${NC}"

aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "$POLICY_ARN"

echo "✅ Policy attached to role"

# Cleanup temporary files
rm -f /tmp/trust-policy.json /tmp/custom-policy.json

echo ""
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Add the following secrets to your GitHub repository:"
echo "   - Name: AWS_DEVOPS_ROLE_ARN"
echo "   - Value: $ROLE_ARN"
echo ""
echo "2. Add the AWS region secret (if different from us-east-1):"
echo "   - Name: AWS_DEFAULT_REGION"
echo "   - Value: your-preferred-region"
echo ""
echo "3. Go to your GitHub repository:"
echo "   Settings > Secrets and variables > Actions > New repository secret"
echo ""
echo -e "${YELLOW}Summary:${NC}"
echo "✅ OIDC Provider: $OIDC_ARN"
echo "✅ IAM Role: $ROLE_ARN" 
echo "✅ IAM Policy: $POLICY_ARN"
echo "✅ Repository: $GITHUB_ORG/$REPO_NAME"
echo ""
echo -e "${GREEN}Your GitHub Actions workflow is now ready to use secure AWS authentication!${NC}"