#!/usr/bin/env bash

set -eu
set -x

. .env.example

# --------------------------------

# # for script in other langs -
# go get golang.org/x/crypto/ssh
# pip install paramiko

# --------------------------------

# W="cyngular-frontend"
ssh_user="ubuntu"

declare -A servers

servers=(
    ["Bastion"]="$BASTION_EIP:keys/bastion.pem"
    ["LoadBalancer"]="$LOAD_BALANCER_PIP:keys/load-balancer.pem:Services/LoadBalancer/LoadBalancerConf.sh"
    ["API"]="$API_PIP:keys/api.pem:Services/Api/ApiConf.sh"
    ["Frontend"]="$FRONTEND_PIP:keys/frontend.pem:Services/Frontend/FrontendConf.sh"
    ["Backend"]="$BACKEND_PIP:keys/backend.pem:Services/Backend/BackendConf.sh"
)

bastion_info="${servers[Bastion]}"
IFS=':' read -ra bastion_parts <<< "$bastion_info"

bastion_ip="${bastion_parts[0]}"
bastion_key="${bastion_parts[1]}"


# # Frontend

# git clone \
#   --branch=dev-v3 git@gitlab.com:cyngular-frontend/cyngular-frontend.git "$W/"

# tar czvf "$W.tar.gz" "$W/"
ssh-add "$bastion_key"

# ssh-add -L # (LIST)
# # ssh-add -D # (DELETE) [“too many authentication failures”]

# frontend_info="${servers["Frontend"]}"
# IFS=':' read -ra frontend_parts <<< "$frontend_info"

# frontend_ip="${frontend_parts[0]}"
# frontend_key="${frontend_parts[1]}"

# scp -J "ubuntu@$bastion_ip" -i "$frontend_key" "$W.tar.gz" "ubuntu@$frontend_ip:$W.tar.gz"

# # Backend

# # Git clone (use script)
# mkdir main
# cd main
# git clone git@gitlab.com:cyngular-backend/auth-service.git
# git clone git@gitlab.com:cyngular-backend/general-service.git
# git clone git@gitlab.com:cyngular-backend/incidents-service.git
# git clone git@gitlab.com:cyngular-backend/investigation-service.git
# git clone git@gitlab.com:cyngular-backend/overview-service.git
# git clone git@gitlab.com:cyngular-backend/settings-service.git
# git clone git@gitlab.com:cyngular-backend/visibilty-service.git
# cd ..
# tar -czvf backend_main.tar.gz main/


# backend_info="${servers["Backend"]}"
# IFS=':' read -ra backend_parts <<< "$backend_info"

# backend_ip="${backend_parts[0]}"
# backend_key="${backend_parts[1]}"
# # Upload to the server
# scp -J "ubuntu@$bastion_ip" -i "$backend_key" backend_main.tar.gz "ubuntu@$backend_ip:backend_main.tar.gz"


recur_script() {
  local server="$1"
  local ssh_user="$2"
  local server_ip="$3"
  local key_path="$4"
  local script_path="$5"
  local region="$6"

  ssh -J "$ssh_user@$bastion_ip" -i "$key_path" "$ssh_user@$server_ip" "bash -s" << EOF
    mkdir -p ~/logs/$server/
    echo "Running config script on $server service..." > ~/logs/$server/verify.log
    bash "$script_path $region"
    echo "Script execution on $server finished." >> ~/logs/$server/verify.log
EOF
}

# Convert the associative array keys to an indexed array and skip the first element (bastion)
server_names=("${!servers[@]}")
server_names=("${server_names[@]:1:${#server_names[@]}-1}")

for server in "${!server_names[@]}"; do
  server_info="${server_names[$server]}"
  IFS=':' read -ra parts <<< "$server_info"
    
  srv="${server_names[$server]}"
  server_ip="${parts[0]}"
  key_path="${parts[1]}"
  script_path="${parts[2]}"
  
  echo "Connecting to $server ($server_ip)..."
  
  config=$(recur_script "$srv" "$ssh_user" "$server_ip" "$key_path" "$script_path" "$REGION")

  if ! $config; then
    echo "Error executing script on $server"
  else
    echo "Successfuly finished execution on $server."
  fi
  echo "Disconnected from $server."
done

