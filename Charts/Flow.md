
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
      * cyngular-lambda-admin-and-execution-roles actions
        * Create AdminAndExecutionRoles
      * Create ManagerLambdaRole & custom resource & trigger Lambda Manager
        * manager lambda actions
          * Invoke Lambda E
            * Update Cyngular Buckey policy with dynamic list of organization_accounts_ids
          * create_stack2 ()
            * Parameters
              * CyngularS3Bucket - created on client account
              * deployRegions (?)
            * Actions
              * create Stackset 2
                * Actions
                  * create gaurd duty lambda & role & trigger
                    * gaurd duty lambda actions
                      * if Guard Duty Detector exist - tag it
                      * if not create it
                  * create kms key & alias
                  * create r53 resolver query logs config
          * create_stackset child 1
            * run on all child accounts in one region
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
            * if not create it
          * create_stackset child 2
            * run on all child accounts in all regions
            * Parameters  
              * ClientRegions (?)
            * create_guardduty (detector or lambda already exist?)
          * Create Lambdas A - E
            * Lambda A - Create resources - run every 30 mins
              * dnslogs - associate every vpc to the cyngular resolver

# Off Boarding

0. Manualy Invoke deletion lambdas - in every account
     * VFL & Resources

0. Manualy delete Stacksets - in mgmgt account
     * Stack-2
     * StackSet-1 & StackSet-2
       * Delete Instances from stacksets
       * delete the stacksets

## TBD

* kms key for gaurd duty (or volume encrypt decrypt)
