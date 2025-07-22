#!/usr/bin/env bash
set -eu

# Gen3 Lambda Layer Deployment Script
LAYER_NAME="cyngular-gen3-common"
LAYER_DIR="Lambdas/Gen3/Layer"
BUILD_DIR="build/layer"
ZIP_FILE="layer.zip"

echo "=== Deploying Cyngular Gen3 Lambda Layer ==="

if [[ ! -d "$LAYER_DIR" ]]; then
    echo "Error: Layer directory '$LAYER_DIR' not found. Run from project root."
    exit 1
fi

source .env

S3_BUCKET="cyngular-onboarding-${CURRENT_REGION}"

echo "Region: $CURRENT_REGION"
echo "S3 Bucket: $S3_BUCKET"

# Create S3 bucket if it doesn't exist
if ! aws s3 ls "s3://$S3_BUCKET" &> /dev/null; then
    echo "Creating S3 bucket: $S3_BUCKET"
    if [[ "$CURRENT_REGION" == "us-east-1" ]]; then
        aws s3 mb "s3://$S3_BUCKET"
    else
        aws s3 mb "s3://$S3_BUCKET" --region "$CURRENT_REGION"
    fi
fi

# Clean up previous builds
rm -rf "$BUILD_DIR" "$ZIP_FILE"

# Create build directory and copy layer content
mkdir -p "$BUILD_DIR"
cp -r "$LAYER_DIR/python" "$BUILD_DIR/"

# Install external dependencies if requirements exist
if [[ -f "$LAYER_DIR/requirements.txt" ]]; then
    echo "Installing external dependencies..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r "$LAYER_DIR/requirements.txt" -t "$BUILD_DIR/python" \
        --platform manylinux2014_x86_64 \
        --implementation cp \
        --python-version 3.11 \
        --only-binary=:all: \
        --upgrade
    deactivate
fi

# Create layer ZIP file
echo "Creating layer ZIP file..."
cd "$BUILD_DIR"
zip -r "../../$ZIP_FILE" . -q
cd - > /dev/null

# Upload to S3
S3_KEY="layers/$LAYER_NAME/$ZIP_FILE"
echo "Uploading to S3: s3://$S3_BUCKET/$S3_KEY"
aws s3 cp "$ZIP_FILE" "s3://$S3_BUCKET/$S3_KEY"

# Deploy CloudFormation stack
STACK_NAME="cyngular-gen3-layer"
CFN_TEMPLATE="CFN/Gen3/Layer.yaml"

if [[ -f "$CFN_TEMPLATE" ]]; then
    echo "Deploying CloudFormation stack..."
    if command -v rain &> /dev/null; then
        rain deploy "$CFN_TEMPLATE" "$STACK_NAME" -y --params "LayerName=$LAYER_NAME"
    else
        aws cloudformation deploy \
            --template-file "$CFN_TEMPLATE" \
            --stack-name "$STACK_NAME" \
            --parameter-overrides "LayerName=$LAYER_NAME" \
            --capabilities CAPABILITY_IAM
    fi
    
    # Get layer ARN from stack outputs
    LAYER_ARN=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query 'Stacks[0].Outputs[?OutputKey==`LayerArn`].OutputValue' \
        --output text)
else
    # Direct layer publication
    echo "Publishing layer version..."
    LAYER_RESULT=$(aws lambda publish-layer-version \
        --layer-name "$LAYER_NAME" \
        --description "Shared utilities for Cyngular Gen3 Lambda functions" \
        --content S3Bucket="$S3_BUCKET",S3Key="$S3_KEY" \
        --compatible-runtimes python3.9 python3.10 python3.11 python3.12 python3.13 \
        --compatible-architectures x86_64 arm64 \
        --license-info "MIT")
    
    LAYER_ARN=$(echo "$LAYER_RESULT" | jq -r '.LayerVersionArn')
fi

# Clean up
rm -rf "$BUILD_DIR" "$ZIP_FILE" .venv

echo "=== Deployment Complete ==="
echo "Layer ARN: $LAYER_ARN"
echo "Usage: from cyngular_common import MetricsCollector, cfnresponse"