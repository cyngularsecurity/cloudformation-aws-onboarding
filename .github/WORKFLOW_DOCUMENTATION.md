# Deploy to S3 Workflow Documentation

## Overview

The `deploy-to-s3-refactored.yml` workflow automates the deployment of CloudFormation templates and Lambda functions to AWS S3 across multiple regions. The workflow uses a modular architecture with composite actions for reusability and maintainability.

## Architecture

### Core Components

1. **Enhanced S3 Sync Script** (`s3_sync.py`)
2. **Composite Actions** (`.github/actions/`)
3. **Main Workflow** (`deploy-to-s3-refactored.yml`)

### Deployment Strategy

- **CloudFormation**: Centralized deployment to single S3 bucket per environment
- **Lambda Functions**: Multi-region deployment with automatic bucket discovery
- **Lambda Layer**: Multi-region deployment using same strategy as functions
- **Versioning**: Dual deployment (timestamp + latest) for all components

## Workflow Triggers

### Automatic Triggers
- **Push events** to branches: `main`, `dev`, `stg`
- **Path filters**: Only triggers when files change in:
  - `CFN/**` (CloudFormation templates)
  - `Lambdas/**` (Lambda functions)
  - `.github/workflows/deploy-to-s3-refactored.yml`
  - `.github/actions/**` (Composite actions)
  - `.github/scripts/s3_sync.py`

### Manual Triggers
- **workflow_dispatch** with inputs:
  - `environment`: Target environment (dev/stg/prod)
  - `deploy_cfn`: Enable/disable CloudFormation deployment
  - `deploy_lambdas`: Enable/disable Lambda deployment

## Environment Configuration

### Branch to Environment Mapping
- `main` branch → `prod` environment
- `stg` branch → `stg` environment  
- All other branches → `dev` environment

### S3 Bucket Structure
```
Environment: dev
├── CFN Bucket: dev-cyngular-onboarding (centralized)
└── Regional Buckets: dev-cyngular-onboarding-{region}

Environment: stg
├── CFN Bucket: stg-cyngular-onboarding (centralized)
└── Regional Buckets: stg-cyngular-onboarding-{region}

Environment: prod
├── CFN Bucket: cyngular-onboarding (centralized)
└── Regional Buckets: cyngular-onboarding-{region}
```

## Jobs Overview

### Job 1: prepare-deployment
**Purpose**: Sets up deployment configuration and determines environment

**Steps**:
1. Checkout code
2. Determine environment from trigger context
3. Use `setup-deploy-config` composite action
4. Display deployment summary

**Outputs**:
- `s3_bucket_cfn`: Centralized S3 bucket for CloudFormation
- `bucket_pattern_regional`: Pattern for regional bucket discovery
- `aws_region`: Primary AWS region
- `python_version`: Python version for consistency
- `timestamp`: Deployment timestamp for versioning
- `environment`: Target environment

### Job 2: deploy-cfn-templates
**Purpose**: Deploy CloudFormation templates to centralized S3 bucket

**Conditions**: Runs only if `deploy_cfn != 'false'`

**Steps**:
1. Checkout code
2. Configure AWS credentials via OIDC
3. Use `deploy-cfn` composite action

**Features**:
- Supports YAML and JSON CloudFormation templates
- Dual deployment (timestamp + latest paths)
- Centralized deployment to single bucket per environment

### Job 3: deploy-lambda-functions
**Purpose**: Package and deploy Lambda functions to regional S3 buckets

**Conditions**: Runs only if `deploy_lambdas != 'false'`

**Strategy**: Matrix deployment for parallel processing
- Services: `Lambdas/Services`
- Cleaners: `Lambdas/Cleaners`

**Steps**:
1. Checkout code
2. Configure AWS credentials via OIDC
3. Use `deploy-lambdas` composite action

**Features**:
- Multi-region deployment with automatic bucket discovery
- ZIP packaging from nested directories
- Parallel processing of Services and Cleaners
- Dual deployment (timestamp + latest paths)

### Job 4: deploy-lambda-layer
**Purpose**: Build and deploy Lambda layer to regional S3 buckets

**Conditions**: Runs only if `deploy_lambdas != 'false'`

**Steps**:
1. Checkout code
2. Configure AWS credentials via OIDC
3. Use `deploy-layer` composite action

**Features**:
- Builds layer with dependencies from requirements.txt
- Includes custom modules from Layer/python/
- Multi-region deployment
- Dual deployment (timestamp + latest paths)

### Job 5: deployment-summary
**Purpose**: Generate comprehensive deployment report

**Conditions**: Always runs (even on failure)

**Features**:
- Job status summary with visual indicators
- Architecture improvements documentation
- Direct links to S3 console and workflow run
- Enhanced GitHub Actions summary page

## Composite Actions

### 1. setup-deploy-config

**Location**: `.github/actions/setup-deploy-config/action.yml`

**Purpose**: Centralizes deployment configuration logic

**Inputs**:
- `environment`: Target environment (default: 'dev')

**Outputs**:
- `s3_bucket_cfn`: Centralized S3 bucket for CFN
- `bucket_pattern_regional`: Regional bucket pattern
- `aws_region`: Primary AWS region
- `python_version`: Python version
- `timestamp`: Deployment timestamp

**Functionality**:
- Maps environment to appropriate S3 buckets
- Generates deployment timestamp
- Displays configuration summary

### 2. deploy-cfn

**Location**: `.github/actions/deploy-cfn/action.yml`

**Purpose**: Deploys CloudFormation templates to centralized S3 bucket

**Inputs**:
- `s3_bucket`: Target S3 bucket
- `timestamp`: Deployment timestamp
- `aws_region`: AWS region

**Functionality**:
- Installs uv for Python dependency management
- Uses enhanced s3_sync.py with dual deployment
- Supports YAML and JSON file patterns
- Provides deployment summary

**S3 Structure**:
```
s3://{bucket}/stacks/{timestamp}/
├── Core.yaml
├── Services.yaml
└── ...

s3://{bucket}/stacks/latest/
├── Core.yaml
├── Services.yaml
└── ...
```

### 3. deploy-lambdas

**Location**: `.github/actions/deploy-lambdas/action.yml`

**Purpose**: Packages and deploys Lambda functions to regional buckets

**Inputs**:
- `lambda_type`: Type of functions (services/cleaners)
- `lambda_path`: Path to Lambda directory
- `bucket_pattern`: Base bucket pattern for discovery
- `timestamp`: Deployment timestamp
- `aws_region`: Primary AWS region

**Functionality**:
- Discovers regional buckets automatically
- Creates ZIP files from nested directories
- Multi-region parallel deployment
- Dual path deployment

**S3 Structure**:
```
s3://{bucket-region}/lambdas/services/{timestamp}/
├── ServiceManager.zip
├── RegionProcessor.zip
└── ...

s3://{bucket-region}/lambdas/services/latest/
├── ServiceManager.zip
├── RegionProcessor.zip
└── ...
```

### 4. deploy-layer

**Location**: `.github/actions/deploy-layer/action.yml`

**Purpose**: Builds and deploys Lambda layer to regional buckets

**Inputs**:
- `bucket_pattern`: Base bucket pattern for discovery
- `timestamp`: Deployment timestamp
- `python_version`: Python version for building
- `aws_region`: Primary AWS region

**Functionality**:
- Sets up Python environment
- Builds layer with dependencies and custom modules
- Multi-region deployment using s3_sync.py
- Proper cleanup of build artifacts

**S3 Structure**:
```
s3://{bucket-region}/layers/{timestamp}/
└── cyngular-layer.zip

s3://{bucket-region}/layers/latest/
└── cyngular-layer.zip
```

## Enhanced S3 Sync Script

### Location
`.github/scripts/s3_sync.py`

### Key Features

#### Multi-Region Support
- **Bucket Discovery**: Automatically finds regional buckets based on naming patterns
- **Parallel Deployment**: Deploys to all discovered regions simultaneously
- **Regional Validation**: Validates each regional bucket before deployment

#### Dual Deployment
- **Timestamp Path**: Version-specific deployment for rollback capability
- **Latest Path**: Always-current deployment for easy reference
- **Configurable**: Can be enabled/disabled via command line flags

#### Enhanced Validation
- **Bucket Existence**: Validates bucket exists before attempting upload
- **Access Permissions**: Tests write permissions with small test object
- **Credential Validation**: Clear error messages for credential issues
- **404 Handling**: Specific messaging for non-existent buckets

### New Command Line Options
```bash
# Multi-region deployment
--multi-region              # Enable multi-region deployment
--bucket-pattern PATTERN    # Base pattern for bucket discovery

# Dual deployment
--dual-deployment           # Enable timestamp + latest deployment
--timestamp TIMESTAMP       # Specific timestamp for versioning

# Enhanced patterns
--pattern "*.{yaml,yml,json}" # Support multiple file extensions
```

### Usage Examples

```bash
# CloudFormation deployment (centralized)
S3_BUCKET=dev-cyngular-onboarding \
S3_PREFIX=stacks/20240101-120000 \
SOURCE_PATH=./CFN \
FILE_PATTERN="*.{yaml,yml,json}" \
DUAL_DEPLOYMENT=true \
TIMESTAMP=20240101-120000 \
uv run s3_sync.py

# Lambda deployment (multi-region)
BUCKET_PATTERN=dev-cyngular-onboarding \
S3_PREFIX=lambdas/services/20240101-120000 \
SOURCE_PATH=./Lambdas/Services \
SYNC_TYPE=zip \
MULTI_REGION=true \
DUAL_DEPLOYMENT=true \
TIMESTAMP=20240101-120000 \
uv run s3_sync.py
```

## Security & Permissions

### AWS Authentication
- **OIDC Integration**: Uses temporary credentials via role assumption
- **No Static Credentials**: No long-lived AWS keys stored in secrets
- **Scoped Sessions**: Each job has specific session names for audit trails

### Required IAM Permissions
The `AWS_DEPLOY_ROLE_ARN` secret must reference a role with:
- `s3:ListBucket` on all deployment buckets
- `s3:GetObject` and `s3:PutObject` on deployment bucket contents
- `s3:DeleteObject` for cleanup operations (bucket validation)

### Session Management
- **Unique Session Names**: Each job uses descriptive session names
- **Limited Duration**: 1-hour credential lifetime
- **Audit Trail**: CloudTrail logs all operations with session context

## Monitoring & Troubleshooting

### GitHub Actions Summary
- **Visual Status**: ✅/❌/⏭️ indicators for each component
- **Architecture Improvements**: Documentation of new features
- **Direct Links**: Quick access to S3 console and workflow details

### Common Issues

#### Bucket Discovery Failures
```
Error discovering regional buckets: Access denied
```
**Solution**: Ensure the deployment role has `s3:ListBucket` permissions globally

#### Multi-Region Deployment Failures
```
Failed to sync to eu-west-1: Bucket validation failed
```
**Solution**: Verify regional buckets exist and follow naming convention

#### Credential Issues
```
AWS credentials not found. Configure credentials using 'aws configure'
```
**Solution**: Check OIDC role configuration and GitHub secrets

### Debugging Tips

1. **Enable Debug Mode**: Add `ACTIONS_STEP_DEBUG=true` to repository secrets
2. **Check S3 Console**: Verify bucket structure matches expectations
3. **Review CloudTrail**: Check for permission issues in AWS logs
4. **Validate Bucket Names**: Ensure regional buckets follow pattern: `{base-pattern}-{region}`

## Migration Guide

### From Original Workflow

1. **Update Workflow File**: Switch from `deploy-to-s3.yml` to `deploy-to-s3-refactored.yml`
2. **Verify Secrets**: Ensure `AWS_DEPLOY_ROLE_ARN` secret is configured
3. **Create Regional Buckets**: Ensure buckets exist for all target regions
4. **Test Deployment**: Run workflow_dispatch with dev environment first

### Breaking Changes
- **Bucket Structure**: CFN templates now deploy to `stacks/` prefix instead of `cfn/`
- **Layer Deployment**: Now uses multi-region strategy instead of single region
- **File Patterns**: CloudFormation deployment now includes JSON files

### Rollback Strategy
- Keep original workflow file until refactored version is validated
- Use timestamp-based deployments for easy rollback to previous versions
- Regional deployments provide redundancy for disaster recovery

## Best Practices

### Development
1. **Test Locally**: Use `uv run s3_sync.py --dry-run` for testing
2. **Validate Templates**: Run cfn-lint before deployment
3. **Check Permissions**: Ensure IAM roles have minimal required permissions

### Operations  
1. **Monitor Deployments**: Check GitHub Actions summary for status
2. **Use Timestamps**: Reference specific deployment versions for troubleshooting
3. **Regular Cleanup**: Consider lifecycle policies for old timestamp deployments

### Security
1. **Rotate Credentials**: Regularly review and rotate OIDC role permissions
2. **Audit Access**: Monitor CloudTrail for deployment activities
3. **Least Privilege**: Ensure deployment role has minimal required permissions

## Support & Maintenance

### File Structure
```
.github/
├── actions/
│   ├── setup-deploy-config/action.yml
│   ├── deploy-cfn/action.yml
│   ├── deploy-lambdas/action.yml
│   └── deploy-layer/action.yml
├── scripts/
│   └── s3_sync.py
├── workflows/
│   └── deploy-to-s3-refactored.yml
└── WORKFLOW_DOCUMENTATION.md
```

### Maintenance Tasks
- **Regular Updates**: Keep composite actions and scripts updated
- **Dependency Management**: Monitor uv and Python version requirements
- **Security Reviews**: Periodically audit IAM permissions and OIDC configuration

### Contributing
1. **Test Changes**: Always test composite action changes with workflow_dispatch
2. **Document Updates**: Update this documentation for any architectural changes
3. **Validate Backwards Compatibility**: Ensure changes don't break existing deployments