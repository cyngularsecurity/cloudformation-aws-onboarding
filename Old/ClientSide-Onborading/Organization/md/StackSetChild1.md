

## Properties

* ClientName
* ProductAccountID
* S3ClientArn
* ClientRegions


## Resources

* ClientProductRole
    * Type - IAM: Role
    * AssumeRolePolicyDocument
        * Allow - to IAM: ProductAccount :root
            * sts: AssumeRole
    * ProductReadOnlyPolicy
        * EC2ProductSnapshot
            * Allow
                * ec2: DeleteSnapShot
                * ec2: ModifySnapShotAttr
            * on - *
            * Condition 
                * NameTag = Product*
        * EC2CreateSnapShot
            * Allow
                * ec2: CopySnapshot
                * ec2: CreateSnapshot
                * ec2: CreateSnapshots
            * on - *
        * ReadOnly
            * Allow

* LambdaRole

* ProductLambda A

