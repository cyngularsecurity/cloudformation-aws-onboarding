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
        self.client_name = os.environ.get('CLIENT_NAME')
        self.region_processor_function = os.environ.get('REGION_PROCESSOR_FUNCTION_NAME')
        self.cyngular_bucket = os.environ.get('CYNGULAR_BUCKET')
        self.cyngular_role_arn = os.environ.get('CYNGULAR_ROLE_ARN')

        self.enable_dns = os.environ.get('ENABLE_DNS', 'false').lower() == 'true'
        self.enable_eks = os.environ.get('ENABLE_EKS', 'false').lower() == 'true'
        self.enable_vpc_flow_logs = os.environ.get('ENABLE_VPC_FLOW_LOGS', 'false').lower() == 'true'

        self.lambda_client = boto3.client('lambda')
        self.ec2_client = boto3.client('ec2')

    def get_enabled_regions(self) -> List[str]:
        """Get list of enabled regions for the account"""
        try:
            regions = []
            response = self.ec2_client.describe_regions(AllRegions=False) ## only enabled
            regions = [r['RegionName'] for r in response['Regions']]

            logger.info(f"Found {len(regions)} enabled regions: {regions}")
            return regions
        except Exception as e:
            logger.error(f"Error getting enabled regions: {str(e)}")
            ## Fallback to current region only
            current_lambda_region = context.invoked_function_arn.split(':')[3]
            logger.info(f"Using current region: {current_lambda_region}")
            return [current_lambda_region]

    def get_services_to_configure(self) -> List[str]:
        """Get list of services that need to be configured"""
        services = ['os']
        
        if self.enable_dns:
            services.append('dns')
        if self.enable_eks:
            services.append('eks')
        if self.enable_vpc_flow_logs:
            services.append('vfl')
        
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
            'regions': regions,
            'services_processed': services,
            'total_tasks': len(regions) * len(services),
            'services_done': 0,
            'services_failed': 0,
            'results': []
        }

        for service in services:
            for region in regions:
                logger.info(f"Processing {service} in {region}")
                result = self.invoke_region_processor(service, region)
                results['results'].append(result)

                if result['success']:
                    results['services_done'] += 1
                else:
                    results['services_failed'] += 1

                # Add a small delay to avoid throttling
                time.sleep(0.1)

        logger.info(f"Processing complete. Success: {results['services_done']}, Failed: {results['services_failed']}")
        return results

    def handle_cloudformation_event(self, event: Dict[str, Any], context: Any) -> None:
        """Handle CloudFormation custom resource events"""
        try:
            request_type = event['RequestType']
            logger.info(f"CloudFormation request type: {request_type}")

            if request_type in ['Create', 'Update']:
                results = self.process_all_services()

                # Determine if the overall operation was successful
                if results['services_failed'] == 0:
                    # cfnresponse.send(event, context, cfnresponse.SUCCESS, results)
                    logger.info(f"results: {results}")
                    cfnresponse.send(event, context, cfnresponse.SUCCESS, {'message': 'Success'})
                else:
                    error_msg = f"Failed to configure {results['services_failed']} tasks out of {results['total_tasks']}"
                    logger.info(f"error_msg: {error_msg} | results: {results}")
                    cfnresponse.send(event, context, cfnresponse.FAILED, {'message': error_msg})
                    
            elif request_type == 'Delete':
                # (clean up resources)
                cfnresponse.send(event, context, cfnresponse.SUCCESS, {'message': 'Delete operation completed'})
                
        except Exception as e:
            logger.error(f"Error handling CloudFormation event: {str(e)}")
            cfnresponse.send(event, context, cfnresponse.FAILED, {'message': str(e)})

    def handle_scheduled_event(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle scheduled EventBridge events"""
        logger.info("Handling scheduled event")
        return self.process_all_services()

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main lambda handler"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
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
    except Exception as e:
        logger.error(f"Error in lambda handler: {str(e)}")
        logger.error(traceback.format_exc())

        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'invocation': event,
                'traceback': traceback.format_exc()
            })
        }
