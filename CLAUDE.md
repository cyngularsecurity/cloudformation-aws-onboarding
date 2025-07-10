# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Cyngular AWS client onboarding system that automates the deployment of security monitoring infrastructure using AWS CloudFormation StackSets. The system enables Cyngular to monitor client AWS accounts for security analysis by deploying standardized CloudFormation templates across multiple regions and accounts.

## Architecture

The project supports multiple generations of deployment architecture:

### Gen2 Architecture (Legacy)
- **CFN/Gen2/**: CloudFormation templates with Lambda-managed StackSets
- **Lambdas/**: Individual Lambda functions for each service
- Region list manually provided by client

### Gen3 Architecture (Current)
- **CFN/Gen3/**: CloudFormation templates with managed StackSets
- **Lambdas/Gen3/**: Consolidated Lambda architecture
- Auto-discovery of all enabled regions

## Gen3 Architecture Components

### 1. CloudFormation Templates (`CFN/Gen3/`)
- **Master.yaml**: Master stack that orchestrates all nested stacks
- **Storage.yaml**: S3 bucket, bucket policy, and CloudTrail resources
- **ReadonlyRole.yaml**: IAM role for Cyngular access with required permissions
- **Lambda.yaml**: Lambda functions, roles, and managed StackSet resources
- **MembersGlobal.yaml**: Global resources deployed to member accounts via StackSet

### 2. Lambda Functions (`Lambdas/Gen3/`)
- **ServiceManager/**: Orchestrator lambda that manages service configuration across regions
- **RegionProcessor/**: Worker lambda that processes individual services per region
- **AdminAndExec/**: Creates StackSet administration and execution roles
- Consolidated architecture with two-lambda design


### 2. Lambda Functions (`Lambdas/`)
- **StackSetManager/**: Manages CloudFormation StackSet operations and deployments
- **ConfigEKS/**: Configures EKS cluster access for monitoring
- **ConfigDNS/**: Sets up DNS logging configuration
- **ConfigOS/**: Configures OpenSearch for log analysis
- **ConfigVFL/**: Manages VPC Flow Logs configuration
- **UpdateBucketPolicy/**: Updates S3 bucket policies for log collection
- **TagBuckets.py**: Tags S3 buckets with monitoring identifiers

### 3. Deployment/OffBoarding Scripts (`Scripts/`)
- **deploy.sh**: Automated deployment script using Rain CLI
- **OffBoarding.sh**: Automated offboarding script
- **OffBoardingRain.sh**: Automated offboarding script using Rain CLI


### 3. Deployment Scripts (`Scripts/Gen3/`)
- **deploy.sh**: Automated deployment script for Gen3 architecture
- **offboarding.sh**: Automated offboarding script for Gen3 cleanup

## Common Commands

### Gen3 Deployment (Recommended)
```bash
# Automated deployment using Gen3 script
./Scripts/Gen3/deploy.sh

# Manual deployment with Rain (Master stack)
rain deploy CFN/Gen3/Master.yaml <stack-name> -y --debug \
  --params "ClientName=<name>,CyngularAccountId=<id>,OrganizationId=<org-id>,EnableDNS=true,EnableEKS=true,EnableVPCFlowLogs=true"

# Offboarding
./Scripts/Gen3/offboarding.sh
```

### Gen2 Deployment (Legacy)
```bash
# Manual deployment with Rain
rain deploy CFN/Gen2/Main.yaml <stack-name> -y --debug \
  --params "ClientName=<name>,ClientRegions=<regions>,CyngularAccountId=<id>,OrganizationId=<org-id>"
```

### Template Validation
```bash
# Validate CloudFormation templates
rain fmt CFN/Gen3/Main.yaml
aws cloudformation validate-template --template-body file://CFN/Gen3/Main.yaml

# Lint templates
cfn-lint CFN/Gen3/*.yaml
```

### Monitoring and Debugging
```bash
# View deployment logs with Rain
rain log <stack-name> --chart

# Check CloudFormation stack status
aws cloudformation describe-stacks --stack-name <stack-name>

# Monitor StackSet operations
aws cloudformation describe-stack-set-operation --stack-set-name <stackset-name> --operation-id <operation-id>

# Gen3 specific monitoring
aws logs tail /aws/lambda/cyngular-service-manager-<client-name> --follow
aws logs tail /aws/lambda/cyngular-region-processor-<client-name> --follow
```

## Key Configuration Parameters

### Gen3 Parameters
- **ClientName**: Company name for resource naming (lowercase, alphanumeric)
- **CyngularAccountId**: Cyngular's AWS account ID for cross-account access
- **OrganizationId**: AWS Organizations ID (optional, for organization-wide deployments)
- **EnableVPCFlowLogs/EnableDNS/EnableEKS**: Boolean flags for service enablement
- **CloudTrailBucket**: Existing CloudTrail bucket name (optional)

### Gen2 Parameters (Legacy)
- **ClientRegions**: Comma-separated list of regions (e.g., "eu-west-1,eu-west-2")
- All Gen3 parameters above

## Prerequisites

Before deployment, ensure:
1. AWS Organizations services are enabled (if using organization deployment):
   - CloudFormation StackSets
   - CloudTrail
2. Appropriate IAM permissions for StackSet administration
3. Rain CLI tool installed (`brew install rain`)
4. AWS CLI configured with appropriate credentials

## Gen3 Architecture Benefits

- **Simplified Deployment**: Managed StackSet eliminates custom Lambda complexity
- **Auto-Region Discovery**: No need to manually specify regions
- **Consolidated Lambdas**: Two-lambda design reduces operational overhead
- **Better Error Handling**: Improved monitoring and debugging capabilities
- **Scalable**: Service Manager orchestrates across all enabled regions automatically

## Development Notes

- All CloudFormation templates follow AWS best practices with proper parameter validation
- Lambda functions include comprehensive error handling and logging
- The system supports both single-account and organization-wide deployments
- Gen3 architecture uses managed StackSet resources for simplified operations
- Service Manager automatically discovers and processes all enabled regions