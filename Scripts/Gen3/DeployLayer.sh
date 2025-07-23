#!/usr/bin/env bash
set -eu

# Gen3 Lambda Layer Deployment Script
readonly LAYER_NAME="cyngular-onboarding"
readonly LAYER_DIR="Lambdas/Gen3/Layer"
readonly BUILD_DIR="build/layer"
readonly ZIP_FILE="python.zip"

echo "=== Deploying Cyngular OnBoarding Lambda Layer ==="

if [[ ! -d "$LAYER_DIR" ]]; then
    echo "Error: Layer directory '$LAYER_DIR' not found. Run from project root."
    exit 1
fi

source .env

readonly S3_BUCKET="cyngular-onboarding-${RUNTIME_REGION}"

echo "Region: $RUNTIME_REGION"
echo "S3 Bucket: $S3_BUCKET"

if ! aws s3 ls "s3://$S3_BUCKET" &> /dev/null; then
    echo "Error: S3 bucket: $S3_BUCKET not found. Run from project root."
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
zip -r9 "../../$ZIP_FILE" . -q
cd - > /dev/null

# Upload to S3
S3_KEY="layers/$LAYER_NAME/$ZIP_FILE"
echo "Uploading to S3: s3://$S3_BUCKET/$S3_KEY"
aws s3 cp "$ZIP_FILE" "s3://$S3_BUCKET/$S3_KEY"

# Clean up
rm -rf "$BUILD_DIR" "$ZIP_FILE" .venv

echo "=== Deployment Complete ==="