

## Parameters

* ClientName:
    - Description: The name of the client. (must be lowercase, can contain letters, numbers and dashes)
    - Type: String


* CyngularAccountId:
    - Description: The cyngular account id
    - Type: String

* RootOUid:
    - Description: the root ou id
    - Type: String

* OrganizationId:
    - Description: the client organization id
    - Type: String

* ClientRegions:
    - Description: The regions in which the client operates (comma-separated for example; us-east-1,us-east-2)
    - Type: CommaDelimitedList

* Stack2URL:
    - Description: The link to the stack2 template url.
    - Type: String

* StackSet1URL:
    - Description: The link to the stackset1 template url.
    - Type: String

* StackSet2URL:
    - Description: The link to the stackset1 template url.
    - Type: String

## Resources


* S3:Bucket
    - Type - S3: Bucket

* S3:BucketPolicy
    - Type - S3: BucketPolicy
    - AWSCloudTrailAclCheck
        * Allow - to CloudTrail
            - S3: GetBucketAcl
            - on - ProductBucket.Arn
        * Condition 
            - Arn = CloudTrail:Region:AcountID:Trail/ProductTrailPath
    - AWSCloudTrailWrite (per Acc)
        * Allow - to CloudTrail
            - S3: PutObject
            - on ProductBucket.Arn/AWSLogs/AccountId/*
        * Condition
            - s3:x-amz-acl = "BucketOwnerFullControl"
            - AWS:SourceArn = CloudTrail:Region:AccountID:Trail/ProductTrailPath
    - AWSCloudTrailWrite 2 (per Oz)
        * Allow - to CloudTrail
            - S3: PutObject
            - on ProductBucket.Arn/AWSLogs/AccountId/*
        * Condition
            - s3:x-amz-acl = "BucketOwnerFullControl"
            - AWS:SourceArn = CloudTrail:Region:OzID:Trail/ProductTrailPath\

* ClientCloudTrail
    - Type - CloudTrail: Trail
    - S3Bucket - ProductS3Bucket

* ClientProductRole - ReadOnly
    - Type - IAM: Role
    - AssumeRole PolicyDocument
        * Allow - to AWS:IAM: ProductAccountID :root
            - sts: AssumeRole
    - EC2ProductSnapShot
        * Allow 
            - ec2: DeleteSnapsho
            - ec2: ModifySnapshotAtt
        * on - *
        * Condition
            - NameTag = Product*
    - EC2CreateSnapShot
        * Allow 
            - ec2: CopySnapshot
            - ec2: CreateSnapsho
            - ec2: CreateSnapshots
        * on - *

    - ReadOnly
        * Allow
            - kms:List*
            - kms:Describe*

            - ecr:Describe*
            - ecr:List*

            - iam:List*
            - iam:Get*
            
            - rds:List*
            - rds:Describe*

            - s3:List*
            - s3:Describe*
            - s3:GetBucketLocation

            - logs:List*
            - logs:Describe*
            - logs:Get*
            - logs:FilterLogEvents

            - eks:Describe*
            - eks:List*
            - ecs:List*

            - ec2:Li
            * ec2:CreateTags
            - ecs:Descri
            - ec2:Describe*
            
            - lambda:List*
            - lambda:Get*

            -  organizations:Describe*
            -  organizations:List*

            -  cloudformation:Describe*
            -  cloudformation:List*
            -  cloudformation:Get*

            - guardduty:List*
            - guardduty:Get*

            - ce:GetCostAndUsage
            - ce:GetDimensionValues

        * on - *

    - S3GetObject
        * Allow 
            - S3: GetObject
        * on -
            - S3:Product ClientName Bukcet AccountID
            - S3:Product ClientName Bukcet OzID

    - VolumeDecrypt
        * Allow 
            - kms: Decrypt
            - kms: CreateGrant
        * on - *

    * ProductKmsKey
        * Allow
            - kms: *
        * on - *
        * Condition
            - NameTag = Product*

* Lambda A Role
    - Type - IAM: Role
    - AssumeRolePolicyDocument
        * Allow - to Lambda
            * sts: AssumeRole

    - ProductLambdaPolicy
        - VisualEditor
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

                - eks:List*
                - eks:UpdateClusterConfig

                - guardduty:*

            * on - *
        - ProductEvent
            * Allow
                - Events: *
            * on - *
        - ProductBuckets
            * Allow
                - S3: *
            * on -
                - Product ClientName Bucket AccountID                
                - Product ClientName Bucket AccountID /*

### Lambda A
* ProductLambda A (Create Resources)
    - OS Internals
    - EKS Logs
    - DNS Logs

* Lambda A ScheduleRule
    * Type - Eventes: Rule
    * ScheduleExpression - (*/30 * * * ? *)
    * Target - ProductLambdaA

* PremisionsForEventsToInvokeLambda A
    * Type - Lambda: Permission
    * Action - Lambda: InvokeFunction
    * to - Events
    * Arn - LambdaScheduleRule

* ProductLambda B (Create VPC Flow Logs)

* Lambda B ScheduleRule
    * Type - Eventes: Rule
    * ScheduleExpression - (*/30 * * * ? *)
    * Target - ProductLambdaB

* PremisionsForEventsToInvokeLambda B
    * Type - Lambda: Permission
    * Action - Lambda: InvokeFunction
    * to - Events
    * Arn - Lambda A ScheduleRule

* ProductLambda C (Delete VPC Flow Logs)
    * Type - Lambda: Function

* ProductLambda D (Delete Resources)
    * Type - Lambda: Function
    - DNS Logs

* ProductLambda E (Update Product Bucket) (Adds Cloudtrail Bucket Permissions)
    * Type - Lambda: Function


<!-- ????? -->


* ManagerLambdaRole
    - Type - IAM: Role
    - AssumeRoleDocument
        * Allow - to Lambda
            * sts: AssumeRole
    - CloudFormationPolicy
        * Allow
            - "lambda:InvokeFunction"
            - "lambda:InvokeAsync"
            - "lambda:GetFunction"

            - "logs:*"

            - "cloudformation:CreateStack"
            - "cloudformation:GetTemplateSummary"
            - "cloudformation:CreateStackSet"
            - "cloudformation:DescribeStackSet"
            - "cloudformation:CreateStackInstances"
            - "cloudformation:DescribeStackSetOperation"
            - "cloudformation:DeleteStackInstances"
            - "cloudformation:ListStackSetOperationResults"
            - cloudformation:DescribeStacks"
            - "cloudformation:DeleteStackSet"

            - "guardduty:TagResource"
            - "guardduty:ListDetectors"
            - "guardduty:CreateDetector"

            - "organizations:ListAccounts"

            - "sts:GetCallerIdentity"

            - "s3:GetObject"

            - "iam:GetRole"
            - "iam:DeleteRolePolicy"
            - "iam:DetachRolePolicy"
            - "iam:AttachRolePolicy"
            - "iam:PutRolePolicy
            - "iam:getRolePolicy
            - "iam:CreateRole"

        * on - *
        
* Admin & Execution Role LambdaRole
    * Type - IAM: Role
    * AssumeRoleDocument
        * Allow - to Lambda
            * sts: AssumeRole
    * CloudFormationPolicy
        * Allow
            - cloudformation:DescribeStacks"
                  - "cloudformation:CreateStack"
                  - "cloudformation:CreateStackSet"
                  - "cloudformation:DescribeStackSet"
                  - "cloudformation:CreateStackInstances"
                  - "cloudformation:DescribeStackSetOperation"
                  - "cloudformation:DeleteStackInstances"
                  - "cloudformation:ListStackSetOperationResults"
                  - "cloudformation:UpdateStackSet"
                  - "cloudformation:UpdateStackInstances"
                  - "cloudformation:DeleteStackSet"
                  - "cloudformation:ListStackInstances"
                  - "cloudformation:DescribeStackEvents"
                  - "cloudformation:ExecuteChangeSet"
                  - "cloudformation:CreateChangSet"
                  - "organizations:ListAccounts"
                  - "s3:GetObject"
                  - "iam:GetRole"
                  - "logs:*
        * on - *

* ProductManagerLambda
    * Type - Lambda: Function

* ManagerLambdaTrigger
    * Type - CloudFormation: CustomResource

* Create Admin & Execution Roles Lambda
    * Type - Lambda: Function

* Create Admin & Execution Role
    * Type - CloudFormation: CustomResource

* DeleteCustomResourceLambda Role
    * Type - IAM: Role

* DeleteCustomResourceLambda
    * Type - Lambda: Function