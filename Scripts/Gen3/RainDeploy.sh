#!/usr/bin/env bash
set -eu

source .env

#### Install zip with templates to local dir:
curl -s https://raw.githubusercontent.com/Cyngular/Devops/main/Scripts/Gen3/zip.sh | bash
#### Install rain cli
# brew install rain

####
rain deploy ./CFN/Gen3/ReadonlyRole.yaml clipper-ro-role \
    --region ap-northeast-3 \
    --profile client_mgmt \
    --params "ClientName=$ClientName,CyngularAccountId=$CyngularAccountId"
####
rain deploy ./CFN/Gen3/Core.yaml clipper-core \
    --region ap-northeast-3 \
    --profile client_mgmt \
    --params "ClientName=$ClientName,CyngularAccountId=$CyngularAccountId,OrganizationId=$OrganizationId,CloudTrailBucket=$CloudTrailBucket,EnableDNS=$EnableDNS,EnableEKS=$EnableEKS,EnableVPCFlowLogs=$EnableVPCFlowLogs"

####
rain deploy ./CFN/Gen3/Services.yaml clipper-services \
    --region ap-northeast-3 \
    --profile client_mgmt \
    --params "ClientName=$ClientName,ServiceManagerOverride=$ServiceManagerOverride,EnableDNS=$EnableDNS,EnableEKS=$EnableEKS,EnableVPCFlowLogs=$EnableVPCFlowLogs"
####
