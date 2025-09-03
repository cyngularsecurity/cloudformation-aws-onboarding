# CloudFormation Aws On Boarding

## Prerequisites

- set values in .env file [as described in service configuration](./SERVICE_CONFIGURATION.md#settings-in-env)

<!-- Note: Parameter names must match exactly as shown below. StackSets do not support unknown parameters; only supply those listed. -->

### Prerequisites

1. **Enable AWS Services**
   - Ensure the following services (trusted access) are enabled:
     - [AWS CloudTrail - console][CloudTrail]
   - If you are using the AWS Organizations feature, also:
     - [AWS CloudFormation StackSets - console][CloudFormation_StackSets]
     - In the AWS CloudFormation service panel, click on "Enable trusted access".
     - See [StackSets - docs][StackSets] for more information.

### Deployment Steps

1. **Deploy Stacks and StackSets**

   - Ensure you are in your preferred AWS region and your AWS CLI profile is configured.
   - You can deploy using the helper script (recommended) or manually.

   - Option A — Scripted deploy (recommended)
     <!-- - Install dependencies: `rain` and `awscli`. -->
     - Copy the `.env.example` file to `.env` and Configure parameters.
     - From the project root, run: `Scripts/RainDeployOB.sh`.
     <!-- - Monitor deployment: `rain log <stack-name> --chart` -->

   - Option B — Manual deploy
     - See: [Manual Deployment Guide](./MANUAL_DEPLOY.md) — AWS Console step-by-step guide for deploying stacks and stack sets.

2. **Using custom S3 bucket for services logs**
   - (e.g., for CloudTrail, VPC Flow logs)
   - **Apply tags**: add the specified tag as defined in [Service Configuration](./SERVICE_CONFIGURATION.md).
   - **Update Bucket policy**: update existing or create new, including the provided statement in the policy [Bucket Policy - raw](./SERVICE_CONFIGURATION.md) or [Bucket_Policy].
   - Only modify the bucket name.

3. **Complete Deployment**
   - After the deployment is complete, enter your management account ID and select your preferred regions.
   - Click "Connect".

---

[CloudTrail]: https://us-east-1.console.aws.amazon.com/organizations/v2/home/services/CloudTrail
[CloudFormation_StackSets]: https://us-east-1.console.aws.amazon.com/organizations/v2/home/services/CloudFormation%20StackSets

[Bucket_Policy]: https://cyngular-onboarding-templates.s3.us-east-1.amazonaws.com/stacks/S3-Bucket-Policy-Statement.json

[StackSets]: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stacksets-prereqs.html
