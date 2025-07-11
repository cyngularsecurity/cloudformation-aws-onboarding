# Gen3 AWS Client Onboarding Deployment Guide

This guide explains how to deploy the Cyngular AWS security monitoring infrastructure using the Gen3 architecture with Rain CLI.

## Overview

The Gen3 deployment process consists of three main steps:
1. **Setup**: Download templates and prepare environment
2. **Deploy ReadOnly Role**: Create IAM role for Cyngular access
3. **Deploy Core Infrastructure**: Deploy storage and core monitoring components
4. **Deploy Services**: Deploy Lambda functions and service management

## Prerequisites

### Required Tools
- Rain CLI: `brew install rain`
- AWS CLI configured with appropriate credentials
- Bash shell environment

### Required Environment Variables
Create a `.env` file in the `Scripts/Gen3/` directory with the following variables:

```bash
# Required Parameters
ClientName=your-client-name          # Company name (lowercase, alphanumeric)
CyngularAccountId=123456789012       # Cyngular's AWS account ID
OrganizationId=o-1234567890          # AWS Organizations ID (optional)

# Service Configuration (true/false)
EnableDNS=true                       # Enable DNS logging
EnableEKS=true                       # Enable EKS monitoring
EnableVPCFlowLogs=true              # Enable VPC Flow Logs

# Optional Parameters
CloudTrailBucket=existing-bucket     # Existing CloudTrail bucket (optional)
ServiceManagerOverride=false        # Override service manager behavior (optional)
```

### AWS Profile Setup
Ensure you have an AWS profile named `client_mgmt` configured:
```bash
aws configure --profile client_mgmt
```

## Deployment Steps

### Step 1: Environment Setup
1. Navigate to the deployment directory:
   ```bash
   cd Scripts/Gen3/
   ```

2. Ensure your `.env` file is properly configured with all required variables

3. The script will automatically download the latest CloudFormation templates:
   ```bash
   curl -s https://raw.githubusercontent.com/Cyngular/Devops/main/Scripts/Gen3/zip.sh | bash
   ```

### Step 2: Deploy ReadOnly Role
The first deployment creates the IAM role that allows Cyngular to access the client account:

```bash
rain deploy ./CFN/Gen3/ReadonlyRole.yaml clipper-ro-role \
    --region ap-northeast-3 \
    --profile client_mgmt \
    --params "ClientName=$ClientName,CyngularAccountId=$CyngularAccountId"
```

**What this deploys:**
- Cross-account IAM role for Cyngular access
- Required permissions for security monitoring

### Step 3: Deploy Core Infrastructure
The core deployment sets up the foundational monitoring infrastructure:

```bash
rain deploy ./CFN/Gen3/Core.yaml clipper-core \
    --region ap-northeast-3 \
    --profile client_mgmt \
    --params "ClientName=$ClientName,CyngularAccountId=$CyngularAccountId,OrganizationId=$OrganizationId,CloudTrailBucket=$CloudTrailBucket,EnableDNS=$EnableDNS,EnableEKS=$EnableEKS,EnableVPCFlowLogs=$EnableVPCFlowLogs"
```

**What this deploys:**
- S3 storage infrastructure
- CloudTrail configuration
- StackSet administration roles
- Core monitoring resources

### Step 4: Deploy Services
The services deployment creates the Lambda functions that manage the monitoring services:

```bash
rain deploy ./CFN/Gen3/Services.yaml clipper-services \
    --region ap-northeast-3 \
    --profile client_mgmt \
    --params "ClientName=$ClientName,ServiceManagerOverride=$ServiceManagerOverride,EnableDNS=$EnableDNS,EnableEKS=$EnableEKS,EnableVPCFlowLogs=$EnableVPCFlowLogs"
```

**What this deploys:**
- Service Manager Lambda (orchestrates services across regions)
- Region Processor Lambda (processes individual services per region)
- StackSet resources for member account deployments
- Service configuration management

## Running the Complete Deployment

To run the entire deployment process:

```bash
# Make the script executable
chmod +x RainDeploy.sh

# Run the deployment
./RainDeploy.sh
```

## Monitoring Deployment Progress

### View Stack Status
```bash
# Check individual stack status
rain log clipper-ro-role --chart
rain log clipper-core --chart
rain log clipper-services --chart
```

### Monitor Lambda Functions
```bash
# View Service Manager logs
aws logs tail /aws/lambda/cyngular-service-manager-${ClientName} --follow

# View Region Processor logs
aws logs tail /aws/lambda/cyngular-region-processor-${ClientName} --follow
```

### Check StackSet Operations
```bash
# List StackSet operations
aws cloudformation list-stack-set-operations --stack-set-name cyngular-members-${ClientName}

# Get operation details
aws cloudformation describe-stack-set-operation \
    --stack-set-name cyngular-members-${ClientName} \
    --operation-id <operation-id>
```

## Configuration Parameters Explained

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `ClientName` | Company identifier for resource naming | Yes | - |
| `CyngularAccountId` | Cyngular's AWS account for cross-account access | Yes | - |
| `OrganizationId` | AWS Organizations ID for org-wide deployment | No | - |
| `CloudTrailBucket` | Existing CloudTrail bucket to use | No | Creates new |
| `EnableDNS` | Enable DNS query logging | No | false |
| `EnableEKS` | Enable EKS cluster monitoring | No | false |
| `EnableVPCFlowLogs` | Enable VPC Flow Logs collection | No | false |
| `ServiceManagerOverride` | Override default service behavior | No | false |

## Troubleshooting

### Common Issues

1. **Permission Errors**
   - Ensure the `client_mgmt` profile has sufficient permissions
   - Verify organization-level permissions for StackSet operations

2. **Template Download Failures**
   - Check internet connectivity
   - Verify access to GitHub repository

3. **Region-Specific Failures**
   - Some regions may not support all services
   - Check service availability in target regions

4. **Stack Creation Timeouts**
   - Large organizations may take longer to deploy
   - Monitor CloudFormation events for detailed progress

### Validation Commands
```bash
# Validate CloudFormation templates
rain fmt CFN/Gen3/ReadonlyRole.yaml
rain fmt CFN/Gen3/Core.yaml
rain fmt CFN/Gen3/Services.yaml

# Lint templates
cfn-lint CFN/Gen3/*.yaml
```

## Security Considerations

- All deployments use least-privilege IAM permissions
- Cross-account access is strictly controlled via IAM roles
- CloudTrail and monitoring data is encrypted at rest
- VPC Flow Logs are collected securely without exposing sensitive data

## Next Steps

After successful deployment:
1. Verify monitoring services are operational
2. Configure any service-specific settings
3. Test cross-account access from Cyngular account
4. Document any custom configurations for the client

For offboarding instructions, see the offboarding guide or run `./offboarding.sh`.