import time
import os
import logging

import boto3
import botocore
from botocore.exceptions import WaiterError

# https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-lambda-function-code-cfnresponsemodule.html#cfn-lambda-function-code-cfnresponsemodule-source-python
import cfnresponse

# Constants
# EXECUTION_ROLE_NAME = "AWSCloudFormationStackSetExecutionRole"
# ADMIN_ROLE_NAME = "AWSCloudFormationStackSetAdministrationRole"
ADMIN_ROLE_NAME = "CyngularCloudFormationStackSetAdministrationRole" #1
EXECUTION_ROLE_NAME = "CyngularCloudFormationStackSetExecutionRole" #2

ADMIN_ROLE_STACK_NAME = "cyngular-managment-admin-role" #1
EXECUTION_ROLE_STACK_NAME = "cyngular-managment-execution-role" #2
EXECUTION_ROLE_STACKSET_NAME = "cyngular-execution-role-stackset"

# def check_role_existence_in_child(account_id, role_name='AWSCloudFormationStackSetExecutionRole'):
#     sts_client = boto3.client('sts')
#     role_arn = f'arn:aws:iam::{account_id}:role/{role_name}'
#     try:
#         # Attempt to assume the role in the child account
#         assumed_role = sts_client.assume_role(
#             RoleArn=role_arn,
#             RoleSessionName='CheckRoleSession'
#         )
        
#         # If assume_role is successful, the role exists and is assumable
#         logging.info(f"Successfully assumed role '{role_name}' in account {account_id}.")
#         return True

#     except botocore.exceptions.ClientError as e:
#         error_code = e.response['Error']['Code']
#         if error_code == 'AccessDenied':
#             # Role exists, but we can't assume it (which is expected)
#             logging.info(f"Role '{role_name}' exists in account {account_id}, but cannot be assumed as expected.")
#             return True
#         elif error_code == 'NoSuchEntity':
#             # Role doesn't exist
#             logging.info(f"Role '{role_name}' does not exist in account {account_id}.")
#             return False
#         else:
#             # Some otheaq1 error occurred
#             logging.info(f"Unexpected error checking role in account {account_id}: {e}")
#             return False

def check_role_existence(role_name):
    """Check if an IAM role exists."""
    iam_client = boto3.client('iam')
    try:
        iam_client.get_role(RoleName=role_name)
        logging.info(f"The IAM role '{role_name}' exists.")
        return True
    except iam_client.exceptions.NoSuchEntityException:
        logging.info(f"The IAM role '{role_name}' does not exist.")
        return False
    except Exception as e:
        raise Exception(f"Unexpected error occurred while checking IAM role '{role_name}': {e}")

def wait_for_stack(stack_name):
    try:
        cfn_client = boto3.client('cloudformation')
        try:
            waiter = cfn_client.get_waiter('stack_create_complete')
            waiter.wait(StackName=stack_name)
        except WaiterError as e:
            print(f"Waiter error: {e}")

    except Exception as e:
        raise Exception(f"Unexpected error occurred while waiting for stack '{stack_name}': {e}")

def wait_for_ss_operation(stackset_name, operation_id):
    try:
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
    except Exception as e:
        raise Exception(f"Unexpected error occurred while waiting for stackset '{stackset_name}' operation: {e}")

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
            # logging.error("Known Error: Access denied when calling ListRoots. This account is part of an organization but not the management account.")
            raise Exception("AccessDeniedException: Account is part of an organization but not the management account.")

        logging.error(f"Unexpected ClientError occurred: {e}")
        raise
    except Exception as e:
        raise Exception(f"Unexpected error checking organization status: {e}")

def create_execution_role_on_members(management_account_id, root_ou_id, regions, url):
    try:
        cfn_client = boto3.client('cloudformation')
        cfn_client.create_stack_set(
            StackSetName=EXECUTION_ROLE_STACKSET_NAME,
            Description='Cyngular Deployments | Member Accounts, Regional scope',
            TemplateURL=url,
            AutoDeployment = {
                'Enabled': True,
                'RetainStacksOnAccountRemoval': False
            },
            PermissionModel = 'SERVICE_MANAGED',
            Capabilities = ['CAPABILITY_IAM',"CAPABILITY_NAMED_IAM"],

            AdministrationRoleARN = f'arn:aws:iam::{management_account_id}:role/{ADMIN_ROLE_NAME}',
            ExecutionRoleName=EXECUTION_ROLE_NAME,

            Parameters = [
                { 
                    'ParameterKey': 'AdministratorAccountId',
                    'ParameterValue': management_account_id
                }
            ]
        )
        result = cfn_client.create_stack_instances(
                StackSetName = EXECUTION_ROLE_STACKSET_NAME,
                DeploymentTargets = {
                    "OrganizationalUnitIds": [root_ou_id]
                },
                Regions = [regions[0]],
                OperationPreferences = {
                    'RegionConcurrencyType': 'PARALLEL',
                    'FailureTolerancePercentage': 90,
                    'MaxConcurrentPercentage': 100,
                    'ConcurrencyMode': 'SOFT_FAILURE_TOLERANCE'
                }
            )
        wait_for_ss_operation(EXECUTION_ROLE_STACKSET_NAME, result["OperationId"])
    except Exception as e:
        logging.error(f"Error creating execution-role on members: {e}")

def create_role_stack(stack_name, template_url, role_name, parameters=None):
    try:
        if not check_role_existence(role_name):
            stackset_params = [
                {'ParameterKey': key, 'ParameterValue': value}
                for key, value in (parameters or {}).items()
            ]
            cfn_client = boto3.client('cloudformation')
            cfn_client.create_stack(
                StackName=stack_name,
                TemplateURL=template_url,
                Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
                EnableTerminationProtection=True,
                DisableRollback=True,
                Parameters=stackset_params
                # Parameters = [
                #     {
                #         'ParameterKey': 'AdministratorAccountId',
                #         'ParameterValue': management_account_id
                #     }
                # ]
            )
            wait_for_stack(stack_name)
    except Exception as e:
        logging.error(f"Error creating role stack {stack_name}: {e}")
        raise

# def create_management_admin_role(url):
#     cfn_client = boto3.client('cloudformation')
#     if not check_role_existence(ADMIN_ROLE_NAME):
#         cfn_client.create_stack(
#             StackName=ADMIN_ROLE_STACK_NAME,
#             TemplateURL=url,
#             Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
#             EnableTerminationProtection=True,
#             DisableRollback=True
#         )
#         wait_for_stack(ADMIN_ROLE_STACK_NAME)

def cyngular_function(event, context):
    try:
        logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.info('STARTING CYNGULAR\'S FUNCTION...')

        if event['RequestType'] == 'Create':        
            try:
                # admin_stack_url = event['ResourceProperties']['ADMIN_TEMPLATE_URL']
                # exec_stack_url = event['ResourceProperties']['EXEC_TEMPLATE_URL']
                admin_stack_url = os.environ['ADMIN_TEMPLATE_URL']
                exec_stack_url = os.environ['EXEC_TEMPLATE_URL']

                mgmt_acc_id = boto3.client('sts').get_caller_identity()['Account']
                is_org, root_ou_id = is_org_deployment()
                regions = list(set(os.environ['CLIENT_REGIONS'].split(',')))

                logger.info("CREATING ROLES ON MANAGEMENT ACCOUNT")
                exec_ss_parameters = {
                    'AdministratorAccountId': mgmt_acc_id
                }
                create_role_stack(EXECUTION_ROLE_STACK_NAME, exec_stack_url, EXECUTION_ROLE_NAME, exec_ss_parameters)
                create_role_stack(ADMIN_ROLE_STACK_NAME, admin_stack_url, ADMIN_ROLE_NAME)

                if is_org:
                    # check_role_existence_in_child(mgmt_acc_id) ## check for all accounts
                    logger.info("CREATING ROLES ON MEMBERS")
                    create_execution_role_on_members(mgmt_acc_id, root_ou_id, regions, exec_stack_url)

                logger.info("DONE WITH ALL CYNGULAR STACKS!")
                cfnresponse.send(event, context, cfnresponse.SUCCESS, {'msg' : '-- Done --'})

            except Exception as e:
                logger.critical(str(e))
                cfnresponse.send(event, context, cfnresponse.FAILED, {'msg' : str(e)})
        else:
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {'msg' : f"RequestType of event is not \'Create\', it is {event['RequestType']}"})
    except Exception as e:
        logger.critical(str(e))
        cfnresponse.send(event, context, cfnresponse.FAILED, {'msg' : str(e)})
