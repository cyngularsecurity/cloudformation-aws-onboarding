import boto3
import time
import os
import logging
import json

# https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-lambda-function-code-cfnresponsemodule.html#cfn-lambda-function-code-cfnresponsemodule-source-python
import cfnresponse

EXECUTION_ROLE_NAME = "CyngularCloudFormationStackSetExecutionRole"
ADMIN_ROLE_NAME = "CyngularCloudFormationStackSetAdministrationRole"

MGMT_REGIONAL_STACKSET_NAME = 'cyngular-stackset-mgmt-regional'
MEMBERS_GLOBAL_STACKSET_NAME = 'cyngular-stackset-1'
MEMBERS_REGIONAL_STACKSET_NAME = 'cyngular-stackset-2'

def is_org_deployment():
    """Check if the account is part of an AWS organization."""
    try:
        is_org_env = os.environ['IsOrg']
        if is_org_env is None:
            raise EnvironmentError("Environment variable 'IsOrg' is not set.")
        if is_org_env.lower() == 'false':
            return False, "Not an organization account deployment, org id param is empty."

        org_client = boto3.client('organizations')
        root_response = org_client.list_roots()
        if 'Roots' in root_response and len(root_response['Roots']) > 0:
            return True, root_response['Roots'][0]['Id']
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'AccessDeniedException':
            logging.info("Known Error: Access denied when calling ListRoots. This account is part of an organization but not the management account.")
            raise ## TODO: validate return of a cfn response error
        logging.error(f"Unexpected ClientError occurred: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error checking organization status: {e}")
        raise

def wait_for_ss_operation(stackset_name, operation_id):
    cfn_client = boto3.client('cloudformation')
    response = cfn_client.describe_stack_set_operation(
        StackSetName=stackset_name,
        OperationId=operation_id
    )
    status = response['StackSetOperation']['Status']
    while status == 'RUNNING':
        time.sleep(10)
        response = cfn_client.describe_stack_set_operation(
            StackSetName=stackset_name,
            OperationId=operation_id
        )
        status = response['StackSetOperation']['Status']
    if status == 'SUCCEEDED':
        logging.info('StackSet operation completed successfully.')
    else:
        logging.info('StackSet operation failed.')

def create_mgmt_regional_stackset(management_account_id, regions, url):
    try:
        cfn_client = boto3.client('cloudformation')
        cfn_client.create_stack_set(
            StackSetName = MGMT_REGIONAL_STACKSET_NAME,
            Description = 'Cyngular Deployments | MGMT Account, Regional scope',
            TemplateURL = url,
            PermissionModel = 'SELF_MANAGED',
            Capabilities = ['CAPABILITY_IAM','CAPABILITY_NAMED_IAM'],
            AdministrationRoleARN = f'arn:aws:iam::{management_account_id}:role/{ADMIN_ROLE_NAME}',
            ExecutionRoleName=EXECUTION_ROLE_NAME,
            Parameters = [
                {
                    'ParameterKey': 'CyngularAccountId',
                    'ParameterValue': os.environ['CyngularAccountId']
                },
                {
                    'ParameterKey': 'S3BucketArn',
                    'ParameterValue': os.environ['S3BucketArn']
                },
                {
                    'ParameterKey': 'EnableDNS',
                    'ParameterValue': os.environ['EnableDNS']
                }
            ],
            Tags = [
                {
                    'Key': 'Company',
                    'Value': os.environ['ClientName']
                },
                {
                    'Key': 'Vendor',
                    'Value': 'Cyngular Security'
                }
            ]
        )
        result = cfn_client.create_stack_instances(
            StackSetName = MGMT_REGIONAL_STACKSET_NAME,
            DeploymentTargets = {
                "Accounts": [management_account_id]
            },
            Regions = regions,
            OperationPreferences = {
                'RegionConcurrencyType': 'SEQUENTIAL', # to allow r53 realtime update to the bucket policy per region
                'FailureTolerancePercentage': 90,
                'MaxConcurrentPercentage': 100,
                'ConcurrencyMode': 'SOFT_FAILURE_TOLERANCE'
            }
        )
        wait_for_ss_operation(MGMT_REGIONAL_STACKSET_NAME, result["OperationId"])
    except Exception as e:
        logging.error(f"Error creating stackset {MGMT_REGIONAL_STACKSET_NAME}: {e}")

def create_members_global_stackset(deployment_targets, regions, main_region, url):
    try:
        cfn_client = boto3.client('cloudformation')
        cfn_client.create_stack_set(
            StackSetName = MEMBERS_GLOBAL_STACKSET_NAME,
            Description = 'Cyngular Deployments | Member Accounts, Global scope',
            TemplateURL = url,
            PermissionModel = 'SERVICE_MANAGED',
            Capabilities = ['CAPABILITY_IAM','CAPABILITY_NAMED_IAM'],
            AutoDeployment = {
                'Enabled': True,
                'RetainStacksOnAccountRemoval': False
            },
            ManagedExecution = {
                'Active': True
            },
            Parameters = [
                {
                    'ParameterKey': 'ClientName',
                    'ParameterValue': os.environ['ClientName']
                },
                {
                    'ParameterKey': 'CyngularAccountId',
                    'ParameterValue': os.environ['CyngularAccountId']
                },
                {
                    'ParameterKey': 'S3BucketArn',
                    'ParameterValue': os.environ['S3BucketArn']
                },
                # {
                #     'ParameterKey': 'BucketPolicyLambdaArn',
                #     'ParameterValue': os.environ['BucketPolicyLambdaArn']
                # },
                {
                    'ParameterKey': 'ClientRegions',
                    'ParameterValue': ','.join(regions)
                },
                {
                    'ParameterKey': 'EnableDNS',
                    'ParameterValue': (os.environ['EnableDNS'])
                },
                {
                    'ParameterKey': 'EnableEKS',
                    'ParameterValue': (os.environ['EnableEKS'])
                },
                {
                    'ParameterKey': 'EnableVPCFlowLogs',
                    'ParameterValue': (os.environ['EnableVPCFlowLogs'])
                }
            ],
            Tags = [
                {
                    'Key': 'Company',
                    'Value': os.environ['ClientName']
                },
                {
                    'Key': 'Vendor',
                    'Value': 'Cyngular Security'
                }
            ]
        )
        result = cfn_client.create_stack_instances(
            StackSetName = MEMBERS_GLOBAL_STACKSET_NAME,
            DeploymentTargets = deployment_targets,
            Regions = [main_region],
            OperationPreferences = {
                'RegionConcurrencyType': 'PARALLEL',
                'FailureTolerancePercentage': 90,
                'MaxConcurrentPercentage': 100,
                'ConcurrencyMode': 'SOFT_FAILURE_TOLERANCE'
            }
        )
        wait_for_ss_operation(MEMBERS_GLOBAL_STACKSET_NAME, result["OperationId"])
    except Exception as e:
        logging.error(f"Error creating stackset {MEMBERS_GLOBAL_STACKSET_NAME}: {e}")

def create_members_regional_stackset(deployment_targets, regions, url):
    try:
        cfn_client = boto3.client('cloudformation')
        cfn_client.create_stack_set(
            StackSetName = MEMBERS_REGIONAL_STACKSET_NAME,
            Description = 'Cyngular Deployments | Member Accounts, Regional scope',
            TemplateURL = url,
            PermissionModel = 'SERVICE_MANAGED',
            Capabilities = ['CAPABILITY_IAM','CAPABILITY_NAMED_IAM'],
            AutoDeployment = {
                'Enabled': True,
                'RetainStacksOnAccountRemoval': False
            },
            ManagedExecution = {
                'Active': True
            },
            Parameters = [
                {
                    'ParameterKey': 'CyngularAccountId',
                    'ParameterValue': os.environ['CyngularAccountId']
                },
                {
                    'ParameterKey': 'S3BucketArn',
                    'ParameterValue': os.environ['S3BucketArn']
                },
                {
                    'ParameterKey': 'EnableDNS',
                    'ParameterValue': os.environ['EnableDNS']
                }
            ]
        )
        result = cfn_client.create_stack_instances(
            StackSetName = MEMBERS_REGIONAL_STACKSET_NAME,
            DeploymentTargets = deployment_targets,
            Regions = regions,
            OperationPreferences = {
                'RegionConcurrencyType': 'SEQUENTIAL',
                'FailureTolerancePercentage': 90,
                'MaxConcurrentPercentage': 100,
                'ConcurrencyMode': 'SOFT_FAILURE_TOLERANCE'
            }
        )
        wait_for_ss_operation(MEMBERS_REGIONAL_STACKSET_NAME, result["OperationId"])
    except Exception as e:
        logging.error(f"Error creating stackset {MEMBERS_REGIONAL_STACKSET_NAME}: {e}")

def invoke_lambda(func_name, is_org):
    try:
        lambda_client = boto3.client('lambda')
        payload = {
            "is_org": is_org
        }

        response = lambda_client.invoke(
            FunctionName = func_name,
            InvocationType = 'RequestResponse',
            # InvocationType='Event',  # async invocation

            Payload=json.dumps(payload),
            LogType = 'Tail'
        )

        # if response['StatusCode'] != 200:
            # logging.critical(f"Error in lambda {lambda_E_name} - {response}")
            # raise Exception(f"Error in lambda {lambda_E_name} - {response}")
        # payload = response['Payload'].read()
        # result = json.loads(payload)

        logging.info(f'Invoked Lambda {func_name}')
        if response['StatusCode'] != 200:
            logging.critical(f"Error in lambda {func_name} - {response}")
    except Exception as e:
        logging.critical(str(e))

def cyngular_function(event, context):
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.info('STARTING CYNGULAR\'S FUNCTION...')
    try:
        # if event['RequestType'] == 'Create' or event['RequestType'] == 'Update':
        if event['RequestType'] != 'Delete':
            try:                            
                management_account_id = boto3.client('sts').get_caller_identity()['Account']
                main_region = context.invoked_function_arn.split(':')[3]

                is_org, root_id = is_org_deployment()
                deployment_targets = {'OrganizationalUnitIds': [root_id]} if is_org else {'Accounts': [management_account_id]}
                regions = list(set(os.environ['ClientRegions'].split(',')))
                logger.info(f"deploy targets -> {deployment_targets}")
                logger.info(f"all regions -> {regions}")
                logger.info(f"main region -> {main_region}")

                # stack2_url = os.environ['Stack2URL']
                stackset1_url = os.environ['StackSet1URL']
                # stackset2_url = os.environ['StackSet2URL']
                lambda_E_name = os.environ['UpdateBucketPolicyLambdaName']

                logger.info("Updating Bucket Policy")
                invoke_lambda(lambda_E_name, is_org)
                time.sleep(60)

                # logger.info("STARING CYNGULAR STACK2")
                # create_mgmt_regional_stackset(management_account_id, regions, stack2_url)

                if is_org:
                    logger.info("STARING CYNGULAR STACKSET1")
                    create_members_global_stackset(deployment_targets, regions, main_region, stackset1_url)

                    # logger.info("STARING CYNGULAR STACKSET2")
                    # create_members_regional_stackset(deployment_targets, regions, stackset2_url)
                logger.info("DONE WITH ALL CYNGULAR STACKS!")
                cfnresponse.send(event, context, cfnresponse.SUCCESS, {'msg' : 'Done'})

            except Exception as e:
                logger.critical(str(e))
                cfnresponse.send(event, context, cfnresponse.FAILED, {'msg' : str(e)})
        else:
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {'msg' : 'No error'})
    except Exception as e:
        logger.critical(str(e))
        cfnresponse.send(event, context, cfnresponse.FAILED, {'msg' : str(e)})
