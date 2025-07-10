#!/usr/bin/env bash
set -eu

source .env

####
install zip with templates to local dir:
curl -s https://raw.githubusercontent.com/Cyngular/Devops/main/Scripts/Gen3/zip.sh | bash
####
rain deploy ./CFN/Gen3/ReadonlyRole.yaml clipper-ro-role \
    --region ap-northeast-3 \
    --profile client_mgmt \
    --params "ClientName=$ClientName,CyngularAccountId=$CyngularAccountId"
####
rain deploy ./CFN/Gen3/Core.yaml clipper-core \
    --region ap-northeast-3 \
    --profile client_mgmt
