# Aws Client On Boarding

## LINK

* "<https://eu-west-3.console.aws.amazon.com/cloudformation/home?region=eu-west-3#/stacks/create/review?templateURL=https://cyngular-onboarding-templates.s3.amazonaws.com/v3/stacks/CyngularOnBoarding.yaml&stackName=CyngularOnBoarding>"

* Click on the provided URL to open the AWS CloudFormation console.
* Switch to Preferred Region.
* Fill in the required parameters.

For services parameters:
provide true, for cyngular to collect logs
provide false, if the service should not be enabled, or if is already configured to log to an existing s3 bucket, add the respective tags to the buckets collecting logs:

Cloud trail logs - {key: cyngular-cloudtrail, value: true}
Vpc dns logs - {key: cyngular-dnslogs, value: true}
Vpc flow logs - {key: cyngular-vpcflowlogs, value: true}

--

Review the stack details and click on "Create Stack" to initiate the process.
Monitor Stack status to change to CREATE_COMPLETE.