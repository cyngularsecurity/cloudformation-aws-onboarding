import boto3
import time
import os
import cfnresponse
import logging

def is_organization_account():
    try:
        org_client = boto3.client('organizations')
        root_response = org_client.list_roots()
        if 'Roots' in root_response and len(root_response['Roots']) > 0:
            return True, root_response['Roots'][0]['Id']
    except Exception as e:
        print(f"Error checking organization status: {e}")
    return False, None

def create_stack2(mgmt_acc_id, regions, url):
    cfn_client = boto3.client('cloudformation')
    cfn_client.create_stack_set(
        StackSetName='cyngular-stackset-mgmt-regional',
        Description='Cyngular Deployments | MGMT Account, Regional scope',
        TemplateURL=url,
        PermissionModel='SELF_MANAGED',
        Capabilities=['CAPABILITY_IAM','CAPABILITY_NAMED_IAM'],
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
    cfn_client.create_stack_instances(
        StackSetName = 'cyngular-stackset-mgmt-regional',
        DeploymentTargets = {
            "Accounts": [mgmt_acc_id]
        },
        Regions = regions,
        OperationPreferences = {
            'RegionConcurrencyType': 'PARALLEL',
            'FailureTolerancePercentage': 0,
            'MaxConcurrentPercentage': 100
        }
    )
def create_stackset1(deployment_targets, regions, url):
    cfn_client = boto3.client('cloudformation')
    cfn_client.create_stack_set(
        StackSetName='cyngular-stackset-1',
        Description='Cyngular Deployments | Child Accounts, Global scope',
        TemplateURL=url,
        PermissionModel='SERVICE_MANAGED',
        AutoDeployment={
            'Enabled': True,
            'RetainStacksOnAccountRemoval': False
        },
        ManagedExecution={
            'Active': True
        },
        Capabilities=['CAPABILITY_IAM','CAPABILITY_NAMED_IAM'],
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
        ]
    )
    cfn_client.create_stack_instances(
        StackSetName = 'cyngular-stackset-1',
        DeploymentTargets = deployment_targets,
        Regions = [regions[0]],
        OperationPreferences = {
            'RegionConcurrencyType': 'PARALLEL',
            'FailureTolerancePercentage': 0,
            'MaxConcurrentPercentage': 100
        }
    )
def create_stackset2(deployment_targets, regions, url):
    cfn_client = boto3.client('cloudformation')
    cfn_client.create_stack_set(
        StackSetName='cyngular-stackset-2',
        Description='Cyngular Deployments | Child Accounts, Regional scope',
        TemplateURL=url,
        PermissionModel='SERVICE_MANAGED',
        AutoDeployment={
            'Enabled': True,
            'RetainStacksOnAccountRemoval': False
        },
        Capabilities=['CAPABILITY_IAM','CAPABILITY_NAMED_IAM'],
        Parameters=[
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
    cfn_client.create_stack_instances(
        StackSetName = 'cyngular-stackset-2',
        DeploymentTargets = deployment_targets,
        Regions = regions,
        OperationPreferences = {
            'RegionConcurrencyType': 'PARALLEL',
            'FailureTolerancePercentage': 0,
            'MaxConcurrentPercentage': 100
        }
    )

def invoke_lambda(func_name):
    try:
        lambda_client = boto3.client('lambda')
        response = lambda_client.invoke(
            FunctionName = func_name,
            InvocationType = 'RequestResponse',
            LogType = 'Tail'
        )
        logging.info('lmbada E invoked!')
        if response['StatusCode'] != 200:
            logging.critical(f"Error {response}")
    except Exception as e:
        logging.critical(str(e))

def cyngular_function(event, context):
    try:
        logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logging.info('STARTING CYNGULAR\'S FUNCTION...')

        if event['RequestType'] == 'Create':
            try:                            
                mgmt_acc_id = boto3.client('sts').get_caller_identity()['Account']

                is_org, root_id = is_organization_account()
                deployment_targets = {'OrganizationalUnitIds': [root_id]} if is_org else {'Accounts': [mgmt_acc_id]}
                regions = list(set(os.getenv('ClientRegions', '').split(',')))
                logger.info(f"deploy targets -> {deployment_targets}")

                stack2_url = event['ResourceProperties']['Stack2URL']
                stackset1_url = event['ResourceProperties']['StackSet1URL']
                stackset2_url = event['ResourceProperties']['StackSet2URL']
                lambda_E_name = os.environ['UpdateBucketPolicyLambdaName']

                logging.info("Updating Bucket Policy")
                invoke_lambda(lambda_E_name)
                time.sleep(60)
                logging.info("STARING CYNGULAR STACK2")
                create_stack2(mgmt_acc_id, regions, stack2_url)

                if is_org:
                    logging.info("STARING CYNGULAR STACKSET1")
                    create_stackset1(deployment_targets, regions, stackset1_url)

                    logging.info("STARING CYNGULAR STACKSET2")
                    create_stackset2(deployment_targets, regions, stackset2_url)
                logging.info("DONE WITH ALL CYNGULAR STACKS!")
                cfnresponse.send(event, context, cfnresponse.SUCCESS, {'msg' : 'Done'})

            except Exception as e:
                logging.critical(str(e))
                cfnresponse.send(event, context, cfnresponse.FAILED, {'msg' : str(e)})
        else:
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {'msg' : 'No error'})
    except Exception as e:
        logging.critical(str(e))
        cfnresponse.send(event, context, cfnresponse.FAILED, {'msg' : str(e)})