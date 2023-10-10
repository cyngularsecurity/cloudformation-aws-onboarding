#!/usr/bin/env bash

set -eu
set -x

echo -e "recursivly scripting; on API server"


# RRN="$1"
# PrKey="cyngular.key"

# Domain="api.aws.$RRN.cyngular.io"
# NgnixConfFile="/etc/nginx/nginx.conf"

# SslCert="$Domain.csr"

# # cd /etc/nginx/
# # vim nginx.conf
# # http { server { …. } }

# cd /etc/ssl/cyngular/
# mv private.key $PrKey

# # openssl req -new -key cyngular.key -out api.aws.RRN.cyngular.io.csr

# openssl req -new -key $PrKey -out "$Domain.csr"

# # openssl req -newkey rsa:2048 \
# #   -nodes -keyout $PrKey -out $SslCert \
# #   -subj "/C=IL/ST=TLV/L=Tel-Aviv/O=Cyngular Security Ltd/OU=Cyngular/CN=$Domain" # add email



# openssl x509 -signkey cyngular.key -in api.aws.us1.hotairballoon.one.csr -req -days 365 -out cyngular.crt

# # Country Name: IL
# # State: TLV
# # Location Name / City: Tel-Aviv
# # Organization Name: Cyngular Security Ltd
# # Organizational Unit Name: Cyngular
# # Common Name: Server_Name (api.aws.RRN.cyngular.io)
# # Email Address: info@cyngularsecurity.com

# # Download CSR file -> send to namecheap generation

# # /etc/ssl/cyngular/cyngular.crt


# # Complete
# # Server_name (based on route53-> Hosted Zoned - > domain)
# # Ssl_certificate
# # Ssl_certificate_key



# if [ ! -f "$NgnixConfFile" ]; then
#     echo "file not found: $NgnixConfFile"
#     exit 1
# fi

# sed -i "s/{{Server_name}}/$Domain/g; \
#     s/{{Ssl_certificate}}/$SslCert/g; \
#     s/{{Ssl_certificate_key}}/$PrKey/g" $NgnixConf && \
#     echo "Placeholders replaced in NGINX configuration file: $NgnixConf"

# # Restart NGINX

# systemctl status nginx

# systemctl restart nginx
# systemctl status nginx

