#!/usr/bin/env bash
set -eu

# Update Gen3 Lambdas to use the shared layer

LAMBDAS_DIR="Lambdas/Gen3"
BACKUP_DIR="build/lambda-backup-$(date +%Y%m%d-%H%M%S)"

echo "=== Updating Gen3 Lambdas for Layer Usage ==="

# Create backup
mkdir -p "$BACKUP_DIR"
cp -r "$LAMBDAS_DIR" "$BACKUP_DIR/"
echo "Backup created: $BACKUP_DIR"

# Update ServiceManager
echo "Updating ServiceManager..."
if [[ -f "$LAMBDAS_DIR/ServiceManager/lambda_function.py" ]]; then
    sed -i.bak 's/from metrics import MetricsCollector/from cyngular_common.metrics import MetricsCollector/g' \
        "$LAMBDAS_DIR/ServiceManager/lambda_function.py"
    sed -i.bak 's/import cfnresponse/from cyngular_common import cfnresponse/g' \
        "$LAMBDAS_DIR/ServiceManager/lambda_function.py"
    rm -f "$LAMBDAS_DIR/ServiceManager/metrics.py"
    rm -f "$LAMBDAS_DIR/ServiceManager/cfnresponse.py"
    rm -f "$LAMBDAS_DIR/ServiceManager/lambda_function.py.bak"
fi

# Update RegionProcessor
echo "Updating RegionProcessor..."
if [[ -f "$LAMBDAS_DIR/RegionProcessor/lambda_function.py" ]]; then
    sed -i.bak 's/from metrics import MetricsCollector/from cyngular_common.metrics import MetricsCollector/g' \
        "$LAMBDAS_DIR/RegionProcessor/lambda_function.py"
    rm -f "$LAMBDAS_DIR/RegionProcessor/metrics.py"
    rm -f "$LAMBDAS_DIR/RegionProcessor/lambda_function.py.bak"
fi

# Update UpdateBucketPolicy
echo "Updating UpdateBucketPolicy..."
if [[ -f "$LAMBDAS_DIR/UpdateBucketPolicy/lambda_function.py" ]]; then
    sed -i.bak 's/import cfnresponse/from cyngular_common import cfnresponse/g' \
        "$LAMBDAS_DIR/UpdateBucketPolicy/lambda_function.py"
    rm -f "$LAMBDAS_DIR/UpdateBucketPolicy/cfnresponse.py"
    rm -f "$LAMBDAS_DIR/UpdateBucketPolicy/lambda_function.py.bak"
fi

echo "=== Lambda Updates Complete ==="
echo "Remember to:"
echo "1. Deploy the layer: ./Scripts/Gen3/deploy-layer.sh"
echo "2. Update CloudFormation templates to include layer ARN"
echo "3. Redeploy Lambda functions"