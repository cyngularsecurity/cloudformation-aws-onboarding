import boto3

# account_id = '123456789012'
# ou_id = 'ou-exam-ple1'

client = boto3.client('organizations')
root_id = client.list_roots()['Roots'][0]['Id']

def list_ous(parent_id):
    ou_paginator = client.get_paginator('list_organizational_units_for_parent')
    for ou_page in ou_paginator.paginate(ParentId=parent_id):
        for ou in ou_page['OrganizationalUnits']:
            print(f"OU ID: {ou['Id']}, Name: {ou['Name']}")
            list_ous(ou['Id'])
            
def get_org_id_by_account_id(account_id):
    response = client.describe_account(AccountId=account_id)
    return response['Account']['Arn'].split(":")[5].split("/")[1]

def get_general_info_by_account_id(account_id):
    response = client.describe_account(AccountId=account_id)
    return response['Account']

def get_accounts_for_org():
    accounts = []
    paginator = client.get_paginator('list_accounts')
    for page in paginator.paginate():
        accounts.extend(page['Accounts'])
    return accounts

def get_accounts_for_ou(ou_id):
    accounts = []
    paginator = client.get_paginator('list_accounts_for_parent')
    for page in paginator.paginate(ParentId=ou_id):
        accounts.extend(page['Accounts'])
    return accounts

def list_ous_recursively(parent_id):
    ous = []
    paginator = client.get_paginator('list_organizational_units_for_parent')
    for page in paginator.paginate(ParentId=parent_id):
        for ou in page['OrganizationalUnits']:
            ous.append(ou)
            ous.extend(list_ous_recursively(ou['Id']))
    return ous

def lambda_handler():
    root_response = client.list_roots()
    if 'Roots' in root_response and len(root_response['Roots']) > 0:
        root_id = root_response['Roots'][0]['Id']
    else:
        print("Could not fetch the root ID.")
        exit(1)
    list_ous(root_id)
    # get_org_id_by_account_id(root_id)
    # get_general_info_by_account_id(root_id)
    accs = get_accounts_for_org()
    print(f"{accs}")
    
lambda_handler()
    
# list_roots = org_client.list_roots()
# root_id = list_roots['Roots'][0]['Id']
# root_name = list_roots['Roots'][0]['Name']
# oulist = org_client.list_organizational_units_for_parent(ParentId=root_id)
# # aws_acc_ou_path = {}

# for ou in oulist['OrganizationalUnits']:
#     ou_id = ou['Id']
#     ou_name = ou['Name']
#     ou_path = root_name + "/" + ou_name
#     org_unit_info = org_client.list_organizational_units_for_parent(ParentId=ou_id)

#     while True:
#           for oui in org_unit_info['OrganizationalUnits']:
#               org_id = oui['Id']
#               ou_path = ou_path + "/" + oui['Name']
#           if 'NextToken' in org_unit_info:
#              org_unit_info = org_client.list_organizational_units_for_parent(ParentId=ou_id, NextToken=org_unit_info['NextToken'])
#           else:
#              break
#     #print (ou_path)
    
# def accounts_with_ou_path(org_client: boto3.client, ou_id: str, path: str) -> list:
#     """ Return list of accounts at this OU as well as deeper """
#     ou_list = []

#     # I. Get further children ous
#     paginator = org_client.get_paginator('list_children')
#     pages = paginator.paginate(
#         ParentId=ou_id,
#         ChildType='ORGANIZATIONAL_UNIT'
#     )
#     for page in pages:
#         for child in page['Children']:
#             ou_list.extend(accounts_with_ou_path(org_client, child['Id'], path+ou_id+'/'))

#     # II. Get Accounts located at ou
#     pages = paginator.paginate(
#         ParentId=ou_id,
#         ChildType='ACCOUNT'
#     )
#     for page in pages:
#         for child in page['Children']:
#             ou_list.append(path+ou_id+'/'+child['Id'])

#     return ou_list

# account_list = accounts_with_ou_path(org_client, 'r-xxxx', '/')
# print(account_list)