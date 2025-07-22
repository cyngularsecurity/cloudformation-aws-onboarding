import boto3
import json
import logging
from botocore.exceptions import ClientError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Initialize boto3 clients
org_client = boto3.client('organizations')
s3_client = boto3.client('s3')
sts_client = boto3.client('sts')
secrets_client = boto3.client('secretsmanager')

def assume_role(account_id, role_name):
    try:
        response = sts_client.assume_role(
            RoleArn=f'arn:aws:iam::{account_id}:role/{role_name}',
            RoleSessionName='AssumeRoleSession'
        )
        return response['Credentials']
    except ClientError as e:
        logger.error(f"Error assuming role for account {account_id}: {e}")
        return None

def get_account_ids():
    account_ids = []
    try:
        paginator = org_client.get_paginator('list_accounts')
        for page in paginator.paginate():
            for account in page['Accounts']:
                account_ids.append(account['Id'])
    except ClientError as e:
        logger.error(f"Error listing accounts: {e}")
    return account_ids

def list_s3_buckets(credentials):
    session = boto3.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )
    s3 = session.client('s3')
    try:
        response = s3.list_buckets()
        return [bucket['Name'] for bucket in response['Buckets']]
    except ClientError as e:
        logger.error(f"Error listing buckets: {e}")
        return []

def tag_s3_bucket(bucket_name, tags, credentials):
    session = boto3.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )
    s3 = session.client('s3')
    try:
        s3.put_bucket_tagging(
            Bucket=bucket_name,
            Tagging={'TagSet': tags}
        )
        logger.info(f"Successfully tagged bucket {bucket_name}")
    except ClientError as e:
        logger.error(f"Error tagging bucket {bucket_name}: {e}")

def list_buckets_by_tag(tag_key, tag_value, credentials):
    session = boto3.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )
    s3 = session.client('s3')
    bucket_names = []
    try:
        response = s3.list_buckets()
        for bucket in response['Buckets']:
            bucket_name = bucket['Name']
            try:
                tags = s3.get_bucket_tagging(Bucket=bucket_name)
                for tag in tags['TagSet']:
                    if tag['Key'] == tag_key and tag['Value'] == tag_value:
                        bucket_names.append(bucket_name)
                        break
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchTagSet':
                    continue
                logger.error(f"Error getting tags for bucket {bucket_name}: {e}")
    except ClientError as e:
        logger.error(f"Error listing buckets: {e}")
    return bucket_names

def store_in_secrets_manager(secret_name, secret_value):
    try:
        secrets_client.put_secret_value(
            SecretId=secret_name,
            SecretString=json.dumps(secret_value)
        )
        logger.info(f"Successfully stored secret {secret_name}")
    except ClientError as e:
        logger.error(f"Error storing secret {secret_name}: {e}")

def handler(event, context):
    role_name = 'OrganizationAccountAccessRole'
    tag_key = 'your-tag-key'
    tag_value = 'your-tag-value'
    secret_name = 'your-secret-name'

    account_ids = get_account_ids()
    all_bucket_names = []

    for account_id in account_ids:
        credentials = assume_role(account_id, role_name)
        if credentials:
            bucket_names = list_s3_buckets(credentials)
            all_bucket_names.extend(bucket_names)

            for bucket_name in bucket_names:
                tags = [{'Key': tag_key, 'Value': tag_value}]
                tag_s3_bucket(bucket_name, tags, credentials)

    store_in_secrets_manager(secret_name, all_bucket_names)

if __name__ == "__main__":
    handler(None, None)
