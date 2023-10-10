
## New Site

* Run RegionDeployment
* Run CreateResources Lambda
* Update RDS Endpoint in Secret Manager

* Create A Records Pointing to EIPs: LB, AWS API, Azure
    - Load balancer - api.us1.hotairballoon.one
    - Api AWS - api.aws.us1.hotairballoon.one
    - Api Azure - api.azure.us1.hotairballoon.one

* Load Balancer Instance Already Included in updated regionDeployment.yaml CFN.
* retrieve intsnaces private keys from param store to ./keys

* Create S3 Bucket in site region and copy lambda/* from existing Lambdas bucket
    - to be done with script to git clone from lambdas repo, for latest version
    
* Configur nginx.conf on 
    - API Server        
    - Load Balancer Server
    <!-- * Domain - Server Name -->
    <!-- * SSL_CERT - /etc/ssl/cyngular/cyngular.crt -->
    * SSL_KEY - /etc/ssl/cyngular/cyngular.key


## New tenant

* copy cyngular made latest linux ami to deployment rgion
* deploy cloudfromation clintDeploy stack and fill params (also from region-init stack)

* Params:
BucketName	cyngular-lambda-code-us-west-1
ClientName	stark
CyngularAccountId	468159710337
LinuxSecurityGroup	sg-012f432d0014a3178
LinuxServiceAmi	ami-02a4fee1e6c3d92d9
PrivateSubnet1	subnet-077757d57972ad3da
PrivateSubnet2	subnet-06aad17f88c0ddf54
RegionName	us_west_1
SqsRdsSecurityGroup	sg-0fd2f42adef936eed
Vpc	vpc-0485041db913726b2
