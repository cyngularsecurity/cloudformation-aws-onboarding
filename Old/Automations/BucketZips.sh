#!/usr/bin/env bash


echo "[*] Creating Directories"
mkdir git
mkdir zips

echo "[*] Cloning Repositories"

cd git || echo "no dir git" && exit 1

git clone --branch=release/2.0 git@gitlab.com:cyngular-security/aws-cloud-service-lambda.git -q
git clone --branch=feature/yoav2 git@gitlab.com:cyngular-security/aws-linux-service-lambda.git -q
git clone --branch=release/1.0 git@gitlab.com:cyngular-security/aws-visibility-service-lambda.git -q
git clone --branch=release/1.6.0-lambda git@gitlab.com:cyngular-security/aws-sqs-rds-service-lambda.git -q
git clone --branch=release/1.6.1-lambda git@gitlab.com:cyngular-security/aws-logic-service.git -q

echo "[*] Creating Zips (recursive looping)"

for d in ./*/; do
  echo "[*] Directory: " "$d"
  cd "$d" || echo "no dir $d" && exit 1

  for d2 in *; do
    if [ -d "$d2" ]; then
    cd "$d2" || echo "no dir $d2" && exit 1; zip -r "../../../zips/$d2.zip" ./*; cd ..;
    fi
  done
  cd ..
done

echo "[*] Renaming (According to the code naming conventions)"

cd ..
cd zips || echo "no dir zips" && exit 1

mv lambdaA.zip LinuxService_Lambda_A.zip
mv lambdaB.zip LinuxService_Lambda_B.zip
mv DatabaseLambda.zip DatabaseService_Lambda.zip
mv DatabaseLambdaInit.zip DatabaseService_Lambda_Init.zip
mv visibility_lambda_a.zip VisibilityService_Lambda_A.zip
mv visibility_lambda_b.zip VisibilityService_Lambda_B.zip
