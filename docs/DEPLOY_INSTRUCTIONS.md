# CloudFormation AWS Onboarding

## Prerequisites

1. **Enable AWS Services**
   - Ensure the following services (trusted access) are enabled:
     - [AWS CloudTrail - console][CloudTrail]
   - If you are using AWS Organizations, also enable:
     - [AWS CloudFormation StackSets - console][CloudFormation_StackSets]
     - See [StackSets - docs][StackSets] for more information.

## Deployment

- **Option A — AWS Console** (recommended)
  - See: [Manual Deployment Guide](./MANUAL_DEPLOY.md) — step-by-step guide for deploying stacks and StackSets.

- **Option B — Rain CLI** (for development and advanced users)
  - Requires: [Rain CLI](https://aws-cloudformation.github.io/rain/) and AWS CLI.
  - Copy `.env.example` to `.env` and configure parameters (see [Service Configuration](./SERVICE_CONFIGURATION.md#settings-in-env)).
  - Run: `Scripts/RainDeployOB.sh`

## Using Custom S3 Buckets (optional)

If you already have S3 buckets for CloudTrail or VPC Flow Logs:

1. **Tag your buckets** as defined in [Service Configuration](./SERVICE_CONFIGURATION.md#using-existing-s3-buckets).
2. **Update bucket policy** using the template at [`CFN/S3-Bucket-Policy-Statement.json`](../CFN/S3-Bucket-Policy-Statement.json) — replace the bucket name and account ID placeholders.

## After Deployment

Enter your management account ID and select your preferred regions in the Cyngular console, then click **Connect**.

---

[CloudTrail]: https://us-east-1.console.aws.amazon.com/organizations/v2/home/services/CloudTrail
[CloudFormation_StackSets]: https://us-east-1.console.aws.amazon.com/organizations/v2/home/services/CloudFormation%20StackSets
[StackSets]: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stacksets-prereqs.html
