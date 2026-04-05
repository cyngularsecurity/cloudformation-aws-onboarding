# Notes & Caveats

- **Organization Deployments:** Organization ID is required only when deploying from the management account. Deployment from a member account will fail on CloudTrail permissions.

- **Region Discovery:** The Service Manager automatically discovers all enabled regions. Use the `ExcludedRegions` parameter to skip specific regions.

- **OS Service (auditd):** Installs auditd on running EC2 instances via SSM. Instances without SSM agent or Windows instances will be skipped — this is expected.

- **Bucket Policy Manager:** Runs daily to maintain S3 bucket policy for log delivery. Safe to run repeatedly — it replaces (not appends) the relevant policy statements each time.

- **Custom Buckets:** For DNS and VPC Flow Logs, you can pass a bucket name instead of `true`/`false`. See [Service Configuration](./SERVICE_CONFIGURATION.md).
