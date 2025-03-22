# Aws Client On Boarding

## Prerequisites

* client AWS Organizations > Services trusted access to enable
  * CloudFormation StackSets
  * CloudTrail

* Click on the provided URL to open the AWS CloudFormation console.
  * Switch to Preferred Region.
  * Fill in the required parameters.

For services parameters:
provide true, for cyngular to collect logs
provide false, if the service should not be enabled,
if already configured to log to an existing s3 bucket, add the respective tags to the buckets collecting logs:

Cloud trail logs - {key: cyngular-cloudtrail, value: true}
Vpc dns logs - {key: cyngular-dnslogs, value: true}
Vpc flow logs - {key: cyngular-vpcflowlogs, value: true}


## Cavieates

* Organization Id is required only if deploying to an organization, from the management account,
deployment to an org from a member account will fail on cloudtrail permissions.

* ClientRegions contains all the regions the client is operation in,
the client main region, included in the list but determind by the region the main stack is deployed to.

## LINK

* "<https://eu-west-3.console.aws.amazon.com/cloudformation/home?region=eu-west-3#/stacks/create/review?templateURL=https://cyngular-onboarding-templates.s3.amazonaws.com/v3/stacks/CyngularOnBoarding.yaml&stackName=CyngularOnBoarding>"


* "https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stacksets-prereqs.html"