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
- **ServiceManager/** (CyngularServiceOrchestrator): Production-ready orchestrator lambda with metrics and error handling
- **RegionProcessor/** (CyngularRegionalServiceManager): Production-ready worker lambda with parameter validation
- **UpdateBucketPolicy/** (CyngularBucketPolicyManager): Manages S3 bucket policies for log collection
- **AdminAndExec/**: Creates StackSet administration and execution roles
- Consolidated architecture with production-grade Lambda functionality and monitoring

## Gen3 Services Overview

### Supported Security Services
1. **DNS Logging Service** (`dns`)
   - Configures Route53 Resolver Query Log Configs
   - Associates VPCs with DNS logging
   - Supports custom S3 bucket destinations
   - Tags buckets with `cyngular-dnslogs: true`

2. **VPC Flow Logs Service** (`vfl`) 
   - Enables VPC Flow Logs for all VPCs in region
   - Configures S3 destination for flow logs
   - Supports custom S3 bucket destinations  
   - Tags buckets with `cyngular-vpcflowlogs: true`

3. **EKS Monitoring Service** (`eks`)
   - Configures EKS cluster audit and authenticator logging
   - Creates Cyngular access entries for cluster monitoring
   - Associates AmazonEKSViewPolicy for readonly access
   - Tags default Cyngular bucket with `cyngular-ekslogs: true`

4. **OS Internals Service** (`os`)
   - Deploys security monitoring agents to EC2 instances
   - Configures audit rules and system monitoring
   - Always enabled for comprehensive security coverage

### Service Configuration Logic
- **Enable Parameter = "true"**: Uses default Cyngular S3 bucket
- **Enable Parameter = "false"**: Service disabled (not deployed)
- **Enable Parameter = "bucket-name"**: Uses custom S3 bucket (DNS/VFL only)

### Latest Production-Ready Features
- **Intelligent S3 Bucket Tagging**: Automatically tags appropriate buckets based on service configuration
- **Custom Bucket Support**: DNS and VFL services support custom S3 bucket destinations
- **Asynchronous Service Processing**: Service Orchestrator invokes Regional Service Manager asynchronously
- **Production-Grade Error Handling**: Structured logging with no stack trace exposure in production responses
- **Official Function Naming**: Professional naming convention (CyngularServiceOrchestrator, etc.)
- **Dynamic Parameter Passing**: Services receive enable parameters for intelligent bucket selection
- **CloudWatch Metrics Integration**: Comprehensive metrics collection via dedicated metrics.py modules
- **Environment Variable Validation**: Fail-fast patterns using os.environ['KEY'] without defaults
- **Security Hardening**: Eliminated security vulnerabilities and implemented best practices
- **Lambda Runtime Logging**: Proper logging using `logger = logging.getLogger(__name__)`

### 2. Lambda Functions (`Lambdas/`) - Legacy
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

## Git Workflow and Development Process

The project follows a standard git workflow through the branch flow: `feature → dev → main → release/v3.8`.

### Recommended Development Workflow

#### 1. Testing and Quality Assurance
```bash
# Test project syntax with ruff
ruff check .
ruff format --check .

# Run any existing test suites
# Check README or project structure for specific test commands
```

#### 2. Feature Branch Development
```bash
# Create feature branch from dev
git checkout dev
git fetch origin && git pull origin dev --rebase
git checkout -b feature/DEVOPS-885-description

# Make your changes and commit with proper message format
git add .
git commit -m "DEVOPS-885: Description of changes

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

#### 3. Complete Git Workflow
```bash
# 1. Push feature branch and create PR to dev
git push origin feature/DEVOPS-885-description
# Create PR: feature → dev

# 2. After dev PR is merged, create PR from dev to main
git checkout dev
git fetch origin && git pull origin dev --rebase
# Create PR: dev → main

# 3. After main PR is merged, merge main to release locally
git checkout main
git fetch origin && git pull origin main --rebase
git checkout release/v3.8
git fetch origin && git pull origin release/v3.8 --rebase
git merge main --no-ff -m "DEVOPS-885: Merge main to release/v3.8"

# 4. Resolve any merge conflicts and finalize release
# If conflicts exist, resolve them manually, then:
git add .
git commit -m "DEVOPS-885: Resolve merge conflicts for release"

# 5. Push release branch and create final PR
git push origin release/v3.8
# Create PR: release/v3.8 → main (for final integration)

# 6. Tag the release after everything is merged
git tag -a v3.8.x -m "Release v3.8.x - Description of release"
git push origin v3.8.x
```

### Critical Git Workflow Requirements
- **Always fetch and pull with rebase** before creating branches or PRs
- **Include DEVOPS-885 commit ID** to meet GitLab pre-receive hook requirements
- **Test with ruff** before creating any commits
- **Use proper commit message format** with ticket ID and Claude attribution

## Agentic Orchestration with Gemini CLI

This project uses Gemini CLI for robust task orchestration and parallel processing.

### Prerequisites
- Gemini CLI installed locally: `/opt/homebrew/bin/gemini`

### Usage
```bash
# Parallel code reviews
gemini -p "Review this code for best practices" < file.py &

# Generate documentation  
gemini -p "Generate API documentation" < lambda_function.py > docs/api.md &

# Security analysis
gemini -p "Perform security analysis" < template.yaml &
```

Use background processes (`&`) for parallel execution and `wait` to synchronize completion.

## State Management with Mem0 MCP Server

Project requires Mem0 MCP server for maintaining context across development sessions.

### Configuration
- **Project**: `cyngular-aws-onboarding`
- **Categories**: architecture, implementation, operations, guidelines

Store memories about Lambda naming conventions, service configuration logic, deployment patterns, production readiness best practices, and development guidelines in the dedicated project space.

### Key Information for Mem0 Storage
- **Lambda Architecture**: ServiceOrchestrator → RegionalServiceManager pattern with asynchronous invocation
- **Production Standards**: Environment variable validation, metrics integration, security hardening
- **Git Workflow**: feature → dev → main → release/v3.8 with DEVOPS-885 commit requirements
- **Testing Requirements**: ruff syntax checking mandatory before commits

**Note**: If the Mem0 project doesn't exist, please create it manually.

## Development Notes

- All CloudFormation templates follow AWS best practices with proper parameter validation
- Lambda functions include production-grade error handling, metrics, and security hardening
- The system supports both single-account and organization-wide deployments
- Gen3 architecture uses managed StackSet resources for simplified operations
- Service Manager automatically discovers and processes all enabled regions
- Use Gemini CLI for complex analysis and code generation tasks
- Maintain project state in Mem0 MCP server for context continuity
- All Lambda functions use fail-fast environment variable validation patterns
- CloudWatch metrics are collected via dedicated metrics.py modules
- Security: No stack traces exposed in production responses
- Testing: ruff syntax checking required before all commits