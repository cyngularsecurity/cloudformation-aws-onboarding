
## Parameters

* ClientName
    - Description: The name of the client
    - Type: String
  
* ClientRegions
    - Description: The regions in which the client operate (use whitespace)
    - Type: String
  
* CyngularAccountId:
    - Description: The cyngular account id
    - Type: String
    - Default: 851565895544


## Resources

* Product S3Bucket
    - Type - S3: Bucket

* S3Bucket Policy
    - Type - S3: BucketPolicy
    - AWSCloudTrail AclCheck
        * Allow - to CloudTrail
            - S3: GetBucket Acl
        * on - Product S3Bucket.Arn
        * Condition
            SrcArn = arn:aws:cloudtrail: AWS::Region AWS::AccountId :trail/product-cloudtrail
    - AWSCloudTrail Write
        * Allow - to CloudTrail
            - S3: PutObject
        * on - Product S3Bucket.Arn /AWSLogs/ AWS::AccountId /*
        * Condition -
            - S3: x-amz-acl = bucket owner full control
            - SrcArn = arn:aws:cloudtrail: AWS::Region AWS::AccountId :trail/product-cloudtrail
    - AWSLogDeliveryWrite
        * Allow - to delivery logs
            - S3: PutObject
        * on - Product S3Bucket.Arn /*