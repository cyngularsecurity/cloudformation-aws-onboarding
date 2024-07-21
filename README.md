# Aws Client On Boarding


##LINK - 

https://eu-west-3.console.aws.amazon.com/cloudformation/home?region=eu-west-3#/stacks/create/review?templateURL=https://cyngular-onboarding-templates.s3.amazonaws.com/v3/stacks/CyngularOnBoarding.yaml&stackName=CyngularOnBoarding


<!-- ## Getting started
Send On Boarding cfn stacks to the client with necessary parameters, to create in their aws root account.
One Stack, to deploy another stack, and 2 StackSets

### Stack 1
* S3 Bucket & Policy for Cyngular.
* CloudTrail Trail for Cyngular.
* Cyngular Read Only IAM role{delete , modify, create snapshots, kms decryption}.

* Lambda A (B, C, D, E) role {r53, ec2, org, ssm, logs, eks, gd }, events, Cyngular s3 bucket
* Lambda A(create resources)
* Lambda B(create VFL)
* Event rule to invoke lambdaA, B
* lambda permission for events to invoke lambda A, B

* Lambda C(delete VFL)
* Lambda D(Delete resources)
* Lambda E(Update cyngular bucket)

* Manager Lambda role (cfn, lambda, logs, gd, iam, org, sts, s3)
* role for manager lambda to create Admin & execution roles in child accounts, if does'nt exists already, to run other stacks
* Manager Lambda -
  * create *stack-2* - including a stackset resource, when executed runs on all child acc -
    * KMS Key & Alias
    * R53 resolver QueryLoggingConfig
  * create *stack-set-1* targets all child acc and client regions -
    * Cyngular read only role
    * Lambda (A) role
    * Lambda A (create resources)
    * Lambda A scheduled rule & premission
* Manager lambda trigger {cr, stacks urls}
* Lambda Create Admin & Exec role

* Delete cr role
* Delete cr lambda

### Stack 2
* Stack set - deploy R53 resolver in every region of a client account.
* Kms key with cyngular access in key policy
* Kms alias

### Client Off boarding
1. run delete lambdas (del resources & del vpc flow logs) in all client accounts.
2. delete stack-1.
3. delete stacksets instances for all client accounts and regions. -->
