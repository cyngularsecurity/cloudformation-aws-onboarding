# CloudFormation Aws On Boarding

## Deployment Steps

### Prerequisites

1. **Enable AWS Services**
   - Ensure the following services (trusted access) are enabled:
     - [AWS CloudTrail - console][CloudTrail]
   - If you are using the AWS Organizations feature, also:
     - [AWS CloudFormation StackSets - console][CloudFormation_StackSets]
     - In the AWS CloudFormation service panel, click on "Enable trusted access".
     - See [StackSets - docs][StackSets] for more information.

2. **Deploy Stacks and StackSets**

   - Ensure you are in your preferred AWS region and your AWS CLI profile is configured.
   - You can deploy using the helper script (recommended) or manually.

   - Option A — Scripted deploy (recommended)
     - Copy the `.env.example` file to `.env` and fill the required values.
     - Install dependencies: `rain` and `awscli`.
     - From the project root, run: `Scripts/RainDeployOB.sh`.

   - Option B — Manual deploy
     - See: [Manual Deployment Guide](./MANUAL_DEPLOY.md) — AWS Console step-by-step guide for deploying stacks and stack sets.

3. **Configure S3 Bucket**
   - If you're using your own S3 bucket (e.g., for CloudTrail, VPC Flow logs), add the specified tag from the CloudFormation template and apply the bucket policy using the provided [Bucket Policy - raw][Bucket_Policy].
   - Only modify the bucket name.

4. **Complete Deployment**
   - After the deployment is complete, enter your management account ID and select your preferred regions.
   - Click "Connect".

[CloudTrail]: https://us-east-1.console.aws.amazon.com/organizations/v2/home/services/CloudTrail
[CloudFormation_StackSets]: https://us-east-1.console.aws.amazon.com/organizations/v2/home/services/CloudFormation%20StackSets

[Bucket_Policy]: https://cyngular-onboarding-templates.s3.us-east-1.amazonaws.com/stacks/S3-Bucket-Policy-Statement.json

[StackSets]: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stacksets-prereqs.html
