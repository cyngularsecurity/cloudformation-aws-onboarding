# GitHub Actions Local Testing with Act CLI

This guide provides practical instructions for testing GitHub Actions workflows locally using [act CLI](https://github.com/nektos/act) for the Cyngular AWS client-onboarding project.

## Prerequisites

### 1. Install Act CLI
```bash
# macOS with Homebrew
brew install act

# Verify installation
act --version
```

### 2. Ensure Docker is Running
```bash
# Check Docker status
docker info

# Start Docker Desktop if needed
open -a Docker
```

### 3. Create Local Secrets File
Create `.secrets` file in project root for testing (**DO NOT commit this file**):

```bash
# Create .secrets file
cat > .secrets << 'EOF'
DEV_AWS_ACCOUNT_ID=123456789012
STG_AWS_ACCOUNT_ID=123456789012  
PROD_AWS_ACCOUNT_ID=123456789012
GITHUB_TOKEN=fake_token_for_testing
EOF
```

## Quick Start Commands

### List Available Workflows
```bash
# List all workflows and jobs
act --list

# Expected output shows our deploy-to-s3.yml jobs:
# - prepare-deployment
# - deploy-cfn-templates  
# - deploy-lambda-functions
# - deploy-lambda-layer
# - deployment-summary
```

### Test Deployment Configuration

#### Test Dev Environment (us-west-2)
```bash
act workflow_dispatch \
  -W .github/workflows/deploy-to-s3.yml \
  --container-architecture linux/amd64 \
  --job prepare-deployment \
  --input environment=dev \
  -P ubuntu-latest=node:16-buster-slim
```

**Expected Output:**
```
Environment: dev
CFN S3 Bucket: dev-cyngular-onboarding-templates
Regional Bucket Pattern: dev-cyngular-onboarding
AWS Region: us-west-2
```

#### Test Staging Environment (us-east-2)
```bash
act workflow_dispatch \
  -W .github/workflows/deploy-to-s3.yml \
  --container-architecture linux/amd64 \
  --job prepare-deployment \
  --input environment=stg \
  -P ubuntu-latest=node:16-buster-slim
```

**Expected Output:**
```
Environment: stg
CFN S3 Bucket: stg-cyngular-onboarding-templates  
Regional Bucket Pattern: stg-cyngular-onboarding
AWS Region: us-east-2
```

#### Test Production Environment (us-east-1)
```bash
act workflow_dispatch \
  -W .github/workflows/deploy-to-s3.yml \
  --container-architecture linux/amd64 \
  --job prepare-deployment \
  --input environment=prod \
  -P ubuntu-latest=node:16-buster-slim
```

**Expected Output:**
```
Environment: prod
CFN S3 Bucket: cyngular-onboarding-templates
Regional Bucket Pattern: cyngular-onboarding  
AWS Region: us-east-1
```

## Docker Image Options

Based on our testing, these images work well:

### Recommended: Node.js Slim Image (~200MB, Fast)
```bash
-P ubuntu-latest=node:16-buster-slim
```
- **Pros**: Fast download, sufficient for our bash scripts
- **Cons**: Limited tooling

### Medium: Act Ubuntu Image (~500MB)  
```bash
-P ubuntu-latest=catthehacker/ubuntu:act-latest
```
- **Pros**: More complete environment
- **Cons**: Larger download, slower startup

### Full: GitHub Runner Image (~17GB)
```bash
-P ubuntu-latest=catthehacker/ubuntu:full-latest
```
- **Pros**: Complete GitHub Actions environment
- **Cons**: Very large, slow download

## Validation Commands

### 1. Syntax Validation (Dry Run)
```bash
# Validate without execution
act workflow_dispatch \
  -W .github/workflows/deploy-to-s3.yml \
  --job prepare-deployment \
  --input environment=dev \
  --dryrun \
  -P ubuntu-latest=node:16-buster-slim
```

### 2. Environment-Specific Testing
```bash
# Test all three environments quickly
for env in dev stg prod; do
  echo "Testing $env environment..."
  act workflow_dispatch \
    --job prepare-deployment \
    --input environment=$env \
    --dryrun \
    -P ubuntu-latest=node:16-buster-slim
done
```

### 3. Test Specific Jobs
```bash
# Test CloudFormation deployment job
act workflow_dispatch \
  --job deploy-cfn-templates \
  --input environment=dev \
  --input deploy_cfn=true \
  --dryrun

# Test Lambda deployment job  
act workflow_dispatch \
  --job deploy-lambda-functions \
  --input environment=dev \
  --input deploy_lambdas=true \
  --dryrun
```

## Common Act CLI Options

| Option | Description | Example |
|--------|-------------|---------|
| `--dryrun` / `-n` | Validate syntax without execution | `--dryrun` |
| `--job` / `-j` | Run specific job | `--job prepare-deployment` |
| `--input` | Pass workflow inputs | `--input environment=dev` |
| `--list` / `-l` | List workflows and jobs | `--list` |
| `--verbose` / `-v` | Verbose output for debugging | `--verbose` |
| `-W` | Specify workflow file | `-W .github/workflows/deploy-to-s3.yml` |
| `-P` | Specify platform/image | `-P ubuntu-latest=node:16-buster-slim` |

## Testing Our Recent Fixes

### 1. Region Configuration Fix
Our fix ensures each environment uses the correct AWS region:

```bash
# Verify dev uses us-west-2
act workflow_dispatch --job prepare-deployment --input environment=dev --dryrun -P ubuntu-latest=node:16-buster-slim | grep "aws_region=us-west-2"

# Verify stg uses us-east-2  
act workflow_dispatch --job prepare-deployment --input environment=stg --dryrun -P ubuntu-latest=node:16-buster-slim | grep "aws_region=us-east-2"

# Verify prod uses us-east-1
act workflow_dispatch --job prepare-deployment --input environment=prod --dryrun -P ubuntu-latest=node:16-buster-slim | grep "aws_region=us-east-1"
```

### 2. Bucket Pattern Fix
Verify bucket patterns include correct prefixes:

```bash
# Dev should have 'dev-' prefix
act workflow_dispatch --job prepare-deployment --input environment=dev -P ubuntu-latest=node:16-buster-slim | grep "dev-cyngular-onboarding"

# Prod should have no prefix
act workflow_dispatch --job prepare-deployment --input environment=prod -P ubuntu-latest=node:16-buster-slim | grep "bucket_pattern_regional=cyngular-onboarding"
```

## Troubleshooting

### Issue: Interactive Docker Image Selection
**Problem**: Act prompts for Docker image selection
```
? Please choose the default image you want to use with act:
```
**Solution**: Always specify `-P ubuntu-latest=node:16-buster-slim` flag

### Issue: Docker Pull Timeout
**Problem**: Large images timeout during download
**Solution**: Use smaller Node.js image or add `--pull=false` after first run

### Issue: Command Fails with Docker Not Running
**Problem**: `Cannot connect to the Docker daemon`
**Solution**: Start Docker Desktop: `open -a Docker`

### Issue: Secrets Not Found
**Problem**: Workflow references missing secrets
**Solution**: Create `.secrets` file with dummy values (shown above)

## Advanced Usage

### Create Act Configuration File
Avoid repetitive flags by creating `~/.actrc`:

```bash
# Create global act config
cat > ~/.actrc << 'EOF'
-P ubuntu-latest=node:16-buster-slim
--container-architecture=linux/amd64
--secret-file=.secrets
EOF
```

### Test Matrix Jobs
```bash
# Test specific matrix combinations for Lambda deployment
act workflow_dispatch \
  --job deploy-lambda-functions \
  --matrix services \
  --input environment=dev \
  --dryrun
```

### Debug Workflow Issues
```bash
# Enable verbose output for debugging
act workflow_dispatch \
  --job prepare-deployment \
  --input environment=dev \
  --verbose \
  -P ubuntu-latest=node:16-buster-slim
```

## Integration with Development Workflow

### Before Committing Workflow Changes
```bash
# Quick validation of all environments
./scripts/validate-workflows.sh  # (create this script)

# Or manual validation:
for env in dev stg prod; do
  echo "Validating $env environment..."
  act workflow_dispatch \
    --job prepare-deployment \
    --input environment=$env \
    --dryrun \
    -P ubuntu-latest=node:16-buster-slim
done
```

### Testing New GitHub Actions Features
```bash
# Test composite actions
act workflow_dispatch --job prepare-deployment --input environment=dev --dryrun

# Test job dependencies
act workflow_dispatch --job deployment-summary --input environment=dev --dryrun

# Test environment-specific logic
act workflow_dispatch --job prepare-deployment --input environment=dev
act workflow_dispatch --job prepare-deployment --input environment=prod
```

## Performance Tips

1. **Use Node.js slim image** for fastest testing
2. **Use `--dryrun`** for syntax validation
3. **Create `.actrc`** to avoid repetitive flags
4. **Skip Docker pull** with `--pull=false` after first run
5. **Test specific jobs** rather than entire workflows

## Example Testing Script

Create `scripts/test-workflows.sh`:

```bash
#!/bin/bash
set -e

echo "🧪 Testing GitHub Actions workflows with act CLI..."

# Test each environment
for env in dev stg prod; do
    echo "Testing $env environment..."
    act workflow_dispatch \
        --job prepare-deployment \
        --input environment=$env \
        --dryrun \
        -P ubuntu-latest=node:16-buster-slim \
        --quiet
    echo "✅ $env environment passed"
done

echo "🎉 All workflow tests passed!"
```

Make it executable:
```bash
chmod +x scripts/test-workflows.sh
./scripts/test-workflows.sh
```

## Known Limitations

1. **AWS Operations**: Real AWS API calls will fail (expected for testing)
2. **Network Access**: Some external services may be blocked in containers
3. **GitHub API**: GitHub API calls with fake tokens will fail
4. **File System**: Container file system is isolated from host

## Next Steps

After validating workflows locally:

1. **Commit changes** knowing syntax is correct
2. **Push to feature branch** for full CI/CD testing  
3. **Monitor GitHub Actions** for real AWS integration
4. **Use act CLI** for rapid iteration during development

This approach dramatically speeds up GitHub Actions development by catching syntax errors and logic issues locally before pushing to the repository.