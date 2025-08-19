# Cyngular AWS Client Onboarding

Automated deployment of security monitoring infrastructure for AWS accounts using CloudFormation Templates.

## Quick Start

1. Configure client parameters in `.env` file
2. Run deployment: `./Scripts/RainDeployOB.sh`
3. Monitor deployment: `rain log <stack-name> --chart`

## Documentation

- [Deployment Instructions](./docs/INSTRUCTIONS.md) - Prerequisites and deployment steps
- [Service Configuration](./docs/CYNGULAR_SERVICES.md) - Service enablement options
- [Architecture Diagrams](./Charts/) - Visual workflow and architecture diagrams

## Architecture

**CloudFormation Templates** with automated region discovery

### CloudFormation Templates (`CFN/`)

#### If not created already

- `AWSCloudFormationStackSetAdministrationRole.yaml` - StackSet admin role
- `AWSCloudFormationStackSetExecutionRole.yaml` - StackSet execution role

#### Then

- `ReadonlyRole.yaml` - Cross-account IAM role for Cyngular access
- `Core.yaml` - S3 storage, CloudTrail, and core infrastructure
- `Services.yaml` - Lambda functions and service management

### Lambda Functions (`Lambdas/`)

- **Services/**
  - `ServiceManager/` - Cyngular Service Orchestrator (coordinates multi-region deployments)
  - `RegionProcessor/` - Cyngular Regional Service Manager (processes individual regions)
  - `UpdateBucketPolicy/` - S3 bucket policy management
  - `Layer/` - Shared Lambda layer with common utilities

- **Cleaners/**
  - `RemoveDNS/` - DNS logging cleanup
  - `RemoveVFL/` - VPC Flow Logs cleanup

## Key Features

- Cross-account security monitoring
- Multi-region automated deployment
- Service-based architecture:
  - **DNS**: Route53 Resolver Query Log configuration
  - **VFL**: VPC Flow Logs to S3
  - **EKS**: Cluster audit logging and access management
  - **OS**: Security monitoring agent deployment
- Organization-wide StackSet support
- Production-grade error handling and CloudWatch metrics
- Lambda layer architecture for shared utilities

## Requirements

- AWS CLI configured
- Rain CLI ([docs](https://aws-cloudformation.github.io/rain/)) (`brew install rain`)
- AWS Organizations (if using org deployment)
- Appropriate IAM permissions (Admin)
