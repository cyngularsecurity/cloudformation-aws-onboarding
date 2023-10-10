

## Parameters

* ClientName

* DeployRegions

* S3ManagmentBucketArn

* ProductAccountID


## Reasources

* StackSet
    - Type - CloudFormation: StackSet
    - DeploymentTarget
        * Account - !AWS: AccountID
        * Regions - !DefloyRegions
    - Template
        * Parameters
            - 4 Above
        * Resources
            * GaurdDutyLambdaRole
                - AssumeRolePolicyDocument
                    * Allow - to Lambda
                        - sts: AssumeRole
                - CloudFormationPolicy
                    * Allow
                        - logs:*"

                        - guardduty:TagResource
                        - guardduty:ListDetectors
                        - guardduty:CreateDetector
                        - guardduty:DeleteDetector
                        - guardduty:ListTagsForResource

                    * on - * 
            * Product GuardDuty CreationLambda
                - Type - Lambda: Function
            * GuardDuty CreationLambda Trigger
                - Type - CloudFormation: CustomResuorce
            * ProductKmsKey
                - Type - Kms: Key
                - KeyPolicy
                    * Enable IAM User Premissions
                        * Allow - to 
                            - IAM: ProductAccountID :root
                            - IAM: AccountID :root
                        * Action: Kms:*
                        * on - *
            * ProductKeyAlias
                - Type - Kms: Alias
                - Target - ProductKmsKey
            * ProductResolver
                - Type - R53Resolver: ResolverQueryLoggingConfig
                - Destination - S3Managment Bucket.Arn

