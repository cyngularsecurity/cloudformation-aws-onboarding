# Cyngular AWS Client Onboarding

Automated deployment of security monitoring infrastructure for AWS accounts using CloudFormation Templates.

<!-- ## Quick Start

1. Configure client parameters in `.env` file
2. Run deployment: `./Scripts/RainDeployOB.sh`
3. Monitor deployment: `rain log <stack-name> --chart` -->

## Documentation

- [Deployment Instructions](./docs/INSTRUCTIONS.md) - Prerequisites and deployment steps
- [Service Configuration](./docs/CYNGULAR_SERVICES.md) - Service enablement options

## Architecture

**CloudFormation Templates** with automated region discovery

### CloudFormation Templates ([`CFN/`](./CFN/))

#### If not created already

- [`AWSCloudFormationStackSetAdministrationRole.yaml`](./CFN/AWSCloudFormationStackSetAdministrationRole.yaml) - StackSet admin role
- [`AWSCloudFormationStackSetExecutionRole.yaml`](./CFN/AWSCloudFormationStackSetExecutionRole.yaml) - StackSet execution role

#### Then

- [`ReadonlyRole.yaml`](./CFN/ReadonlyRole.yaml) - Cross-account IAM role for Cyngular access
- [`Core.yaml`](./CFN/Core.yaml) - S3 storage, CloudTrail, and core infrastructure
- [`Services.yaml`](./CFN/Services.yaml) - Lambda functions services

### Lambda Functions ([`Lambdas/`](./Lambdas/))

- **[Services/](./Lambdas/Services/)**
  - [`ServiceManager/`](./Lambdas/Services/ServiceManager/) - Cyngular Service Orchestrator (coordinates multi-region deployments)
  - [`RegionProcessor/`](./Lambdas/Services/RegionProcessor/) - Cyngular Regional Service Manager (processes individual regions)
  - [`UpdateBucketPolicy/`](./Lambdas/Services/UpdateBucketPolicy/) - S3 bucket policy management
  - [`Layer/`](./Lambdas/Services/Layer/) - Shared Lambda layer with common utilities

- **[Cleaners/](./Lambdas/Cleaners/)**
  - [`RemoveDNS/`](./Lambdas/Cleaners/RemoveDNS/) - DNS logging cleanup
  - [`RemoveVFL/`](./Lambdas/Cleaners/RemoveVFL/) - VPC Flow Logs cleanup

## Requirements

- AWS CLI configured
- Rain CLI ([docs](https://aws-cloudformation.github.io/rain/)) (`brew install rain`)
- AWS Organizations (if deploying to an organization)
- Appropriate IAM permissions (Admin)
