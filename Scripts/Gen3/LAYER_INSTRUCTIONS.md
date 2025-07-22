# Cyngular Gen3 Lambda Layer Instructions

## Overview

The Cyngular Gen3 Lambda Layer provides shared utilities and dependencies for all Gen3 Lambda functions, reducing code duplication and ensuring consistency across the Lambda architecture.

## Layer Contents

### Shared Modules
- **`cyngular_common.metrics`**: Centralized CloudWatch metrics collection
- **`cyngular_common.cfnresponse`**: CloudFormation custom resource response handling

### External Dependencies  
- **aioboto3**: Async AWS SDK for Python
- **typing-extensions**: Enhanced typing support

## Deployment Process

### Prerequisites
- Python 3.9+ installed
- AWS CLI configured with appropriate permissions
- Rain CLI (optional, for enhanced CloudFormation experience)

### Step 1: Deploy the Layer

```bash
# From project root directory
./Scripts/Gen3/deploy-layer.sh
```

The script will:
1. Validate prerequisites
2. Create S3 bucket if needed (`cyngular-onboarding-{region}`)
3. Build layer with shared code and dependencies
4. Upload layer ZIP to S3
5. Deploy CloudFormation stack (`cyngular-gen3-layer`)
6. Output layer ARN for use in Lambda functions

### Step 2: Update Lambda Functions

#### Manual Update (CloudFormation)
Add the layer ARN to your Lambda function resources:

```yaml
Resources:
  MyLambdaFunction:
    Type: AWS::Lambda::Function
    Properties:
      # ... other properties
      Layers:
        - !ImportValue cyngular-gen3-layer-LayerArn
```

#### Manual Update (AWS CLI)
```bash
aws lambda update-function-configuration \
  --function-name YOUR_FUNCTION_NAME \
  --layers arn:aws:lambda:region:account:layer:cyngular-common:version
```

### Step 3: Update Lambda Code

Replace existing imports with layer imports:

**Before:**
```python
import cfnresponse
from metrics import MetricsCollector
```

**After:**
```python
from cyngular_common import cfnresponse
from cyngular_common.metrics import MetricsCollector
```

## File Structure

```
Lambdas/Gen3/Layer/
├── python/
│   └── cyngular_common/
│       ├── __init__.py
│       ├── cfnresponse.py
│       └── metrics.py
└── requirements.txt
```

## Usage Examples

### MetricsCollector Usage
```python
from cyngular_common.metrics import MetricsCollector

# Initialize metrics collector
metrics = MetricsCollector("client-name", "ServiceOrchestrator")

# Record invocation
metrics.record_invocation("CloudFormation")

# Record processing results
results = {
    "total_tasks": 10,
    "services_done": 8,
    "services_failed": 2,
    "success_rate": 0.8,
    "processing_time_seconds": 45.2
}
metrics.record_processing_results(results)

# Record custom metric
metrics.put_metric(
    namespace="Cyngular/Services",
    metric_name="CustomMetric",
    value=1,
    dimensions={"ServiceType": "DNS"}
)
```

### CloudFormation Response Usage
```python
from cyngular_common import cfnresponse

def lambda_handler(event, context):
    try:
        # Your processing logic here
        result = process_request(event)
        
        # Send success response
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {
            "Message": "Operation completed successfully",
            "Result": result
        })
        
    except Exception as e:
        # Send failure response  
        cfnresponse.send(event, context, cfnresponse.FAILED, {
            "Message": f"Operation failed: {str(e)}"
        })
```

## Deployment Script Flow

The `deploy-layer.sh` script follows this workflow:

1. **Prerequisites Check**
   - Verify Python 3 installation
   - Check AWS CLI and credentials
   - Validate layer directory exists

2. **S3 Bucket Setup**
   - Check if deployment bucket exists
   - Create bucket if needed (region-specific)

3. **Layer Build**
   - Clean previous builds
   - Copy shared Python modules
   - Install external dependencies via pip
   - Create optimized ZIP package

4. **Layer Deployment**
   - Upload ZIP to S3
   - Deploy CloudFormation stack
   - Retrieve layer ARN

5. **Cleanup**
   - Remove build artifacts
   - Clean up virtual environment

## Updating the Layer

To update the layer:

1. Modify files in `Lambdas/Gen3/Layer/`
2. Run `./Scripts/Gen3/deploy-layer.sh`
3. Update Lambda functions to use new layer version

## Troubleshooting

### Common Issues

**Script fails with "Layer directory not found"**
- Ensure you're running from the project root directory
- Verify `Lambdas/Gen3/Layer/` exists

**S3 permission errors**
- Check AWS credentials have S3 bucket creation/write permissions
- Verify region settings in AWS CLI

**Layer import errors in Lambda**
- Ensure layer is properly attached to Lambda function
- Verify import paths use `cyngular_common` prefix

**Dependencies not working**
- Check `requirements.txt` is in layer directory
- Verify pip install completed successfully

### Manual Verification

Check layer contents:
```bash
# Download and inspect layer
aws lambda get-layer-version \
  --layer-name cyngular-common \
  --version-number LATEST

# Test layer import locally
python3 -c "from cyngular_common.metrics import MetricsCollector; print('Success')"
```

## Integration with Gen3 Architecture

The layer integrates with the Gen3 Lambda architecture:

- **ServiceManager**: Uses metrics for orchestration tracking
- **RegionProcessor**: Uses metrics for service processing  
- **UpdateBucketPolicy**: Uses cfnresponse for CloudFormation integration
- **Future Lambdas**: Can leverage shared utilities immediately

This reduces deployment size, ensures consistency, and simplifies maintenance across all Gen3 Lambda functions.