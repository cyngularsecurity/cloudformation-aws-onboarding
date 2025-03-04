import boto3
import time
import os
import cfnresponse
import logging
import botocore

def check_role_existence_in_child(account_id, role_name='AWSCloudFormationStackSetExecutionRole'):
    sts_client = boto3.client('sts')
    role_arn = f'arn:aws:iam::{account_id}:role/{role_name}'
    try:
        # Attempt to assume the role in the child account
        assumed_role = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName='CheckRoleSession'
        )
        
        # If assume_role is successful, the role exists and is assumable
        logging.info(f"Successfully assumed role '{role_name}' in account {account_id}.")
        return True

    except botocore.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDenied':
            # Role exists, but we can't assume it (which is expected)
            logging.info(f"Role '{role_name}' exists in account {account_id}, but cannot be assumed as expected.")
            return True
        elif error_code == 'NoSuchEntity':
            # Role doesn't exist
            logging.info(f"Role '{role_name}' does not exist in account {account_id}.")
            return False
        else:
            # Some other error occurred
            logging.info(f"Unexpected error checking role in account {account_id}: {e}")
            return False

def check_role_existence(role_name):
    iam_client = boto3.client('iam')
    try:
        iam_client.get_role(RoleName=role_name)
        logging.info(f"The IAM role '{role_name}' exists.")
        return True
    except Exception as e:
        logging.info(str(e))
        return False

def wait_for(stack_name):
    cfn_client = boto3.client('cloudformation')
    waiter = cfn_client.get_waiter('stack_create_complete')
    waiter.wait(StackName=stack_name)

def wait_for_stackset_creation(stackset_name, operation_id):
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
        logging.info('StackSet creation completed successfully.')
    else:
        logging.info('StackSet creation failed.')

def is_organization_account():
    try:
        org_client = boto3.client('organizations')
        root_response = org_client.list_roots()
        if 'Roots' in root_response and len(root_response['Roots']) > 0:
            return True, root_response['Roots'][0]['Id']
    except Exception as e:
        logging.info(f"Error checking organization status: {e}")
    return False, None

def create_executionrole_on_childs(management_account_id, root_ou_id, regions, url):
    try:
        cfn_client = boto3.client('cloudformation')
        cfn_client.create_stack_set(
            StackSetName='cyngular-execution-role-stackset',
            Description='Cyngular Deployments | Child Accounts, Regional scope',
            TemplateURL=url,
            # TemplateBody=EXECUTION_ROLE_TEMPLATE,
            AutoDeployment = {
                'Enabled': True,
                'RetainStacksOnAccountRemoval': False
            },
            PermissionModel = 'SERVICE_MANAGED',
            Capabilities = ['CAPABILITY_IAM',"CAPABILITY_NAMED_IAM"],
            Parameters = [
                { 
                    'ParameterKey': 'AdministratorAccountId',
                    'ParameterValue': management_account_id
                }
            ]
        )
        result = cfn_client.create_stack_instances(
                StackSetName = 'cyngular-execution-role-stackset',
                DeploymentTargets = {
                    "OrganizationalUnitIds": [root_ou_id]
                },
                Regions = [regions[0]],
                OperationPreferences = {
                    'RegionConcurrencyType': 'PARALLEL',
                    'FailureTolerancePercentage': 100,
                    'MaxConcurrentPercentage': 100,
                    'ConcurrencyMode': 'SOFT_FAILURE_TOLERANCE'
                }
            )
        wait_for_stackset_creation("cyngular-execution-role-stackset", result["OperationId"])
    except Exception as e:
        logging.info(f"Error creating execution-role on childs: {e}")

def create_management_execution_role(management_account_id):
    cfn_client = boto3.client('cloudformation')
    if not check_role_existence("AWSCloudFormationStackSetExecutionRole"):
        cfn_client.create_stack(
            StackName='cyngular-managment-execution-role',
            TemplateBody=EXECUTION_ROLE_TEMPLATE,
            Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
            Parameters = [
                {
                    'ParameterKey': 'AdministratorAccountId',
                    'ParameterValue': management_account_id
                }
            ]
        )
        wait_for("cyngular-managment-execution-role")

def create_management_admin_role(url):
    cfn_client = boto3.client('cloudformation')
    if not check_role_existence("AWSCloudFormationStackSetAdministrationRole"):
        cfn_client.create_stack(
            StackName='cyngular-managment-admin-role',
            # TemplateBody=ADMIN_ROLE_TEMPLATE,
            TemplateURL=url,
            Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM']
        )
        wait_for("cyngular-managment-admin-role")

def cyngular_function(event, context):
    try:
        logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.info('STARTING CYNGULAR\'S FUNCTION...')

        if event['RequestType'] == 'Create':        
            try:
                exec_stack_url = event['ResourceProperties']['EXEC_TEMPLATE_URL']
                admin_stack_url = event['ResourceProperties']['ADMIN_TEMPLATE_URL']

                mgmt_acc_id = boto3.client('sts').get_caller_identity()['Account']
                is_org, root_ou_id = is_organization_account()
                regions = list(set(os.getenv('CLIENT_REGIONS', '').split(',')))

                logger.info("CREATING ROLES ON MANAGEMENT ACCOUNT")
                create_management_execution_role(mgmt_acc_id)
                create_management_admin_role(admin_stack_url)

                if is_org:
                    # check_role_existence_in_child(mgmt_acc_id) ## check for all accounts
                    logger.info("CREATING ROLES ON CHILDS")
                    create_executionrole_on_childs(mgmt_acc_id, root_ou_id, regions, exec_stack_url)
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
