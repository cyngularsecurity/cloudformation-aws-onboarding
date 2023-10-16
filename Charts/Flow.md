
# OnBoarding Workflow

0. Upload files to cyngular s3 bucket (trigger: user)
  * Sync files / changes to s3
    * Stack 2
    * Stackset child 1
    * Staclset child 2
0. Run Stack 1 on mgmt account (trigger: user)
    * Parameters
      * OrganizationId
      * RootOUid (?)
      * ClientName
      * CyngularAccountId (default)
      * ClientRegions (Comma Delimited List)
      * Stack2URL (default)
      * StackSet1URL (default)
      * StackSet2URL (default)
    * Actions
      * create cyngular S3 bucket, Part of bucket policy, cyngular readonly client role
      
      * Create lamda (A) role

      * Create Lambdas A-E, event rules For A & B
        * Lambda A - Create resources - run every 30 mins
          * dns logs - associate every vpc to the cyngular resolver
          * EKS logs
          * os internals

      * Create admin-and-execution-roles lambda & role custom resource & trigger
        * Create AdminAndExecutionRoles 
          * on mgmt account (Admin and Exec Stacks)
          * on child accounts (Exec stack as Stackset) 
          * both one region per account

      * Create ManagerLambda Lambda & Role & custom resource & trigger
        * manager lambda actions
          * Invoke Lambda E
            * Update Cyngular Buckey policy with dynamic list of organization_accounts_ids

          * create_stack2 ()
            * Parameters
              * CyngularS3Bucket - created on client account
              * deployRegions
            * Actions
              * create Stackset 2 
              * aplly to all regions in mgmt acc
                * Actions
                  * create r53 resolver query logs config
                  * create gaurd duty lambda & role & trigger
                    * gaurd duty lambda actions
                      * if Guard Duty Detector exist - tag it
                      * if not create it
                  * create kms key & alias

          * create_stackset child 1
            * aplly to all child accounts in one region
            * Parameters  
              * ClientName
              * CyngularAccountId
              * S3BucketArn
              * ClientRegions (accepts white spaces since is passed from lambda)
            * resources
              * cyngular read only role & lambdas role
              * Lamdas A - D
              * event schedules * permissions for lambda A & B
              * Custom Resource to trigger lambda B

          * create_guardduty
            * if Guard Duty Detector exist - tag it
            * if not create it, (enable, data from s3 Logs)

          * create_stackset child 2
            * run on all regions in child accounts 
            * Parameters  
              * ClientRegions (?)
            * create_guardduty detector, if exist - tag it
        * create delete-custom-resource lambda & role

## Catches
  * replacing CDLs With spaces
  * event rules for lambdas, creation and deletion in the lambda and in the template:
    * A - Enabled both, (D - Disabling)
    * B - In lambda Enabled, (C - Disabling)
  * cyngular S3 Buckets store only logs from cyngular CT trail 
  * Checking for exec & admin roles only in mgmt acc

  * kms key used in client 'tenant' deployment on cyngular side, with linux service & lambda, to encrypt * decrypt volumes, snapshots 