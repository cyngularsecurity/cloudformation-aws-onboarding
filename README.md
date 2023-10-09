# Aws Client On Boarding

## Getting started

Send On Boarding cfn stacks to the client with necessary parameters, to create in their aws root account.
One Stack, to deploy another stack, and 2 StackSets

### Stack 1

* S3 Bucket & Policy for Cyngular.
* CloudTrail Trail for Cyngular.
* Cyngular Read Only IAM role{} delete , modify, create snapshots, kms decryption.

* Lambda A (B, C, D, E) role {r53, ec2, org, ssm, logs, eks, gd }, events, Cyngular s3 bucket
* Lambda A(create resources)
* Lambda B(create VFL)
* Event rule to invoke lambdaA, B
* lambda permission for events to invoke lambda A, B

* Lambda C(delete VFL)
* Lambda D(Delete resources)
* Lambda E(Update singular bucket)

* Manager lambda role (cfn, lambda, logs, gd, iam, org, sts, s3)
* Admin & execution role for manager lambda, to run other stacks
* Manager Lambda - deploy 3 other templates
* Manager lambda trigger {cr, stacks urls}
* Lambda Create Admin & Exec role

* Delete cr role
* Delete cr lambda

### Stack 2

* Stack set - deploy R53 resolver & guard duty detector in every region of a client account.
* Guard duty lambda role, logs
* Create guard duty Lambda
* Guard duty lambda trigger cfn cr.
* (guard duty delete lambda)
* Kms key with cyngular access in key policy
* Kms alias

## TODO

1. use custom s3 bucket on client side to store stacks template files and lambdas code.
2. add ResolverQueryLoggingConfigAssociation type, stack 2, for detaching vpcs on stack deletion.
3. check for already existing resources and deletion options for:

* gaurd duty detector (lambda tags existing one with cyngular-guardduty, deletion lambda)
* osinternals (auditd), eks & dns logs (lambda for creating[A] and one for deletion[D - dnslogs only])
* vpc flow logs (lambda for creating[B] and one for deletion[C])
