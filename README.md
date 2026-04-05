# Cyngular AWS Client Onboarding

Automated deployment of security monitoring infrastructure for AWS accounts using CloudFormation Templates.

## Requirements

- Appropriate IAM permissions (Global Admin)
- AWS CLI installed & configured
- [CloudFormation Templates](#cloudformation-templates-cfn) for deployment

## Optional

- Rain CLI ([docs](https://aws-cloudformation.github.io/rain/)) (`brew install rain`)
- AWS Organizations (if deploying to an organization)

## Quick Start

- [Deployment Instructions](./docs/DEPLOY_INSTRUCTIONS.md) - Prerequisites and deployment steps
- [Service Configuration](./docs/SERVICE_CONFIGURATION.md) - Service enablement options
- [Maintenance Guide](./docs/MAINTENANCE.md) - Manage existing deployments

## Architecture

**CloudFormation Templates** with automated region discovery

### CloudFormation Templates ([`CFN/`](./CFN/))

#### AWS CFN Access Management - If using organizations & not created already

- [`AWSCloudFormationStackSetAdministrationRole.yaml`](./CFN/AWSCloudFormationStackSetAdministrationRole.yaml) - StackSet admin role
- [`AWSCloudFormationStackSetExecutionRole.yaml`](./CFN/AWSCloudFormationStackSetExecutionRole.yaml) - StackSet execution role

#### Cyngular Onboarding (in order)

- [`ReadonlyRole.yaml`](./CFN/ReadonlyRole.yaml) - Cross-account IAM role for Cyngular access
- [`Core.yaml`](./CFN/Core.yaml) - S3 storage, CloudTrail, and core infrastructure (always, on management account only)
- [`Services.yaml`](./CFN/Services.yaml) - Lambda functions services

#### Additional Templates

- [`bucket_and_trail.yaml`](./CFN/bucket_and_trail.yaml) - Standalone S3 bucket and CloudTrail setup (alternative to Core.yaml for specific use cases)
- [`s3-events-ingestion.yaml`](./CFN/s3-events-ingestion.yaml) - EventBridge rules and SQS queues for S3 log ingestion across multiple log types (CloudTrail, VPC Flow Logs, DNS, EKS)
- [`Cleanup.yaml`](./CFN/Cleanup.yaml) - Offboarding cleanup - For Lambda functions (DNS and VPC Flow Logs removal)

### Lambdas Services ([`Lambdas/`](./Lambdas/))

- **[Services/](./Lambdas/Services/)**
  - [`ServiceManager/`](./Lambdas/Services/ServiceManager/) - Cyngular Service Orchestrator
  - [`RegionProcessor/`](./Lambdas/Services/RegionProcessor/) - Cyngular Regional Service Manager (processes each service per region)
  - [`UpdateBucketPolicy/`](./Lambdas/Services/UpdateBucketPolicy/) - S3 bucket policy configuration
  - [`Layer/`](./Lambdas/Services/Layer/) - Shared Lambda layer with common utilities

- **[Cleaners/](./Lambdas/Cleaners/)**
  - [`RemoveVFL/`](./Lambdas/Cleaners/RemoveVFL/) - VPC Flow Logs cleanup (Required for offboarding)
  - [`RemoveDNS/`](./Lambdas/Cleaners/RemoveDNS/) - DNS logging cleanup (Optional for offboarding)

### Offboarding

See [Offboarding Guide](./Charts/Cleanup.md) for the full decommissioning process.
