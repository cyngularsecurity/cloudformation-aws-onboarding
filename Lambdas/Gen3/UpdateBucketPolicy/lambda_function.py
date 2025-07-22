import boto3
import os
import logging
import json
import cfnresponse


def get_account_ids_lst(management_account_id):
    member_accounts = []
    try:
        org_client = boto3.client("organizations")
        paginator = org_client.get_paginator("list_accounts")

        for page in paginator.paginate():
            member_accounts.extend(
                account["Id"]
                for account in page["Accounts"]
                if account["Id"] != management_account_id
            )
    except Exception as e:
        logging.critical(
            "CyngularFunctions (ERROR) - while trying to get account ids for organization: "
            + str(e)
        )
    return member_accounts


def update_bucket(bucket_name, management_account_id, is_org):
    try:
        s3_client = boto3.client("s3")
        response = s3_client.get_bucket_policy(Bucket=bucket_name)

        account_ids_list = (
            get_account_ids_lst(management_account_id)
            if is_org
            else [management_account_id]
        )
        account_arns_list = []
        for account_id in account_ids_list:
            account_arns_list.append(f'"arn:aws:logs:*:{account_id}:*"')
        new_statement = """[
            {
                "Sid": "OrgLogDeliveryWrite",
                "Effect": "Allow",
                "Principal": {
                    "Service": "delivery.logs.amazonaws.com"
                },
                "Action": "s3:PutObject",
                "Resource": "$%BUCKET_ARN%$/*",
                "Condition": {
                    "ArnLike": {
                        "AWS:SourceArn": [$%ACCOUNT_ARNS_LIST%$]
                    }
                }
            },
            {
                "Sid": "OrgLogDeliveryAclCheck",
                "Effect": "Allow",
                "Principal": {
                    "Service": "delivery.logs.amazonaws.com"
                },
                "Action": [
                    "s3:GetBucketAcl",
                    "s3:ListBucket"
                ],
                "Resource": "$%BUCKET_ARN%$",
                "Condition": {
                    "ArnLike": {
                        "aws:SourceArn": [$%ACCOUNT_ARNS_LIST%$]
                    }
                }
            }
        ]
        """.replace("$%ACCOUNT_ARNS_LIST%$", ",".join(account_arns_list)).replace(
            "$%BUCKET_ARN%$", f"arn:aws:s3:::{bucket_name}"
        )
        new_statement_json = json.loads(new_statement)
        reponse_policy = json.loads(response["Policy"])
        statement_policy = reponse_policy["Statement"]
        statement_policy.extend(new_statement_json)
        new_policy = {}
        new_policy["Statement"] = statement_policy
        new_policy["Version"] = "2012-10-17"

        response = s3_client.put_bucket_policy(
            Bucket=bucket_name, Policy=json.dumps(new_policy)
        )
        logging.info(response)
    except Exception as e:
        logging.critical(str(e))


def lambda_handler(event, context):
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.info("STARTING CYNGULAR'S FUNCTION...")
    
    # Check if this is a CloudFormation custom resource event
    is_cfn_event = "RequestType" in event and "StackId" in event
    
    try:
        logger.info("UPDATING CYNGULAR BUCKET POLICY")
        is_org = os.environ["IS_ORG"]
        cyngular_bucket_name = os.environ["BUCKET_NAME"]
        mgmt_acc_id = boto3.client("sts").get_caller_identity()["Account"]

        update_bucket(cyngular_bucket_name, mgmt_acc_id, is_org)
        logger.info("DONE!")
        
        # Send success response to CloudFormation if needed
        if is_cfn_event:
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {
                "Message": "Bucket policy updated successfully"
            })

    except Exception as e:
        logger.critical(str(e))
        
        # Send failure response to CloudFormation if needed
        if is_cfn_event:
            cfnresponse.send(event, context, cfnresponse.FAILED, {
                "Message": f"Failed to update bucket policy: {str(e)}"
            })
