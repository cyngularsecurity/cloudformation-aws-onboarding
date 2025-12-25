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

## Updating Lambda Functions

To update Lambda functions to newer versions via AWS Console:

1. Navigate to **AWS Lambda service** in the AWS Console
2. Select the Lambda function you want to update
3. In the **Code** panel, click **Upload from** → **Amazon S3 location**
4. Provide the S3 object URL using the template below:

```bash
AWS_REGION="us-east-1"  # Use the deployed main region of the client
SERVICE_ZIP="UpdateBucketPolicy.zip"  # Choose from available zips

https://cyngular-onboarding-${AWS_REGION}.s3.${AWS_REGION}.amazonaws.com/lambdas/services/latest/${SERVICE_ZIP}
```

**Available Lambda packages:**

- `UpdateBucketPolicy.zip`
- `RegionProcessor.zip`
- `ServiceManager.zip`

## Architecture

**CloudFormation Templates** with automated region discovery

### CloudFormation Templates ([`CFN/`](./CFN/))

#### AWS CFN Access Management - If using organizations & not created already

- [`AWSCloudFormationStackSetAdministrationRole.yaml`](./CFN/AWSCloudFormationStackSetAdministrationRole.yaml) - StackSet admin role
- [`AWSCloudFormationStackSetExecutionRole.yaml`](./CFN/AWSCloudFormationStackSetExecutionRole.yaml) - StackSet execution role

#### Then **Cyngular Onboarding** (in order)

- [`ReadonlyRole.yaml`](./CFN/ReadonlyRole.yaml) - Cross-account IAM role for Cyngular access
- [`Core.yaml`](./CFN/Core.yaml) - S3 storage, CloudTrail, and core infrastructure (always, on management account only)
- [`Services.yaml`](./CFN/Services.yaml) - Lambda functions services

### Lambdas Services ([`Lambdas/`](./Lambdas/))

- **[Services/](./Lambdas/Services/)**
  - [`ServiceManager/`](./Lambdas/Services/ServiceManager/) - Cyngular Service Orchestrator
  - [`RegionProcessor/`](./Lambdas/Services/RegionProcessor/) - Cyngular Regional Service Manager (processes each service per region)
  - [`UpdateBucketPolicy/`](./Lambdas/Services/UpdateBucketPolicy/) - S3 bucket policy configuration
  - [`Layer/`](./Lambdas/Services/Layer/) - Shared Lambda layer with common utilities

- **[Cleaners/](./Lambdas/Cleaners/)**
  - [`RemoveVFL/`](./Lambdas/Cleaners/RemoveVFL/) - VPC Flow Logs cleanup (Required for offboarding)
  - [`RemoveDNS/`](./Lambdas/Cleaners/RemoveDNS/) - DNS logging cleanup (Optional for offboarding)
