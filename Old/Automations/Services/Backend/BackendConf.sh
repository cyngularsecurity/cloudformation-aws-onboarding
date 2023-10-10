#!/usr/bin/env bash

set -eu
set -x

echo -e "recursivly scripting; on Backend server"


# .env files
for dir in ./*/
do
  cd "${dir}"
  if [ -f .env.example ]; then
    cp .env.example .env
  fi
  cd ..
done

# # nv 
# # API_VERSION=1
# # CLOUD_NAME=aws/azure
# # NODE_ENV=production

# # # Auth
# # DOMAIN=
# # CLIENT_ID=
# # CLIENT_SECRET=

# # AUDIENCE=API -> Auth0 Management API -> API Identifier
# #  DB(Secret Manager)
# # DB_HOST=RDS Endpoint


# # npm i (each micro-service)
# for dir in ./*/
# do
#   cd "${dir}"
#   if [ -f package.json ]; then
#     npm i
#   fi
#   cd ..
# done


# # npm run build (each micro-service)
# for dir in ./*/
# do
#   cd "${dir}"
#   if [ -f package.json ]; then
#     echo "#### Running 'npm run build' in directory: ${dir}"
#     npm run build
#     if [ $? -eq 0 ]; then
#         echo "#### 'npm run build' successfully completed in ${dir}"
#     else
#         echo "#### 'npm run build' failed in ${dir}"
#     fi
#   else
#     echo "#### No package.json found in directory: ${dir}. Skipping..."
#   fi
#   cd ..
# done


# # nohup npm start & (each micro-service)
# for dir in ./*/
# do
#   cd "${dir}"
#   echo "#### Running 'nohup npm start &' in directory: ${dir}"
#   nohup npm start &
#   echo "#### 'nohup npm start &' command sent to background in ${dir}"
#   cd ..
# done


# # check the status of the services
# echo "Checking services status..."
# declare -A services=(
#   ["8206"]="auth-service"
#   ["80"]="overview-service"
#   ["81"]="incidents-service"
#   ["82"]="investigation-serivce"
#   ["83"]="visibility-service"
#   ["84"]="settings-service"
#   ["85"]="general-service"
# )

# for port in "${!services[@]}"
# do
#   echo "${port} - ${services[$port]}"
#   lsof -t -i:${port}
# done

# -------------------------

psql -h database-instance-us-west-1.cgsvxq53n8oc.us-west-1.rds.amazonaws.com -U postgres -d db_cyngular_prod_us_west_1
\dn - schemas
SET search_path = SCHEMANAME; 
\dt - tables
# ALTER TABLE users ADD COLUMN default_cloud_provider INTEGER DEFAULT 1 NOT NULL;

# UPDATE integrations
# SET fk_client_id = a82ff1ba-a8b7-429b-9106-8c61d254617d;

# INSERT INTO users (fk_client_id,user_id,user_name,full_name,email,picture,role_id,creation_time,last_seen,mfa,enable,live_timeline,default_cloud_provider) VALUES ('a82ff1ba-a8b7-429b-9106-8c61d254617d','auth0|64ef2f55086f90da14271d4e','tomer','Tomer Tourgeman','tomer@cyngularsecurity.com',6,1,NOW()::timestamp,NOW()::timestamp,1,1,1,1); 

#  fk_client_id  | character varying           |           | not null |  from Auth0
#  user_id       | character varying           |           | not null |  from Auth0
#  user_name     | character varying           |           | not null |  dvirg
#  full_name     | character varying           |           | not null |  dvir gross
#  email         | character varying           |           | not null |  dvirg@cyngularsecurity.com
#  picture       | character varying           |           | not null |  '0-6'
#  role_id       | integer                     |           | not null |  from roles table (1,2) (admin,)
#  creation_time | timestamp without time zone |           | not null |  current time function
#  last_seen     | timestamp without time zone |           | not null |  ""
#  mfa           | integer                     |           | not null |  1
#  enable        | integer                     |           | not null |  1
#  live_timeline | integer                     |           | not null |  1
#  default_cloud_provider | integer            |           | not null |  1 -->


# https://api.us1.hotairballoon.one/api/v1/aws/general/popup_notifications?cloud_name=aws

# api.us1.hotairballoon.one


# sudo tcpdump -i <interface> -A -s 0 'tcp port 80 and tcp[((tcp[12:1] & 0xf0) >> 2):4] = 0x47455420'

# COPY (SELECT * FROM your_table WHERE your_condition) TO '/path/to/your/output/file.csv' WITH CSV HEADER; 

# psql -h your_host -d your_database -U your_user -c "SELECT * FROM schema.table WHERE your_condition" -F',' -A -t > output.csv 

# In order to stop the service, run the following command:
# 	kill -9 `lsof -t -i:SERVICE_PORT`

# nano /tmp/cronfile
# crontab /tmp/cronfile
# crontab -l

# Investigation
# Enable Lambda - 


# INSERT INTO users (fk_client_id,user_id,user_name,full_name,email,picture,role_id,creation_time,last_seen,mfa,enable,live_timeline,default_cloud_provider) VALUES ('a82ff1ba-a8b7-429b-9106-8c61d254617d','auth0|64ff29722f447617693e836d','amir','Amir Skouri','amir@cyngularsecurity.com',3,1,NOW()::timestamp,NOW()::timestamp,1,1,1,1); 
# INSERT INTO users (fk_client_id,user_id,user_name,full_name,email,picture,role_id,creation_time,last_seen,mfa,enable,live_timeline,default_cloud_provider) VALUES ('a82ff1ba-a8b7-429b-9106-8c61d254617d','google-oauth2|115123162382542373778','itzik','Itzik Berrebi','itzik@cyngularsecurity.com',8,1,NOW()::timestamp,NOW()::timestamp,1,1,1,1); 