#!/usr/bin/env bash

set -eu
set -x


echo -e "recursivly scripting; on Frontend server"

# # conf ssl crt also
# # P="cyngular/app"
# W="cyngular-frontend"

# AuthClientID=""
# AuthAppDomain=""
# AppBaseUrl="https://api.eu1.cyngular.io/api/v1/"

# CrtFile="" # /etc/ssl/cyngular/cyngular.crt
# KeyFile="" # aws-api-service-key-us-west-2.pem

# if [ -d "$W" ]; then
#     echo "Already exist: $W"
#     mv $W "${W}_old_$(date)"
# fi

# tar "xvf $W.tar.gz"
# rm "$W.tar.gz"


# # copy .env.example to .env
# cp .env.example .env

# -----------------------------------

# # declare -A replacements
# # replacements=(
# #   ["{{DB_HOST}}"]="db.example.com"
# #   ["{{DB_USER}}"]="username"
# #   ["{{DB_PASS}}"]="password"
# # )

# # Replace placeholders with actual values in .env
# sed -i "s/{{REACT_APP_CLIENT_ID}}/$AuthClientID/g; \
#   s/{{REACT_APP_DOMAIN}}/$AuthAppDomain/g; \
#   s/{{REACT_APP_BASE_URL}}/$AppBaseUrl/g; \
#   s/{{HTTPS}}/true/g; \
#   s/{{SSL_CRT_FILE}}/$CrtFile/g; \
#   s/{{SSL_KEY_FILE}}/$KeyFile/g" .env


# # # Replace placeholders with actual values in .env
# # for placeholder in "${!replacements[@]}"; do
# #     replacement="${replacements[$placeholder]}"
# #     sed -i "s/$placeholder/$replacement/g" .env
# # done

# -----------------------------------

# cd cyngular-frontend


# # killall nohup
# # killall npm
# killall node

# npm i
# nohup npm start &


# # Auth0
# # Configure CORS (4 different places)
# # Add:
# https://us1.cyngular.io:3000
# https://us1.cyngular.io:3000/overview?auth=1

