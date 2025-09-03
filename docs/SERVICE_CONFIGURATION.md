# Service Configuration Guide

## Service Parameters

### Service Enablement Options

For each service, you can provide one of the following values:

- **`"true"`** - Enable service with Cyngular-managed S3 bucket
- **`"false"`** - Disable the service completely  
- **`"bucket-name"`** - Use existing custom S3 bucket (DNS and VPC Flow Logs only)

### Using Existing S3 Buckets

If you already have S3 buckets configured for logging, add the following tags to enable Cyngular collection:

- **CloudTrail logs**: `{key: cyngular-cloudtrail, value: true}`
- **VPC DNS logs**: `{key: cyngular-dnslogs, value: true}`
- **VPC Flow logs**: `{key: cyngular-vpcflowlogs, value: true}`
- **EKS audit logs**: `{key: cyngular-ekslogs, value: true}` (Cyngular bucket only)

## Settings in .env

### Sample - [Settings in .env](../.env.example)

### Required Variables

| Variable | Description | Default |
|----------|-------------|---------|
| **CLIENT_NAME** | Short identifier for your organization (lowercase, 3-15 chars, alphanumeric) | `-` |
| **RUNTIME_REGION** | Your primary region where resources are created | `us-east-1` |
| **RUNTIME_PROFILE** | AWS CLI profile to use for deployment | `default` |
| **CYNGULAR_ACCOUNT_ID** | Cyngular AWS account ID | `851565895544` |

### Organization Deployment Variables

Required when deploying to AWS Organizations:

| Variable | Description | Default |
|----------|-------------|---------|
| **CLIENT_MGMT_ACCOUNT_ID** | Client Management account ID | `-` |
| **ORGANIZATION_ID** | AWS Organization ID | `o-xxxxxxxxxx` |
| **ORGANIZATIONAL_UNIT_IDS** | Comma-separated OU IDs (no spaces)<br/>Use root OU ID (`r-xxxx`) for org-wide deployment | `r-kdxm` |

### Feature Flags

| Variable | Description | Options | Default |
|----------|-------------|---------|---------|
| **EnableCloudTrail** | Create CloudTrail trail | `true`/`false` | `true` |
| **EnableDNS** | Enable DNS logging service | `true`/`false`/`bucket-name` | `true` |
| **EnableEKS** | Enable EKS audit logging | `true`/`false` | `true` |
| **EnableVPCFlowLogs** | Enable VPC Flow Logs | `true`/`false`/`bucket-name` | `true` |
| **EnableBucketPolicyManager** | Enable cross-account bucket policy management | `true`/`false` | `true` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| **CloudTrailBucket** | Existing CloudTrail bucket name (if already configured) | `""` |
| **ExcludedRegions** | Comma-separated list of regions to exclude from service manager lookup | `""` |
| **ServiceManagerOverride** | Increment to retrigger ServiceManager Lambda from CloudFormation stack | `1` |

### StackSet Operation Tuning

| Variable | Description | Range | Default |
|----------|-------------|-------|---------|
| **FAILURE_TOLERANCE_PERCENTAGE** | Percentage of accounts that can fail before stopping deployment | 0-100 | `25` |
| **MAX_CONCURRENT_PERCENTAGE** | Maximum percentage of accounts to deploy to concurrently | 1-100 | `90` |

## Example .env Configuration

### Single Account Deployment
```bash
# Required
CLIENT_NAME="acme"
RUNTIME_REGION="us-east-1"
RUNTIME_PROFILE="default"
CYNGULAR_ACCOUNT_ID="851565895544"

# Services
EnableCloudTrail="true"
EnableDNS="true"
EnableEKS="true"
EnableVPCFlowLogs="true"
EnableBucketPolicyManager="false"

# Optional
ServiceManagerOverride=1
```

### Organization-Wide Deployment
```bash
# Required
CLIENT_NAME="enterprise"
RUNTIME_REGION="us-east-1"
RUNTIME_PROFILE="org-mgmt"
CYNGULAR_ACCOUNT_ID="851565895544"

# Organization settings (required for org deployment)
CLIENT_MGMT_ACCOUNT_ID="111122223333"
ORGANIZATION_ID="o-abc123def"
ORGANIZATIONAL_UNIT_IDS="r-kdxm"  # Root OU for org-wide

# Services
EnableCloudTrail="true"
EnableDNS="true"
EnableEKS="true"
EnableVPCFlowLogs="true"
EnableBucketPolicyManager="true"

# Optional tuning
ServiceManagerOverride=1
MAX_CONCURRENT_PERCENTAGE="75"
FAILURE_TOLERANCE_PERCENTAGE="30"
ExcludedRegions="eu-central-1,sa-east-1"
```

### Using Existing Buckets
```bash
# Required
CLIENT_NAME="hybrid"
RUNTIME_REGION="us-west-2"
RUNTIME_PROFILE="default"
CYNGULAR_ACCOUNT_ID="851565895544"

# Use existing buckets for some services
CloudTrailBucket="my-existing-cloudtrail-bucket"
EnableDNS="my-dns-logs-bucket"        # Custom bucket for DNS logs
EnableVPCFlowLogs="my-vpc-logs-bucket" # Custom bucket for VPC Flow Logs
EnableEKS="true"                       # Uses Cyngular bucket
EnableBucketPolicyManager="false"
```