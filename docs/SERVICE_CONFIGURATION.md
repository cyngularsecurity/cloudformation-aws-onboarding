# Service Configuration Guide

## Service Enablement Options

For each service, you can provide one of the following values:

- **`"true"`** - Enable service with Cyngular-managed S3 bucket
- **`"false"`** - Disable the service completely
- **`"bucket-name"`** - Use existing custom S3 bucket (DNS and VPC Flow Logs only)

## Using Existing S3 Buckets

If you already have S3 buckets configured for logging, add the following tags to enable Cyngular collection:

- **CloudTrail logs**: `{key: cyngular-cloudtrail, value: true}`
- **VPC DNS logs**: `{key: cyngular-dnslogs, value: true}`
- **VPC Flow logs**: `{key: cyngular-vpcflowlogs, value: true}`
- **EKS audit logs**: `{key: cyngular-ekslogs, value: true}` (Cyngular bucket only)

When using existing buckets, also update the bucket policy to allow Cyngular access. See the policy template at [`CFN/S3-Bucket-Policy-Statement.json`](../CFN/S3-Bucket-Policy-Statement.json).

## Settings in .env

> **Note:** The `.env` file is only used with the Rain CLI deployment method. If deploying via the AWS Console, provide these values as CloudFormation parameters directly.

### Sample - [.env.example](../.env.example)

### Required Variables

| Variable | Description | Default |
|----------|-------------|---------|
| **CLIENT_NAME** | Short identifier for your organization (lowercase, 3-15 chars, alphanumeric) | - |
| **RUNTIME_REGION** | Primary region where resources are created | `us-east-1` |
| **RUNTIME_PROFILE** | AWS CLI profile to use for deployment | `default` |
| **CYNGULAR_ACCOUNT_ID** | Cyngular AWS account ID | `851565895544` |

### Organization Variables (required for org deployments)

| Variable | Description |
|----------|-------------|
| **CLIENT_MGMT_ACCOUNT_ID** | Management account ID |
| **ORGANIZATION_ID** | AWS Organization ID (e.g. `o-xxxxxxxxxx`) |
| **ORGANIZATIONAL_UNIT_IDS** | Comma-separated OU IDs (use root OU for org-wide) |

### Feature Flags

| Variable | Description | Options | Default |
|----------|-------------|---------|---------|
| **EnableCloudTrail** | Create CloudTrail trail | `true`/`false` | `true` |
| **EnableDNS** | Enable DNS logging | `true`/`false`/`bucket-name` | `true` |
| **EnableEKS** | Enable EKS audit logging | `true`/`false` | `true` |
| **EnableVPCFlowLogs** | Enable VPC Flow Logs | `true`/`false`/`bucket-name` | `true` |
| **EnableBucketPolicyManager** | Enable bucket policy management | `true`/`false` | `true` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| **CloudTrailBucket** | Existing CloudTrail bucket name | `""` |
| **ExcludedRegions** | Comma-separated regions to exclude | `""` |
| **ServiceManagerOverride** | Increment to retrigger Service Manager Lambda | `1` |

## Example .env

```bash
CLIENT_NAME="acme"
RUNTIME_REGION="us-east-1"
RUNTIME_PROFILE="default"
CYNGULAR_ACCOUNT_ID="851565895544"

# Organization settings (omit for single-account deployment)
# CLIENT_MGMT_ACCOUNT_ID="111122223333"
# ORGANIZATION_ID="o-abc123def"
# ORGANIZATIONAL_UNIT_IDS="r-kdxm"

# Services
EnableCloudTrail="true"
EnableDNS="true"
EnableEKS="true"
EnableVPCFlowLogs="true"
EnableBucketPolicyManager="true"
```
