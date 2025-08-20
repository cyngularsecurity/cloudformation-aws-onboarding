
# On services parameters

provide true, for cyngular to collect logs
provide false, if the service should not be enabled,.

if already configured to log to an existing s3 bucket, add the following tags, respectivly to the buckets collecting logs:

- Cloud trail logs - {key: cyngular-cloudtrail, value: true}
- Vpc dns logs - {key: cyngular-dnslogs, value: true}
- Vpc flow logs - {key: cyngular-vpcflowlogs, value: true}
