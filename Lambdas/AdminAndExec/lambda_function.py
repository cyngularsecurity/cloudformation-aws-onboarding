import boto3
import time
import os
import cfnresponse
import logging

def check_role_existence(role_name):
    iam_client = boto3.client('iam')
    try:
        iam_client.get_role(RoleName=role_name)
        print(f"IAM role '{role_name}' already exists.")
        return True
    except Exception as e:
        print(str(e))
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
        print(f"Error checking organization status: {e}")
    return False, None

def create_executionrole_on_childs(management_account_id, root_ou_id, regions, url):
    try:
        cfn_client = boto3.client('cloudformation')
        cfn_client.create_stack_set(
            StackSetName='cyngular-execution-role-stackset',
            Description='Cyngular Deployments | Child Accounts, Global scope',
            TemplateURL=url,
            # TemplateBody=EXECUTION_ROLE_TEMPLATE,
            AutoDeployment={
                'Enabled': True,
                'RetainStacksOnAccountRemoval': False
            },
            PermissionModel='SERVICE_MANAGED',
            Capabilities=['CAPABILITY_IAM',"CAPABILITY_NAMED_IAM"],
            Parameters=[
                { 
                    'ParameterKey': 'AdministratorAccountId',
                    'ParameterValue': management_account_id
                },
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
        print(f"Error creating execution-role on childs: {e}")

def create_management_execution_role(management_account_id):
    cfn_client = boto3.client('cloudformation')
    if not check_role_existence("AWSCloudFormationStackSetExecutionRole"):
        cfn_client.create_stack(
            StackName='cyngular-managment-execution-role',
            TemplateBody=EXECUTION_ROLE_TEMPLATE,
            Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
            Parameters=[
                {
                    'ParameterKey': 'AdministratorAccountId',
                    'ParameterValue': management_account_id
                },
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
