
## Parameters

* RegionName
    Description: underscore seperated region name (example- us_east_1)
    Type: String

* ClientName
    - Description: An environment name that is prefixed to resource names
    - Type: String

* BucketName
    - Description: The name of the bucket in which the lambda source files are located
    - Type: String

* ProductAccountId
    - Description: The account id of the Product account
    - Type: String

* LinuxServiceAmi
    - Description: The ami of the ec2 instance of the linux service
    - Type: String

* LinuxSecurityGroup
    - Description: linux service security group id
    - Type: AWS::EC2::SecurityGroup::Id

* PrivateSubnet1
    - Description: the id of the private subnet 1
    - Type: AWS::EC2::Subnet::Id

* PrivateSubnet2
    - Description: the id of the private subnet 2
    - Type: AWS::EC2::Subnet::Id

* Vpc
    - Description: the id of the region vpc
    - Type: AWS::EC2::VPC::Id

* SqsRdsSecurityGroup
    - Description: The id of the security group for the sqs rds lambda
    - Type: AWS::EC2::SecurityGroup::Id


 <!-- ------------------------------------------------------------------------ -->
## Resources:

### Secrets Manager

* SecretManager:
    - Type - SecretsManager: Secret
    - Description: Secret for Client

 <!-- ------------------------------------------------------------------------ -->
### SQS - Queues & Queue Policies

#### Cloud
* Product CloudService SQS
     - Type - SQS: Queue
     - Visibility TimeOut - 900 s (In which the message is unavailable for other subscribers, when recived from one already, waits for deleteion or other proccesing)
     - Delay Seconds - 0
     - ReceiveMassage WaitTimeSeconds - 0

* Product CloudService SQS Policy:
    - Type - SQS: QueuePolicy
    - Queues - Product CloudService SQS
        * Allow - to *
            - sqs: *
        * on - *

#### EKS
* Product EksService SQS
    - Type - SQS: Queue

* Product EksService SQS Policy
    - Type - SQS: QueuePolicy
    - Queues - Product EksService SQS
        * Allow - to *
            - sqs: *
        * on - *

#### Linux
* Product LinuxService SQS
    - Type - SQS: Queue

#### RDS
* Product RdsService SQS
    - Type - SQS: Queue

* Product RdsService SQS Policy:
    - Type - SQS: QueuePolicy
    - Queues - Product RdsService SQS
        * Allow - to *
            - sqs: *
        * on - *


 <!-- ------------------------------------------------------------------------ -->
### Dynamo DB Table
* Prosuct LinuxDynamoDB
    - Type - DynamoDB: Table


 <!-- ------------------------------------------------------------------------ -->
### Role ,Policy & Instance Profile for LinuxService

* LinuxService Role
    - Type - IAM: Role
    - AuumeRolePilicyDocument
        * Allow - to EC2
            sts: AssumeRole

 * LinuxService Policy
    - Type - IAM: ManagedPolicy
    - Role - LinuxService Role
    - VisualEditor0
        * Allow
            - ec2:DetachVolume
            - ec2:AttachVolume
            - ec2:CopySnapshot
            - ec2:DeleteSnapshot
            - ec2:List*
            - ec2:CreateVolume*
            - ec2:CreateTag*
            - ec2:DeleteVolume
            - ec2:Describe*

            - kms:Decrypt
            - kms:Describe*
            - kms:ReEncrypt*
            - kms:GenerateDataKey*
            - kms:Encrypt
            - kms:CreateGrant

            - iam:List*
            - iam:Get*
            - iam:PassRole

            - lambda:ListFunctions

            - eks:Describe*
            - eks:List*

            - ce:GetCostAndUsage
            - ce:GetDimensionValues
        * on - *

    - VisualEditor 5
        * Allow
            - EC2: TerminateInstance
            - on - *
        * Condition
            - TagClient = ClientName 
    
    - VisualEditor 1
        * Allow
            - SecretManager: GetSecretValue
        * on - !SecretManager
    
    - VisualEditor 2
        * Allow
            - sqs: *
        * on - *
        * Condition
            - TagClient = ClientName
    
    - VisualEditor 3 (?)
        * Allow 
            - sqs: *
        * on 
            - Product CloudServiceSqs.Arn
            - Product EksService Sqs.Arn
            - Product LinuxService Sqs.Arn
            - Product RdsService Sqs.Arn
    
    - VisualEditor 4 
        * Allow 
            - DynamoDB: *
        * on - Product LinuxDynamoDB

    - AllowPassRole (permission to enable critical privilege escalation) (to the Linux service to assign this role Arn)
        * Allow 
            - IAM: PassRole
        * on - arn:aws:iam:: Product AccountId :instance-profile/ Product - Role - ClientName

* Linux InstanceProfile:
    - Type - IAM: InstanceProfile
    - Path - "/"
    - Roles - LinuxService Role


 <!-- ------------------------------------------------------------------------ -->
#### Role & Policy for lambdas

* Product LambdaRole
    - Type - IAM: Role
    - AssumeRole PolicyDocument
        * Allow - to Lambda
            - sts: AssumeRole
    - ManagedPolicyArns
        - service-role/AWSLambda VPCAccessExecution Role
        - service-role/AWSLambda BasicExecution Role

* Product LambdaPolicy:
    - Type - IAM: ManagedPolicy
    - Roles - CProduct LambdaRole
    - VisualEditor0
        * Allow
            - iam:List*
            - iam:Get*
            - iam:AddRoleToInstanceProfile
 
            - kms:Decrypt
            - kms:Encrypt
            - kms:Describe*
            - kms:ReEncrypt*
            - kms:GenerateDataKey*
            - kms:CreateGrant

            - ec2:DescribeTags
            - ec2:DetachVolume
            - ec2:AttachVolume
            - ec2:CopySnapshot
            - ec2:DeleteSnapshot
            - ec2:CreateVolume
            - ec2:DeleteVolume
            - ec2:CreateTag*
            - ec2:List*
            - ec2:Describe*
            - ec2:RunInstances
            - ec2:ModifySnapshotAttribute
            - ec2:CreateSnapshot

            - logs:*

            - lambda:InvokeFunction
            - lambda:InvokeAsync
            - lambda:ListFunctions
        * on - *
    - VisualEditor 1
        * Allow
            - SecretManager: GetSecretValue
        * on - !SecretManager

    - VisualEditor 2
        * Allow
            - DymanoDB: *
        * on - Product LinuxDynamoDB.Arn
    
    - VisualEditor 3s
        * Allow
            - sqs: *
        * on - 
            - Product CloudService Sqs.Arn
            - Product EksService Sqs.Arn
            - Product LinuxService Sqs.Arn
            - Product RdsService Sqs.Arn

    - VisualEditor4 (?)
        * Allow
            - sts: AssumeRole
        * on - arn:aws:iam::*:role/Product-readonly-role- !ClientName
    
    - (?)
        * Allow
            - IAM: PassRole
        * on - LinuxService Role.Arn
        * Condition - IAM: PassedToService = ec2 (can perform Passrole action to pass a role only to ec2)


 <!-- ------------------------------------------------------------------------ -->
### Cloud Lambdas

#### Lambda A
* Product CloudService A LambdaFunction:
    - Type - Lambda: Function
    - Code 
        * S3Bucket - !BucketName
        * S3Key - Lambda/ CloudService_Lambda_A.zip
    - Role - !Product LambdaRole.Arn


* Cloud ScheduledRule
    - Type - Events: Rule
    - State: "ENABLED"

    - ScheduleExpression: "cron(0 * * * ? *)" (? - replaced with the cron daemon start-up time)
    - Targets
        * Arn: !Product CloudServiceALambdaFunction.Arn
        * Id: "TargetFunctionV1"

* Cloud PermissionForEvents ToInvokeLambda
    - Type - Lambda: Permission
        * Allow - to Events
            - lambda: InvokeFunction
        * SrcArn: !Cloud ScheduledRule.Arn

#### LAmbda B
* Product CloudService B LambdaFunction
    - Type - Lambda: Function
    - Code 
        * S3Bucket - !BucketName
        * S3Key - Lambda/ CloudService_Lambda_B.zip
    - Role - !Product LambdaRole.Arn

#### Lambda C
* Product CloudService C LambdaFunction
    - Type - Lambda: Function
    - Code 
        * S3Bucket - !BucketName
        * S3Key - Lambda/ CloudService_Lambda_C.zip
    - Role - !Product LambdaRole.Arn

* Product Cloud LambdaFunction EventSourceMapping
    - Type - Lambda: EventSourceMapping
    - Enabled: true

    - EventSourceArn: !Product CloudService Sqs.Arn
    - FunctionName: !Product CloudService C LambdaFunction.Arn

    - BatchSize: 50 (maximum records in a batch that Lambda pulls from sqs queue and sends to the function)
    - MaximumBatching WindowInSeconds: 60 (maximum time, in seconds, Lambda spends gathering records before invoking the function)
    

 <!-- ------------------------------------------------------------------------ -->
### EKS Lambdas

#### Lambda A
* Product EksService A LambdaFunction
    - Type - Lambda: Function
    -  Code 
        * S3Bucket - !BucketName
        * S3Key - Lambda/ CloudService_EKSLogs_Lambda_A.zip
    - Role - !Product LambdaRole.Arn

* Eks ScheduledRule:
    - Type - Events: Rule
    - State: "ENABLED"

    - ScheduleExpression: "cron(0 * * * ? *)"
    - Targets:
        * Arn: !Product EksServiceALambdaFunction.Arn
        * Id: "TargetFunctionV1"

* Eks PermissionForEvents ToInvokeLambda:
    - Type - Lambda: Permission
    - FunctionName: !Product EksServiceALambdaFunction.Arn
        * Allow - to Events
            - lambda:InvokeFunction
        * SrcArn: !Eks ScheduledRule.Arn

#### Lambda B
* Product EksService B LambdaFunction
    - Type - Lambda: Function
    -  Code 
        * S3Bucket - !BucketName
        * S3Key - Lambda/ CloudService_EKSLogs_Lambda_B.zip
    - Role - !Product LambdaRole.Arn

    
#### Lambda C
* Product EksService C LambdaFunction
    - Type - Lambda: Function
    -  Code 
        * S3Bucket - !BucketName
        * S3Key - Lambda/ CloudService_EKSLogs_Lambda_C.zip
    - Role - !Product LambdaRole.Arn

* Product Eks LambdaFunction EventSourceMapping
    - Type - Lambda: EventSourceMapping
    - Enabled: true

    - EventSourceArn: !Product EksService Sqs.Arn 
    - FunctionName: !Product EksService C LambdaFunction.Arn 

    - BatchSize: 50 
    - MaximumBatching WindowInSeconds: 60 
    
 <!-- ------------------------------------------------------------------------ -->
#### Linux Lambdas

#### Lambda A
* Product LinuxService A LambdaFunction
    - Type - Lambda: Function
    -  Code 
        * S3Bucket - !BucketName
        * S3Key - Lambda/ LinuxService_Lambda_B.zip
    - Role - !Product LambdaRole.Arn

* LinuxScheduledRule
    - Type - Events: Rule
    - State: "ENABLED"

    - ScheduleExpression: "cron(0 * * * ? *)"
    - Targets:
        * Arn: !Product LinuxService A LambdaFunction.Arn
        * Id: "TargetFunctionV1"

* Linux PermissionForEvents ToInvokeLambda:
    - Type - Lambda: Permission
    - FunctionName: !Product LinuxService A LambdaFunction.Arn
        * Allow - to Events
            - lambda:InvokeFunction
        * SrcArn: !Linux ScheduledRule.Arn

#### Lambda B
* Product LinuxService B LambdaFunction
    - Type - Lambda: Function
    -  Code 
        * S3Bucket - !BucketName
        * S3Key - Lambda/ LinuxService_Lambda_B.zip
    - Role - !Product LambdaRole.Arn


 <!-- ------------------------------------------------------------------------ -->
### Visibility Lambdas

#### Lambda A
* Product VisibilityService A LambdaFunction
    - Type - Lambda: Function
    -  Code 
        * S3Bucket - !BucketName
        * S3Key - Lambda/ VisibilityService_Lambda_A.zip
    - Role - !Product LambdaRole.Arn

* Visibility ScheduledRule
    - Type - Events: Rule
    - State: "ENABLED"

    - ScheduleExpression: "cron(0 */6 * * ? *)" 
    - Targets:
        * Arn: !Product VisibilityServic A LambdaFunction.Arn
        * Id: "TargetFunctionV1"

* Linux PermissionForEvents ToInvokeLambda:
    - Type - Lambda: Permission
    - FunctionName: !Product VisibilityService A LambdaFunction.Arn
        * Allow - to Events
            - lambda: InvokeFunction
        * SrcArn: !Visibility ScheduledRule.Arn

#### Lambda B
* Product VisibilityService B LambdaFunction
    - Type - Lambda: Function
    -  Code 
        * S3Bucket - !BucketName
        * S3Key - Lambda/ VisibilityService_Lambda_B.zip
    - Role - !Product LambdaRole.Arn


 <!-- ------------------------------------------------------------------------ -->
### DB Lambdas

#### init Lambda

* DatabaseInit Service LambdaFunction
    - Type - Lambda: Function
    -  Code 
        * S3Bucket - !BucketName
        * S3Key - Lambda/ DatabaseService_Lambda_Init.zip
    - Role - !Product LambdaRole.Arn

    - VpcConfig
        * SecurityGroupIds
          - SqsRds SecurityGroup
        * SubnetIds
          - PrivateSubnet1
          - PrivateSubnet2

#### Main Lambda
* Product DatabaseService LambdaFunction
    - Type - Lambda: Function
    -  Code 
        * S3Bucket - !BucketName
        * S3Key - Lambda/ DatabaseService_Lambda.zip
    - Role - !Product LambdaRole.Arn

    - VpcConfig
        * SecurityGroupIds
          - SqsRds SecurityGroup
        * SubnetIds
          - PrivateSubnet1
          - PrivateSubnet2

* Product Database LambdaFunction EventSourceMapping
    - Type - Lambda: EventSourceMapping
    - Enabled: true

    - EventSourceArn: !Product RdsService Sqs.Arn 
    - FunctionName: !Product DatabaseService LambdaFunction.Arn 

    - BatchSize: 1000 
    - MaximumBatching WindowInSeconds: 60 
    

 <!-- ------------------------------------------------------------------------ -->
### Logic Lambdas

#### Lambda A
* Product LogicService A LambdaFunction
    - Type - Lambda: Function
    -  Code 
        * S3Bucket - !BucketName
        * S3Key - Lambda/ LogicService_Lambda_A.zip
    - Role - !Product LambdaRole.Arn

    - VpcConfig
        * SecurityGroupIds
          - SqsRds SecurityGroup
        * SubnetIds
          - PrivateSubnet1
          - PrivateSubnet2

* Logic ScheduledRule
    - Type - Events: Rule
    - State: "ENABLED"

    - ScheduleExpression: "cron(*/30 * * * ? *)" 
    - Targets:
        * Arn: !Product LogicServic A LambdaFunction.Arn
        * Id: "TargetFunctionV1"

* Logic PermissionForEvents ToInvokeLambda:
    - Type - Lambda: Permission
    - FunctionName: !Product LogicService A LambdaFunction.Arn
        * Allow - to Events
            - lambda: InvokeFunction
        * SrcArn: !Logic ScheduledRule.Arn

#### Lambda B
* Product LogicService B LambdaFunction
    - Type - Lambda: Function
    -  Code 
        * S3Bucket - !BucketName
        * S3Key - Lambda/ LogicService_Lambda_B.zip
    - Role - !Product LambdaRole.Arn

    - VpcConfig
        * SecurityGroupIds
          - SqsRds SecurityGroup
        * SubnetIds
          - PrivateSubnet1
          - PrivateSubnet2
