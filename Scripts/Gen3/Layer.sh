#!/usr/bin/env bash
set -eu

LAYER_NAME="aioboto3"

# Create necessary directories
mkdir -p layer/python zips

python3 -m venv .venv
source .venv/bin/activate

# Install packages from requirements.txt
pip install -r requirements.txt -t layer/python
# pip install --platform manylinux2014_x86_64 \
#   -r requirements.txt \
#   --target=layer/python \
#   --implementation cp --python-version 3.11 \
#   --only-binary=:all: --upgrade aioboto3

cd layer

zip -r ../zips/aioboto3.zip .
cd ..

deactivate

aws lambda publish-layer-version \
    --layer-name ${LAYER_NAME} \
    --description "A layer including the aioboto3 module" \
    --zip-file fileb://zips/aioboto3.zip \
    --compatible-runtimes python3.9 python3.10 python3.11 python3.12 python3.13 \
    --license-info "MIT"

rm -rf .venv layer zips

aws lambda add-layer-version-permission \
  --layer-name ${LAYER_NAME} \
  --version-number 1 \
  --statement-id public-access \
  --action lambda:GetLayerVersion \
  --principal "*"