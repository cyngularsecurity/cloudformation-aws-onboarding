# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Cyngular AWS client onboarding system that automates the deployment of security monitoring infrastructure using AWS CloudFormation StackSets. The system enables Cyngular to monitor client AWS accounts for security analysis by deploying standardized CloudFormation templates across multiple regions and accounts.

## Architecture

The project supports multiple generations of deployment architecture:

### Gen2 Architecture (Legacy)
- **CFN/CyngularOnBoarding.yaml**: Single CloudFormation template with Lambda-managed StackSets
- **Lambdas/**: Individual Lambda functions for each service
- Region list manually provided by client

### Gen3 Architecture (Current)
- **CFN/Gen3/**: CloudFormation templates with managed StackSets
- **Lambdas/Gen3/**: Consolidated Lambda architecture
- Auto-discovery of all enabled regions

## Gen3 Architecture Components

### 1. CloudFormation Templates (`CFN/Gen3/`)
- **Core.yaml**: S3 storage, CloudTrail, and core infrastructure resources
- **Services.yaml**: Lambda functions, roles, and service management infrastructure
- **ReadonlyRole.yaml**: IAM role for Cyngular cross-account access with required permissions
- **Layer.yaml**: Lambda layer deployment template for shared utilities
- **AWSCloudFormationStackSet*.yaml**: StackSet administration and execution role templates

### 2. Lambda Functions (`Lambdas/Gen3/`)
- **ServiceManager/** (CyngularServiceOrchestrator): Production-ready orchestrator that coordinates multi-region deployments
- **RegionProcessor/** (CyngularRegionalServiceManager): Worker lambda that processes individual regions with service registry integration
- **UpdateBucketPolicy/**: Manages S3 bucket policies for log collection
- **RemoveDNS/** & **RemoveVFL/**: Service cleanup functions for offboarding
- **Layer/**: Shared Lambda layer containing common utilities and dependencies

### 3. Service Registry Architecture (`service_registry.py`)
The codebase implements a plugin-style service architecture:
- **DNS Service** (`dns`): Route53 Resolver Query Log configuration with VPC association
- **VPC Flow Logs** (`vfl`): VPC Flow Logs enablement with S3 destination configuration  
- **EKS Service** (`eks`): EKS cluster audit logging and access entry management
- **OS Service** (`os`): Security monitoring agent deployment (always enabled)
- **Dynamic Service Loading**: Services are loaded based on enable parameters and support custom S3 buckets

### 4. Lambda Layer Architecture (`Lambdas/Gen3/Layer/`)
The Gen3 Lambda layer provides shared utilities to eliminate code duplication:
- **`python/cyngular_common/`**: Shared module package
  - **`metrics.py`**: Centralized CloudWatch metrics collector with validation
  - **`cfnresponse.py`**: CloudFormation custom resource response handling
  - **`__init__.py`**: Package initialization and exports
- **`requirements.txt`**: External dependencies (aioboto3, typing-extensions)
- **Layer Benefits**: Reduces deployment size, ensures consistency, simplifies maintenance

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
- **Lambda Layer Integration**: Shared utilities via `cyngular_common` layer reducing code duplication
- **Intelligent S3 Bucket Tagging**: Automatically tags appropriate buckets based on service configuration
- **Custom Bucket Support**: DNS and VFL services support custom S3 bucket destinations
- **Asynchronous Service Processing**: Service Orchestrator invokes Regional Service Manager asynchronously
- **Production-Grade Error Handling**: Structured logging with no stack trace exposure in production responses
- **Official Function Naming**: Professional naming convention (CyngularServiceOrchestrator, etc.)
- **Dynamic Parameter Passing**: Services receive enable parameters for intelligent bucket selection
- **CloudWatch Metrics Integration**: Comprehensive metrics collection with input validation
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


### 4. Deployment Scripts (`Scripts/Gen3/`)
- **deploy.sh**: Automated deployment script for Gen3 architecture
- **deploy-layer.sh**: Automated Lambda layer deployment script
- **update-lambdas-for-layer.sh**: Migrates existing Lambdas to use shared layer
- **offboarding.sh**: Automated offboarding script for Gen3 cleanup
- **LAYER_INSTRUCTIONS.md**: Comprehensive layer usage documentation

## Common Commands

### Gen3 Deployment (Recommended)
```bash
# Automated deployment using Gen3 script
./Scripts/Gen3/deploy.sh

# Manual deployment with Rain (Core stack)  
rain deploy CFN/Gen3/Core.yaml <stack-name> -y --debug \
  --params "ClientName=<name>,CyngularAccountId=<id>,OrganizationId=<org-id>,EnableDNS=true,EnableEKS=true,EnableVPCFlowLogs=true"

# Offboarding
./Scripts/Gen3/offboarding.sh
```

### Lambda Layer Management (Gen3)
```bash
# Build Lambda layer (creates zip file)
./Scripts/Gen3/BuildLayer.sh

# Deploy shared Lambda layer
./Scripts/Gen3/DeployLayer.sh

# Update existing Lambdas to use layer
./Scripts/Gen3/update-lambdas-for-layer.sh
```

### Legacy Gen2 deployment (not recommended)
```bash
rain deploy CFN/CyngularOnBoarding.yaml <stack-name> -y --debug \
  --params "ClientName=<name>,ClientRegions=<regions>,CyngularAccountId=<id>,OrganizationId=<org-id>"
```

### Code Quality and Testing
```bash
# Required syntax checking (mandatory before commits)
ruff check .
ruff format --check .

# Format code (optional - currently commented in deployment)
ruff format .

# Validate CloudFormation templates
rain fmt CFN/Gen3/*.yaml
aws cloudformation validate-template --template-body file://CFN/Gen3/Core.yaml

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

## Configuration

### Environment Configuration (.env)
The project uses a `.env` file for client-specific configuration:
```bash
# Required configuration variables
ClientName="client-name"                    # Client company name (3-15 chars, alphanumeric)
CyngularAccountId="123456789012"           # Cyngular AWS account ID  
OrganizationId="o-xxxxxxxxxx"              # AWS Organization ID (optional)
CloudTrailBucket="existing-bucket-name"    # Existing CloudTrail bucket (optional)

# Service enablement flags
EnableDNS="true"                           # Enable DNS logging (true/false/bucket-name)
EnableEKS="true"                           # Enable EKS monitoring (true/false)
EnableVPCFlowLogs="true"                   # Enable VPC Flow Logs (true/false/bucket-name)

# Deployment configuration
RUNTIME_REGION="us-east-1"                 # Primary deployment region
RUNTIME_PROFILE="default"                  # AWS CLI profile
ServiceManagerOverride=1                   # Force service manager redeployment
ExcludedRegions="eu-central-1,eu-west-1"   # Regions to exclude from scanning
```

### GitLab CI/CD
- Uses external pipeline from `cyngular-security/cyngular-devops/automation`
- Includes CloudFormation validation in CI pipeline
- Configuration: `.gitlab-ci.yml` with `CFN` as ZIP_FILES_PATH

## Prerequisites

Before deployment, ensure:
1. AWS Organizations services are enabled (if using organization deployment):
   - CloudFormation StackSets
   - CloudTrail
2. Appropriate IAM permissions for StackSet administration
3. Rain CLI tool installed (`brew install rain`)
4. AWS CLI configured with appropriate credentials
5. Environment variables configured in `.env` file

## Gen3 Architecture Benefits

- **Simplified Deployment**: Managed StackSet eliminates custom Lambda complexity
- **Auto-Region Discovery**: No need to manually specify regions
- **Consolidated Lambdas**: Two-lambda design reduces operational overhead
- **Better Error Handling**: Improved monitoring and debugging capabilities
- **Scalable**: Service Manager orchestrates across all enabled regions automatically

## Git Workflow and Development Process

The project follows a standard git workflow through the branch flow: `feature → dev → main → release/v3.8`.

### Critical Git Workflow Requirements
- **Always fetch and pull with rebase** before creating branches or PRs
- **Include DEVOPS-885 commit ID** to meet GitLab pre-receive hook requirements
- **Test with ruff** before creating any commits
- **Use proper commit message format** with ticket ID and Claude attribution

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

## Development Notes

- All CloudFormation templates follow AWS best practices with proper parameter validation
- Lambda functions include production-grade error handling, metrics, and security hardening
- The system supports both single-account and organization-wide deployments
- Gen3 architecture uses managed StackSet resources for simplified operations
- Service Manager automatically discovers and processes all enabled regions
- **Lambda Layer**: Use `from cyngular_common.metrics import MetricsCollector` and `from cyngular_common import cfnresponse` for shared utilities
- **Metrics Validation**: All metric values are validated to be numeric before CloudWatch submission
- All Lambda functions use fail-fast environment variable validation patterns
- CloudWatch metrics include input validation to prevent AWS API errors
- Security: No stack traces exposed in production responses, sensitive data handled securely
- Testing: ruff syntax checking required before all commits
- **S3 Bucket Convention**: Deployment buckets follow pattern `cyngular-onboarding-{region}`
- **Layer Deployment**: Always deploy layer before updating Lambda functions to use it