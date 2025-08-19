# CloudFormation Aws On Boarding

## Deployment Steps

### Prerequisites

1. **Enable AWS Services**
   - Ensure the following services (trusted access) are enabled:
     - [AWS CloudTrail](CloudTrail)
   - If you are using the AWS Organizations feature, also:
     - [AWS CloudFormation StackSets](CloudFormation_StackSets)
     - In the AWS CloudFormation service panel, click on "Enable trusted access".
     - See [StackSets](StackSets) for more information.

2. **Create a CloudFormation Stack**
   - Ensure you are in your preferred AWS region.
   - Use Cyngular's template to deploy the Cyngular Onboarding Stack. [Deploy Cyngular Onboarding Stack](Deploy_Cyngular_Onboarding_Stack)

3. **Configure S3 Bucket**
   - If you're using your own S3 bucket (e.g., for CloudTrail, VPC Flow logs), add the specified tag from the CloudFormation template and apply the bucket policy using the provided [Bucket Policy](Bucket_Policy).
   - Only modify the bucket name.

4. **Complete Deployment**
   - After the deployment is complete, enter your management account ID and select your preferred regions.
   - Click "Connect".

[CloudTrail]: https://us-east-1.console.aws.amazon.com/organizations/v2/home/services/CloudTrail
[CloudFormation_StackSets]: https://us-east-1.console.aws.amazon.com/organizations/v2/home/services/CloudFormation%20StackSets

[Deploy_Cyngular_Onboarding_Stack]: https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/quickcreate?templateURL=https://cyngular-onboarding-templates.s3.amazonaws.com/stacks/CyngularOnBoarding.yaml&stackName=CyngularOnBoarding

[Bucket_Policy]: https://cyngular-onboarding-templates.s3.us-east-1.amazonaws.com/stacks/bucket-policy-s3-statement.json


[StackSets]: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stacksets-prereqs.html