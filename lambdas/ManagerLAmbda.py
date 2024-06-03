import cfnresponse
import traceback
import logging
import boto3
import os

logging.basicConfig(
    filename="CyngularOnboarding.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

class DeployList:
    def __init__(self):
        self.ous = []
        self.accounts = []

def handle_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            logging.critical(f"{traceback.format_exc()}")
    return wrapper

# @handle_exception
# def get_child_accounts(management_account_id):
#     org_client = boto3.client('organizations')
#     account_list = org_client.list_accounts()
#     child_accounts = []
#     for account in account_list['Accounts']:
#         if account['Id'] != management_account_id:
#             child_accounts.append(account['Id'])
    
#     return child_accounts

@handle_exception
def guardduty_exists(region):
    client = boto3.client('guardduty', region)
    response = client.list_detectors()
    if len(response['DetectorIds']) == 0:
        return False
    return True

@handle_exception
def create_guardduty():
    client_regions = os.environ['ClientRegions'].split(',')
    for region in client_regions:
        if guardduty_exists(region):
            logging.info(f'guardduty found in {region}, adding cyngular tag')
            client = boto3.client('guardduty', region)
            sts_client = boto3.client('sts')
            detectors = client.list_detectors()
            detector_id = detectors['DetectorIds'][0]
            account_id = sts_client.get_caller_identity()['Account']
            _ = client.tag_resource(
                Tags={'Value' : 'cyngular-guardduty'}, 
                ResourceArn=f'arn:aws:guardduty:{region}:{account_id}:detector/{detector_id}'
            )
        
        else:
            logging.info(f'creating guardduty in {region}')
            client = boto3.client('guardduty', region)
            detector_properties = {
                'Enable': True,
                'FindingPublishingFrequency': 'FIFTEEN_MINUTES',
                'DataSources': {
                    'S3Logs': {
                        'Enable': True
                    },
                },
                'Tags': [
                    {
                        'Value': 'cyngular-guardduty'
                    }
                ]
            }
            
            _ = client.create_detector(
                Enable=detector_properties['Enable'],
                FindingPublishingFrequency=detector_properties['FindingPublishingFrequency'],
                DataSources=detector_properties['DataSources'],
                Tags=detector_properties['Tags'][0],)

@handle_exception
def create_stack_of_stacksets(url):
    stack_client = boto3.client('cloudformation')
    is_org = os.environ['IsOrg']
    account_list = os.environ['AccountList']
    ous_list = os.environ['OUList']
    deploy_list = DeployList()
    
    if is_org != "0":
        org = boto3.client('organizations')
        paginator = org.get_paginator('list_accounts_for_parent')
        for page in paginator.paginate(ParentId=is_org):
            for account in page['Accounts']:
                deploy_list.accounts.append(account['Id'])
        for ou in org.list_roots()['Roots'][0]['OrganizationalUnits']:
            deploy_list.ous.append(ou['Id'])
            # for page in paginator.paginate(ParentId=ou['Id']):
            #     for account in page['Accounts']:
            #         deploy_list.accounts.append(account['Id'])

    if ous_list != "0":
        org = boto3.client('organizations')
        for ou in ous_list.split(','):
            deploy_list.ous.append(ou)
            # paginator = org.get_paginator('list_accounts_for_parent')
            # for page in paginator.paginate(ParentId=ou):
            #     for account in page['Accounts']:
            #         deploy_list.accounts.append(account['Id'])

    if account_list != "0":
        for account in account_list.split(','):
            deploy_list.accounts.append(account)

    # for ou in deploy_list.ous:
    # for account in deploy_list.accounts:

    # ClientName = os.environ['ClientName']
    # ClientRegions = os.environ['ClientRegions']
    # S3BucketArn = os.environ['S3BucketArn']
    # CyngularAccountId = os.environ['CyngularAccountId']

    guard_duty = os.environ['EnableGuardDuty']
    resolver = os.environ['EnableResolver']
    
    # Determine whether to include GuardDuty and Resolver deployment
    if guard_duty == 'yes':
        guard_duty = True
    elif guard_duty == 'no':
        guard_duty = False
    else:
        pass
    
    if resolver == 'yes':
        resolver = True
    elif resolver == 'no':
        resolver = False
    else: 
        pass
    
    Parameters=[
        { 'ParameterKey': 'ClientName', 'ParameterValue': os.environ['ClientName'] },
        { 'ParameterKey': 'deployRegions', 'ParameterValue': os.environ['ClientRegions'] },
        { 'ParameterKey': 'S3ManagementBucketArn', 'ParameterValue': os.environ['S3BucketArn'] },
        { 'ParameterKey': 'CyngularAccountId', 'ParameterValue': os.environ['CyngularAccountId'] },
        { 'ParameterKey': 'MgmtAccountId', 'ParameterValue': os.environ['MgmtAccountId'] },
        { 'ParameterKey': 'IsOrg', 'ParameterValue': os.environ['IsOrg'] },            
        { 'ParameterKey': 'EnableGuardDuty', 'ParameterValue': guard_duty },            
        { 'ParameterKey': 'EnableResolver',  'ParameterValue': resolver },            
        { 'ParameterKey': 'DeployList', 'ParameterValue': os.environ['DeployList'] },            
        { 'ParameterKey': 'AccountList', 'ParameterValue': os.environ['AccountList'] },            
        { 'ParameterKey': 'OUList', 'ParameterValue': os.environ['OUList'] },        
         
    ]
    stack_client.create_stack(
        StackName='cyngular-stack2',
        TemplateURL=url,
        Parameters=Parameters,
        Capabilities=['CAPABILITY_IAM']
    )

@handle_exception
def invoke_lambda_3():
    lambda_client = boto3.client('lambda')
    response = lambda_client.invoke(
        FunctionName='cyngular-lambda-update-cyngular-bucket',
        InvocationType = 'RequestResponse',
        LogType='Tail',
    )
    logging.info('lmbada E invoked!')
    if response['StatusCode'] != 200:
        logging.critical(f"Error {response}")

@handle_exception
def cyngular_function(event, context):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logging.info('STARTING CYNGULAR\'S FUNCTION...')
    # print event for responseurl
    logging.info(f"copy this to manually delete the custom resource: \n{event}")
    # if stack is being created
    if event['RequestType'] == 'Create':        
        try:
            stack2_url = event['ResourceProperties']['Stack2URL']
            stackset2_url = event['ResourceProperties']['StackSet2URL']
            child_accounts = get_child_accounts(os.environ['currentAccountId'])
            invoke_lambda_3()
            logging.info("CREATING CYNGULAR STACKS")
            create_stack_of_stacksets(stack2_url)
   
            logging.info("Creating GuardDuties")
            create_guardduty()
            logging.info("STARING CYNGULAR STACKSET2")
            create_stackset2(child_accounts,stackset2_url)
            logging.info("DONE WITH ALL CYNGULAR STACKS!")
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {'msg' : 'Done'})
        except Exception as e:
            logging.critical(str(e))
            cfnresponse.send(event, context, cfnresponse.FAILED, {'msg' : str(e)})
    else:
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {'msg' : 'No error'})