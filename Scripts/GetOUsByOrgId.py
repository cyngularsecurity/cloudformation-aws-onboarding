import boto3

client = boto3.client('organizations')

def get_org_id_by_account_id(account_id):
    response = client.describe_account(AccountId=account_id)
    return response['Account']['Arn'].split(":")[5].split("/")[1]
# org_id = get_org_id_by_account_id("026207525186")

organization_info = []
root_accounts = []
OUIds = []
AccIds = []

def list_ous_and_accounts(parent_id):
    try:
        acc_paginator = client.get_paginator('list_accounts_for_parent')
        for acc_page in acc_paginator.paginate(ParentId=parent_id):
            for account in acc_page['Accounts']:
                root_accounts.append({'Account_ID': account['Id'], 'Account_Name': account['Name']})
    except Exception as e:
        print(f"An error occurred while fetching accounts under root: {e}")

    try:
        ou_paginator = client.get_paginator('list_organizational_units_for_parent')
        for ou_page in ou_paginator.paginate(ParentId=parent_id):
            for ou in ou_page['OrganizationalUnits']:
                ou_info = {'OU_ID': ou['Id'], 'OU_Name': ou['Name']}
                
                # Fetch accounts under the current OU
                accounts = []
                acc_paginator = client.get_paginator('list_accounts_for_parent')
                for acc_page in acc_paginator.paginate(ParentId=ou['Id']):
                    for account in acc_page['Accounts']:
                        accounts.append({'Account_ID': account['Id'], 'Account_Name': account['Name']})

                ou_info['Accounts'] = accounts
                
                organization_info.append(ou_info)
                list_ous_and_accounts(ou['Id'])
    except Exception:
        pass

def lambda_handler():
    try:
        root_response = client.list_roots()
        if 'Roots' in root_response and len(root_response['Roots']) > 0:
            root_id = root_response['Roots'][0]['Id']
        else:
            print("Could not fetch the root ID.")
            exit(1)
    except Exception:
        print("Could not fetch the root ID.")
    
    # populating ous and nested accs for root id
    list_ous_and_accounts(root_id)
    
    all_accounts = []
    
    try:
        acc_paginator = client.get_paginator('list_accounts')
        for acc_page in acc_paginator.paginate():
            for account in acc_page['Accounts']:
                all_accounts.append({'Account_ID': account['Id'], 'Account_Name': account['Name']})
    except Exception as e:
        print(f"An error occurred while fetching all accounts: {e}")
    
    accounts_in_ous = [account for ou in organization_info for account in ou['Accounts']]
    root_accounts = [account for account in all_accounts if account not in accounts_in_ous]
    
    if len(root_accounts) > 0:
        organization_info.append({'OU_ID': root_id, 'OU_Name': 'Root', 'Accounts': root_accounts})

    for ou_info in organization_info:
        OUIds.append(ou_info['OU_ID'])
    
        for account in ou_info['Accounts']:
            AccIds.append(account['Account_ID'])
        
    print("listing org info\n")

    print(f"{organization_info}")

    print("listing acc in ous\n")
    print(f"{accounts_in_ous}")

    print("listing acc under root\n")
    print(f"{root_accounts}")
    
lambda_handler()
# ------------
print("out of lambda")

# Debug print extracted OU information
print(f"Extracted OU Information: {AccIds}{OUIds}")
# def list_ous_recursively(parent_id):
#     ous = []
#     paginator = client.get_paginator('list_organizational_units_for_parent')
#     for page in paginator.paginate(ParentId=parent_id):
#         for ou in page['OrganizationalUnits']:
#             ous.append(ou)
#             ous.extend(list_ous_recursively(ou['Id']))
#     return ous
    
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