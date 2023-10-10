
## Parameters:

* RegionName:
    - underscore seperated single region name (example- us_east_1)
    - Type: String

* UbuntuLatestAmiID:
    - Retrives the latest ubuntu ami id of the current Region.
    - Default: "/aws/service/canonical/ubuntu/server/jammy/stable/current/amd64/hvm/ebs-gp2/ami-id"
    - Type: "AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>"

* VpcCIDR:
    - IP range for the VPC (CIDR notation)
    - Type: String

* PrivateSubnet1CIDR:
    - IP range (CIDR notation) for the VPC private Subnet 1.
    - Type: String

* PrivateSubnet2CIDR:
    - IP range (CIDR notation) for the VPC private Subnet 2.
    - Type: String

* PublicSubnet1CIDR:
    - IP range (CIDR notation) for the VPC public Subnet 1.
    - Type: String

* PublicSubnet2CIDR:
    - IP range (CIDR notation) for the VPC public Subnet 2.
    - Type: String

* DbPassword:
    - Master Password for the RDS. (min 8 characters)
    - Type: String


 <!-- ------------------------------------------------------------------------ -->
## Resources

* SecretManager - Specific for Client and region
    - Type - SecretsManager: Secret

* VPC
    - Type - Ec2: Vpc

* InternetGateway
    - Type - EC2: InternetGateway

* InternetGatewayAttachment
    - Type - EC2: VPCGatewayAttachment

* S3-VPC EndPoint
    - Type - EC2: VPCEndPoint
    - VPC - VPC
    - RouteTableIds
        * Private RouteTable 1
        * Private RouteTable 2


 <!-- ------------------------------------------------------------------------ -->
### Subnets
    
* PublicSubnet 1
    - Public RouteTable
    - Internet GateWay - To 0.0.0.0/0 (EveryWhere)

* PublicSubnet 2
    - Public RouteTable
    - Internet GateWay - To 0.0.0.0/0 (EveryWhere)

* PrivateSubnet 1
    - Private RouteTable 1
    - Nat GateWay 1 
        * From EIP1
        * To 0.0.0.0/0 (EveryWhere)

* PrivateSubnet 2
    - Pivate RouteTable 2
    - Nat GateWay 2 
        * From EIP2
        * To 0.0.0.0/0 (EveryWhere)
        

 <!-- ------------------------------------------------------------------------ -->
### IAM Premissions to Services

#### BackEnd Service
* Backebd ServiceRole
    - Type - IAM: Role
    - AssumeRolePolicyDocument
        * Allow - to EC2
            - sts: AssumeRole
    - ManagedPolicyArn
        * AmazonSSMManagedInstanceCore
        * AmazonSSMDirectoryServiceAccess
        * CloudWatchAgentServerPolicy

* LinuxServicePolicy
   - Type - IAM: ManagedPolicy
   - Role - BackendServiceRole
   - VisualEditor
       * Allow 
           - SecretManager: GetSecretValue
           - on - !SecretManager
   - AllowPassRole
       * Allow 
           - IAM: PassRole
           - on - BackendIntsnaceProfile.Arn

* BackendInstanceProfile
    - Type - InstanceProfile
        * Role - BackendServiceRole
        * Path - "/"

#### API Service
* ApiServiceRole
    - Type -  IAM: Role
    - AssumeRolePolicyDocument
        * Allow - to EC2
            - sts: AssumeRole
        * ManagedPolicyArns
            - AmazonSSMManagedInstanceCore
            - AmazonSSMDirectoryServiceAccess
            - CloudWatchAgentServerPolicy

* ApiServicePolicy
    * Type - IAM: ManagedPolicy
    * Role - APiServiceRole
    * AllowPassRole
        * Allow
            - IAM; PassRole
        * on - ApiInstanceProfile

* ApiInstanceProfile
    - Type - IAM: InstanceProfile
    - Path - "/"
    - Role - ApiServiceRole

#### FrontEnd Service
* FrontendServiceRole
    - Type - IAM: Role
    - AssumeRolePolicyDocument
        * Allow - to EC2
            - sts: AssumeRole
    - ManagedPolicyArns
        * AmazonSSMManagedInstanceCore
        * AmazonSSMDirectoryServiceAccess
        * CloudWatchAgentServerPolicy

* FrontendServicePolicy
    - Type - IAM: ManagedPolicy
    - Role - FrontendServiceRole
    - AllowPassRole
        * Allow
            - IAM: PassRole
        * on - FrontendInstanceProfile.Arn

* FrontendInstanceProfile
    * Type - IAM: InstanceProfile


 <!-- ------------------------------------------------------------------------ -->
#### Security Groups

* Linux SG
    - Type - EC2: SecurityGroup
    - Ingress
        * TCP - 22
            - SrcSG - Bastion SG

    - Egress
        * TCP - 0 to 65535
            - SrcCIDR - 0/0

* SQS-RDS SG
    - Type - EC2: SecurityGroup
    - Ingress
        * TCP - 0 to 65535
            - SrcCIDR - 0/0

    - Egress
        * TCP - 0 to 65535
            - SrcCIDR - 0/0

* API SG
    - Type - EC2: SecurityGroup
    - Ingress
        * TCP - 22
            - SrcSG - Bastion SG
        * TCP - 80
            - SrcCIDR - 0/0
        * TCP - 443
            - SrcCIDR - 0/0

    - Egress
        * TCP - 0 to 65535
            - SrcCIDR - 0/0

* Frontend SG
    - Type - EC2: SecurityGroup
    - Ingress
        * TCP - 22
            - SrcSG - Bastion SG
        * TCP - 80
            - SrcCIDR - 0/0
        * TCP - 443
            - SrcCIDR - 0/0

    - Egress
        * TCP - 0 to 65535
            - SrcCIDR - 0/0

* Backend SG
    - Type - EC2: SecurityGroup
    - Ingress
        * TCP - 22
            - SrcSG - Bastion SG
        * TCP - 8206
            - SrcSG - ApiSecurityGroup
        * TCP - 80 to 85
            - SrcSG - ApiSecurityGroup

    - Egress
        * TCP - 0 to 65535
            - SrcCIDR - 0/0

* Bastion SG
    - Type - EC2: SecurityGroup
    - Ingress
        * TCP - 22
            - SrcCIDR - 0/0 (Change to your own)

    - Egress
        * TCP - 0 to 65535
            - SrcCIDR - 0/0

* DB SG
    - Type - EC2: SecurityGroup
    - Ingress
        * TCP - 5432
            - SrcSg - Backend SG
            - SrcSg - SQS-RDS SG


    - Egress
        * TCP - 0 to 65535
            - SrcCIDR - 0/0
     

 <!-- ------------------------------------------------------------------------ -->
### Services: / Machines

#### Bastion

* KeyPair
    - Type - EC2: KeyPair
* Instance
    - Type - EC2: Instance
    - SubnetId - PublicSubnet 1
    - KeyName - Bastion KeyPair
    - BlockDeviceMappings:
        * EBS - /dev/sda1
            - VolumeSize: 30
            - VolumeType: gp2

    - SecurityGroupIds - BastionSecurityGroup
    - ImageId - UbuntuLatestAmiID
    - InstanceType - t2.micro

    - PrivateDnsNameOptions:
        * EnableResourceNameDnsARecord - true
        * HostnameType - ip-name

* EIP
    - Type - EC2: EIP

#### APi

* KeyPair
    - Type - EC2: KeyPair

* Instance 
    - Type - EC2: Instance

    - SubnetId - PublicSubnet 1
    - KeyName - API KeyPair
    - BlockDeviceMappings:
        * EBS - /dev/sda1
            - VolumeSize: 30
            - VolumeType: gp2

    - SecurityGroupIds - ApiSecurityGroup
    - ImageId - UbuntuLatestAmiID
    - InstanceType: t3.medium

    - PrivateDnsNameOptions:
        * EnableResourceNameDnsARecord - true
        * HostnameType - ip-name

    - IamInstanceProfile - ApiInstanceProfile

    - UserData:
        Fn::Base64: !Sub |
          <!-- #!/bin/bash
            sudo apt update
            sudo apt install nginx -y
            sudo ufw allow 'Nginx Full'
            mkdir /etc/ssl/Product
            cd /etc/ssl/Product
            openssl genrsa -out private.key 2048 -->

* EIP
    - Type - EC2: EIP


#### Frontend

* KeyPair
    - Type - EC2: KeyPair

* Instance 
    - Type - EC2: Instance
    - SubnetId - PublicSubnet 1
    - KeyName - Fontend KeyPair

    - BlockDeviceMappings:
        * EBS - /dev/sda1
            - VolumeSize: 30
            - VolumeType: gp2

    - SecurityGroupIds - FrontendSecurityGroup
    - ImageId - UbuntuLatestAmiID
    - InstanceType: t3.large

    - PrivateDnsNameOptions:
        * EnableResourceNameDnsARecord - true
        * HostnameType - ip-name

    - IamInstanceProfile - FrontendInstanceProfile

    - UserData:
        * Fn::Base64: !Sub |
            <!-- #!/bin/bash
            sudo apt update
            curl -sL https://deb.nodesource.com/setup_18.x | sudo -E bash -
            sudo apt install nodejs -y
            sudo apt install npm -y
            sudo npm cache clean -f
            sudo npm install -g n
            sudo n stable
            sudo n latest
            mkdir /etc/ssl/Product
            cd /etc/ssl/Product
            openssl genrsa -out private.key 2048 -->



#### Backend

* KeyPair
    - Type - EC2: KeyPair

* Instance 
    - Type - EC2: Instance
    - SubnetId - Parivate Subnet 1
    - KeyName - Backend KeyPair

    - BlockDeviceMappings:
        * EBS - /dev/sda1
            - VolumeSize: 30
            - VolumeType: gp2

    - SecurityGroupIds - BackendSecurityGroup
    - ImageId - UbuntuLatestAmiID
    - InstanceType: t3.large

    - PrivateDnsNameOptions:
        * EnableResourceNameDnsARecord - true
        * HostnameType - ip-name

    - IamInstanceProfile - BackendInstanceProfile

    - UserData:
        * Fn::Base64: !Sub |
            <!-- #!/bin/bash
            sudo apt update
            curl -sL https://deb.nodesource.com/setup_18.x | sudo -E bash -
            sudo apt install nodejs -y
            sudo apt install npm -y
            sudo npm cache clean -f
            sudo npm install -g n
            sudo n stable
            sudo n latest
            mkdir /etc/ssl/Product
            cd /etc/ssl/Product
            openssl genrsa -out private.key 2048 -->

#### RDS

* DBSubnetGroup
    - Type - RDS: DBSubnetGroup
    - SubnetIds
        * Private Subnet 1
        * Private Subnet 2

* RdsInstance
    - Type - RDS: DBInstance

    - Engine: postgres
    - DBInstanceClass: db.r6i.2xlarge

    - StorageType: gp2
    - AllocatedStorage: 100
    - MaxAllocatedStorage: 1000

    - MultiAZ: false
    - PubliclyAccessible: false
    - DBSubnetGroup - DB SubnetGroup

    - EnableIAMDatabaseAuthentication: true
 
    - BackupRetentionPeriod: 7
    - CopyTagsToSnapshot: true
    - StorageEncrypted: true
    - AutoMinorVersionUpgrade: true
    - DeletionProtection: false

    - MasterUserPassword - DbPassword
    - VPCSecurityGroups - DB SecurityGroup


 <!-- ------------------------------------------------------------------------ -->
### Lambdas

#### Lambda A

* LambdaRole
    - Type - IAM: Role
    - AssumeRolePolicyDocument
        * Allow - to Lambda
            - sts: AssumeRole
    - VisualEditor0
        * Allow
            - route53resolver:*

            - ec2:Describe*
            - ec2:CreateFlowLogs
            - ec2:CreateTags
            - ec2:DeleteFlowLogs
            - ec2:DeleteTags

            - organizations:ListAccounts

            - ssm:*
            - logs:*

        * on - *

* Product Lambda - Configure Resource (Nginx Configuration)
    - Type - Lambda: Function
    - Role - !LambdaRole

    

## Outputs

* Linux SG Output:
    - Description: The id of the linux security group
    - Value - Linux SG

* Private Subnet 1 Output:
    - Description: the id of the private subnet 1
    - Value - Private Subnet 1

* Private Subnet 2 Output:
    - Description: the id of the private subnet 2
    - Value - Private Subnet 2

* Vpc Output:
    - Description: The id of the region vpc
    - Value - Vpc

* SQS-RDS SG Output:
    - Description: The id of the security group for the sqs rds lambda
    - Value - SQS-RDS SG