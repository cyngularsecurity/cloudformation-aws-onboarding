
# OnBoarding Workflow

0. Upload files to cyngular s3 bucket (trigger: user)
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
        * Create ManagerLambdaRole
      * Create custom resource & trigger Lambda Manager
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
          * create_stackset1
            * Parameters  
              * ClientRegions (?)
          * create_guardduty
            * if Guard Duty Detector exist - tag it
            * if not create it
          * create_stackset2
            * Parameters  
              * ClientRegions (?)
            * create_guardduty (detector or lambda already exist?)