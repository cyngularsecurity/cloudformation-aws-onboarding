# Maintenance Guide

This guide provides instructions for maintaining and updating existing Cyngular AWS client deployments.

## Updating Lambda Functions

Lambda code is deployed to S3 via CI (GitHub Actions) on every push to main. To update a deployed Lambda to the latest version:

### Via AWS Console

1. Navigate to **AWS Lambda service** in the AWS Console
2. Select the Lambda function you want to update
3. In the **Code** panel, click **Upload from** > **Amazon S3 location**
4. Provide the S3 object URL using the template below:

```
https://cyngular-onboarding-${AWS_REGION}.s3.${AWS_REGION}.amazonaws.com/lambdas/services/latest/${SERVICE_ZIP}
```

### Via AWS CLI

```bash
aws lambda update-function-code \
  --function-name <LAMBDA_FUNCTION_NAME> \
  --s3-bucket cyngular-onboarding-${AWS_REGION} \
  --s3-key lambdas/services/latest/${SERVICE_ZIP} \
  --region ${AWS_REGION}
```

**Available Lambda packages:**

| Package | Lambda naming pattern | Description |
|---------|----------------------|-------------|
| `ServiceManager.zip` | `cyngular-service-orchestrator-${CLIENT}` | Service orchestrator (dispatches to regions) |
| `RegionProcessor.zip` | `cyngular-regional-service-manager-${CLIENT}` | Regional service manager (DNS, VFL, EKS, OS per region) |
| `UpdateBucketPolicy.zip` | `cyngular-bucket-policy-manager-${CLIENT}` | S3 bucket policy configuration |

> [!TIP]
> Always verify the Lambda function's region matches the AWS_REGION in the S3 URL to ensure compatibility.

## Updating CloudFormation Stacks

CFN templates are synced to S3 on every push to main. To update an existing stack:

### Via AWS Console

1. Navigate to **CloudFormation** > **Stacks**
2. Select the stack to update > **Update**
3. Choose **Replace current template** > **Amazon S3 URL**
4. Use:
   ```
   https://cyngular-onboarding-templates.s3.us-east-1.amazonaws.com/cfn/latest/${TEMPLATE_NAME}
   ```
5. Review/update parameters and submit

### Updating StackSet Instances

1. Navigate to **CloudFormation** > **StackSets**
2. Select the StackSet > **Actions** > **Edit StackSet details**
3. Replace template URL with the latest S3 path
4. Review parameters and submit
5. The update will roll out to all stack instances

## Retriggering the Service Manager

To force the Service Manager Lambda to re-run (e.g., after updating Lambda code or adding new regions):

- Update the **Services** stack and increment the `ServiceManagerOverride` parameter by 1
- This triggers the CloudFormation custom resource which invokes the Service Manager Lambda

## Available Templates

| Template | S3 Key | Purpose |
|----------|--------|---------|
| `ReadonlyRole.yaml` | `cfn/latest/ReadonlyRole.yaml` | Cross-account IAM role |
| `Core.yaml` | `cfn/latest/Core.yaml` | S3 bucket, CloudTrail, Lambda layer |
| `Services.yaml` | `cfn/latest/Services.yaml` | Service orchestration Lambdas |
| `Cleanup.yaml` | `cfn/latest/Cleanup.yaml` | Offboarding cleanup functions |
| `s3-events-ingestion.yaml` | `cfn/latest/s3-events-ingestion.yaml` | EventBridge + SQS for S3 log ingestion |
