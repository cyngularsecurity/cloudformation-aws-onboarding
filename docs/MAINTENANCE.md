# Maintenance Guide

This guide provides instructions for maintaining and updating existing Cyngular AWS client deployments.

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

- `UpdateBucketPolicy.zip` - S3 bucket policy configuration service
- `RegionProcessor.zip` - Regional service manager
- `ServiceManager.zip` - Service orchestrator

> [!TIP]
> Always verify the Lambda function's region matches the AWS_REGION in the S3 URL template to ensure compatibility.
