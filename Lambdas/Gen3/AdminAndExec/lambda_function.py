import boto3
import json
import logging
import os
import cfnresponse
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class AdminAndExecRoleManager:
    def __init__(self):
        self.cloudformation_client = boto3.client('cloudformation')
        self.organizations_client = boto3.client('organizations')
        
        self.is_org = os.environ.get('IS_ORG', 'false').lower() == 'true'
        self.admin_template_url = os.environ.get('ADMIN_TEMPLATE_URL')
        self.exec_template_url = os.environ.get('EXEC_TEMPLATE_URL')

    def is_org_deployment(self) -> tuple[bool, str]:
        """Check if the account is part of an AWS organization."""
        try:
            if not self.is_org:
                return False, "Not an organization account deployment, org id param is empty."

            root_response = self.organizations_client.list_roots()
            if 'Roots' in root_response and len(root_response['Roots']) > 0:
                return True, root_response['Roots'][0]['Id']
            else:
                return False, "No organization roots found."
        except Exception as e:
            logger.error(f"Error checking organization deployment: {str(e)}")
            return False, str(e)

    def stack_exists(self, stack_name: str) -> bool:
        """Check if a CloudFormation stack exists."""
        try:
            self.cloudformation_client.describe_stacks(StackName=stack_name)
            return True
        except self.cloudformation_client.exceptions.ClientError as e:
            if 'does not exist' in str(e):
                return False
            else:
                raise e

    def create_stack(self, stack_name: str, template_url: str, capabilities: list = None) -> str:
        """Create a CloudFormation stack."""
        try:
            if self.stack_exists(stack_name):
                logger.info(f"Stack {stack_name} already exists, skipping creation")
                return "EXISTS"

            params = {
                'StackName': stack_name,
                'TemplateURL': template_url,
                'Tags': [
                    {'Key': 'Vendor', 'Value': 'Cyngular Security'},
                    {'Key': 'Purpose', 'Value': 'StackSet Role Management'}
                ]
            }

            if capabilities:
                params['Capabilities'] = capabilities

            response = self.cloudformation_client.create_stack(**params)
            logger.info(f"Created stack {stack_name}: {response['StackId']}")
            return response['StackId']

        except Exception as e:
            logger.error(f"Error creating stack {stack_name}: {str(e)}")
            raise e

    def wait_for_stack_completion(self, stack_name: str) -> bool:
        """Wait for stack creation to complete."""
        try:
            waiter = self.cloudformation_client.get_waiter('stack_create_complete')
            waiter.wait(StackName=stack_name)
            logger.info(f"Stack {stack_name} creation completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error waiting for stack {stack_name} completion: {str(e)}")
            return False

    def create_admin_and_exec_roles(self) -> Dict[str, Any]:
        """Create both admin and execution roles for StackSet."""
        try:
            is_org, org_info = self.is_org_deployment()
            logger.info(f"Organization deployment: {is_org}, Info: {org_info}")

            results = {
                'organization_deployment': is_org,
                'organization_info': org_info,
                'admin_role': None,
                'exec_role': None
            }

            # Create Administration Role
            admin_stack_name = "CyngularCloudFormationStackSetAdministrationRole"
            try:
                admin_result = self.create_stack(
                    admin_stack_name,
                    self.admin_template_url,
                    ['CAPABILITY_NAMED_IAM']
                )
                results['admin_role'] = {
                    'stack_name': admin_stack_name,
                    'status': 'created' if admin_result != 'EXISTS' else 'exists',
                    'stack_id': admin_result
                }
                
                if admin_result != 'EXISTS':
                    self.wait_for_stack_completion(admin_stack_name)

            except Exception as e:
                logger.error(f"Error creating admin role: {str(e)}")
                results['admin_role'] = {
                    'stack_name': admin_stack_name,
                    'status': 'failed',
                    'error': str(e)
                }

            # Create Execution Role
            exec_stack_name = "CyngularCloudFormationStackSetExecutionRole"
            try:
                exec_result = self.create_stack(
                    exec_stack_name,
                    self.exec_template_url,
                    ['CAPABILITY_NAMED_IAM']
                )
                results['exec_role'] = {
                    'stack_name': exec_stack_name,
                    'status': 'created' if exec_result != 'EXISTS' else 'exists',
                    'stack_id': exec_result
                }
                
                if exec_result != 'EXISTS':
                    self.wait_for_stack_completion(exec_stack_name)

            except Exception as e:
                logger.error(f"Error creating execution role: {str(e)}")
                results['exec_role'] = {
                    'stack_name': exec_stack_name,
                    'status': 'failed',
                    'error': str(e)
                }

            return results

        except Exception as e:
            logger.error(f"Error in create_admin_and_exec_roles: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def handle_cloudformation_event(self, event: Dict[str, Any], context: Any) -> None:
        """Handle CloudFormation custom resource events."""
        try:
            request_type = event['RequestType']
            logger.info(f"CloudFormation request type: {request_type}")
            
            if request_type in ['Create', 'Update']:
                results = self.create_admin_and_exec_roles()
                
                # Check if both roles were created successfully
                admin_success = results.get('admin_role', {}).get('status') in ['created', 'exists']
                exec_success = results.get('exec_role', {}).get('status') in ['created', 'exists']
                
                if admin_success and exec_success:
                    cfnresponse.send(event, context, cfnresponse.SUCCESS, results)
                else:
                    error_msg = f"Failed to create roles. Admin: {results.get('admin_role', {})}, Exec: {results.get('exec_role', {})}"
                    cfnresponse.send(event, context, cfnresponse.FAILED, results, reason=error_msg)
                    
            elif request_type == 'Delete':
                # For delete operations, we might want to clean up resources
                # For now, just return success as roles might be needed by other resources
                cfnresponse.send(event, context, cfnresponse.SUCCESS, {'message': 'Delete operation completed'})
                
        except Exception as e:
            logger.error(f"Error handling CloudFormation event: {str(e)}")
            cfnresponse.send(event, context, cfnresponse.FAILED, {}, reason=str(e))

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main lambda handler"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    manager = AdminAndExecRoleManager()
    
    # Check if this is a CloudFormation custom resource event
    if 'RequestType' in event and 'StackId' in event:
        manager.handle_cloudformation_event(event, context)
        return {'statusCode': 200}
    
    # Direct invocation
    else:
        result = manager.create_admin_and_exec_roles()
        return {'statusCode': 200, 'body': json.dumps(result)}