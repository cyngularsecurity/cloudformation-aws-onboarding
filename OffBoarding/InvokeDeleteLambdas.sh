#!/usr/bin/env bash
set -eu

GREEN="\033[32m"
BLUE="\033[34m"
RESET="\033[0m"


aws lambda invoke --function-name testFunction \
  --cli-binary-format raw-in-base64-out \
  --payload '{"name": "John Smith"}' response.json
