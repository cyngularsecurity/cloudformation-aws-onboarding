#!/usr/bin/env bash
set -eu

# Create necessary directories
mkdir -p layer/python zips

python3 -m venv .venv
source .venv/bin/activate

# Install packages from requirements.txt
pip install -r requirements.txt -t layer/python
cd layer

zip -r ../zips/aioboto3.zip .
cd ..

deactivate

aws lambda publish-layer-version \
    --layer-name aioboto3 \
    --description "A layer including the aioboto3 module" \
    --zip-file fileb://zips/aioboto3.zip \
    --compatible-runtimes python3.9 python3.10 python3.11 python3.12 python3.13

rm -rf .venv layer zips
