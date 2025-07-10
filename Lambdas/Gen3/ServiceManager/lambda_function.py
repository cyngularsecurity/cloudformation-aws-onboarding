import boto3
import json
import logging
import os
import time
from typing import Dict, List, Any
import cfnresponse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class ServiceManager:
    def __init__(self):
        self.lambda_client = boto3.client('lambda')
        self.ec2_client = boto3.client('ec2')
        self.account_client = boto3.client('account')
        
        self.client_name = os.environ.get('CLIENT_NAME')
        self.region_processor_function = os.environ.get('REGION_PROCESSOR_FUNCTION_NAME')
        self.enable_dns = os.environ.get('ENABLE_DNS', 'false').lower() == 'true'
        self.enable_eks = os.environ.get('ENABLE_EKS', 'false').lower() == 'true'
        self.enable_vpc_flow_logs = os.environ.get('ENABLE_VPC_FLOW_LOGS', 'false').lower() == 'true'
        self.cyngular_bucket = os.environ.get('CYNGULAR_BUCKET')
        self.cyngular_role_arn = os.environ.get('CYNGULAR_ROLE_ARN')

    def get_enabled_regions(self) -> List[str]:
        """Get list of enabled regions for the account"""
        try:
            regions = []

            # response = self.ec2_client.describe_regions()
            # regions = [region['RegionName'] for region in response['Regions']]
            
            response = self.account_client.list_regions(RegionOptStatusContains=['ENABLED'])
            # regions.extend([r['RegionName'] for r in response['Regions']])
            
            while 'NextToken' in response:
                response = account.list_regions(NextToken=response['NextToken'])
                regions.extend([r['RegionName'] for r in response['Regions']])

            logger.info(f"Found {len(regions)} enabled regions: {regions}")
            return regions
        except Exception as e:
            logger.error(f"Error getting enabled regions: {str(e)}")
            # Fallback to current region only
            current_lambda_arn = context.invoked_function_arn
            current_lambda_region = current_lambda_arn.split(':')[3]
            logger.info(f"Using current region: {current_lambda_region}")
            return [current_lambda_region]

    def get_services_to_configure(self) -> List[str]:
        """Get list of services that need to be configured"""
        services = []
        
        if self.enable_dns:
            services.append('dns')
        if self.enable_eks:
            services.append('eks')
        if self.enable_vpc_flow_logs:
            services.append('vfl')
        
        # Always include os service
        services.append('os')
        
        logger.info(f"Services to configure: {services}")
        return services

    def invoke_region_processor(self, service: str, region: str) -> Dict[str, Any]:
        """Invoke the region processor lambda for a specific service and region"""
        payload = {
            'service': service,
            'region': region,
            'client_name': self.client_name,
            'cyngular_bucket': self.cyngular_bucket,
            'cyngular_role_arn': self.cyngular_role_arn
        }
        
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.region_processor_function,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            response_payload = json.loads(response['Payload'].read())
            
            if response['StatusCode'] == 200:
                logger.info(f"Successfully processed {service} in {region}")
                return {
                    'success': True,
                    'service': service,
                    'region': region,
                    'result': response_payload
                }
            else:
                logger.error(f"Failed to process {service} in {region}: {response_payload}")
                return {
                    'success': False,
                    'service': service,
                    'region': region,
                    'error': response_payload
                }
                
        except Exception as e:
            logger.error(f"Error invoking region processor for {service} in {region}: {str(e)}")
            return {
                'success': False,
                'service': service,
                'region': region,
                'error': str(e)
            }

    def process_all_services(self) -> Dict[str, Any]:
        """Process all enabled services across all regions"""
        regions = self.get_enabled_regions()
        services = self.get_services_to_configure()
        
        results = {
            'total_tasks': len(regions) * len(services),
            'successful_tasks': 0,
            'failed_tasks': 0,
            'results': []
        }
        
        for service in services:
            for region in regions:
                logger.info(f"Processing {service} in {region}")
                result = self.invoke_region_processor(service, region)
                results['results'].append(result)
                
                if result['success']:
                    results['successful_tasks'] += 1
                else:
                    results['failed_tasks'] += 1
                
                # Add a small delay to avoid throttling
                time.sleep(0.1)
        
        logger.info(f"Processing complete. Success: {results['successful_tasks']}, Failed: {results['failed_tasks']}")
        return results

    def handle_cloudformation_event(self, event: Dict[str, Any], context: Any) -> None:
        """Handle CloudFormation custom resource events"""
        try:
            request_type = event['RequestType']
            logger.info(f"CloudFormation request type: {request_type}")
            
            if request_type in ['Create', 'Update']:
                results = self.process_all_services()
                
                # Determine if the overall operation was successful
                if results['failed_tasks'] == 0:
                    cfnresponse.send(event, context, cfnresponse.SUCCESS, results)
                else:
                    error_msg = f"Failed to configure {results['failed_tasks']} tasks out of {results['total_tasks']}"
                    cfnresponse.send(event, context, cfnresponse.FAILED, results, reason=error_msg)
                    
            elif request_type == 'Delete':
                # For delete operations, we might want to clean up resources
                # For now, just return success
                cfnresponse.send(event, context, cfnresponse.SUCCESS, {'message': 'Delete operation completed'})
                
        except Exception as e:
            logger.error(f"Error handling CloudFormation event: {str(e)}")
            cfnresponse.send(event, context, cfnresponse.FAILED, {}, reason=str(e))

    def handle_scheduled_event(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle scheduled EventBridge events"""
        logger.info("Handling scheduled event")
        return self.process_all_services()

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main lambda handler"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    service_manager = ServiceManager()
    
    # Check if this is a CloudFormation custom resource event
    if 'RequestType' in event and 'StackId' in event:
        service_manager.handle_cloudformation_event(event, context)
        return {'statusCode': 200}
    
    # Check if this is a scheduled event
    elif 'source' in event and event['source'] == 'aws.events':
        result = service_manager.handle_scheduled_event(event, context)
        return {'statusCode': 200, 'body': json.dumps(result)}
    
    # Direct invocation
    else:
        result = service_manager.process_all_services()
        return {'statusCode': 200, 'body': json.dumps(result)}