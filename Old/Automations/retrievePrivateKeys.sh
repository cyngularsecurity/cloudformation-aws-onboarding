#!/bin/bash

keyPairName=""

while [ -z $keyPairName ];

    do
        echo "invalid key pair name!"
        echo -n "enter a valid name for the key pair:"

        read keyPairName

    done  

# fetch the ID of the key pair and set the variable to store it
keyPairID=$(aws ec2 describe-key-pairs \
    --filters Name=key-name,Values=$keyPairName \
    --query KeyPairs[*].KeyPairId \
    --output text)

# echo "keyPairID = $keyPairID"

if [ -z $keyPairID ]

    then

        echo ""
        # stop running the script if the key pair does not exist
        echo "the key pair with the name [$keyPairName] does not exist in aws systems manager parameter store."
        echo "please create a valid key pair with cloudformation or check the key pair name and try again!"

    else # continue running the script if the key pair exists

        fileName="private_key"

        # fetch the private key and store it in the .pem file
        aws ssm get-parameter \
            --name /ec2/keypair/$keyPairID \
            --with-decryption \
            --query Parameter.Value \
            --output text > $fileName.pem

        chmod 400 $fileName.pem

fi