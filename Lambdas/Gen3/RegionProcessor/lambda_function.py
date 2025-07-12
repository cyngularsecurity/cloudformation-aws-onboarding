import json
import logging
import traceback
from typing import Dict, Any
from .utils import process_dns_service, process_vfl_service, process_eks_service, process_os_service

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class RegionProcessor:
    def __init__(self, region: str, client_name: str, cyngular_bucket: str, cyngular_role_arn: str):
        self.region = region
        self.client_name = client_name
        self.cyngular_bucket = cyngular_bucket
        self.cyngular_role_arn = cyngular_role_arn


    def process_service(self, service: str) -> Dict[str, Any]:
        """Process a specific service for the region"""
        
        service_map = {
            'dns': process_dns_service,
            'vfl': process_vfl_service,
            'eks': process_eks_service,
            'os': process_os_service
        }
        
        if service not in service_map:
            return {'success': False, 'error': f'Unknown service: {service}'}
        
        try:
            # Call each service function with only the parameters it needs
            if service == 'dns':
                result = service_map[service](self.region, self.cyngular_bucket)
            elif service == 'vfl':
                result = service_map[service](self.region, self.cyngular_bucket)
            elif service == 'eks':
                result = service_map[service](self.region, self.cyngular_role_arn)
            elif service == 'os':
                result = service_map[service](self.region)
            else:
                return {'success': False, 'error': f'Unknown service: {service}'}
                
            result['service'] = service
            result['region'] = self.region
            return result
        except Exception as e:
            logger.error(f'Error processing service {service}: {str(e)}')
            return {
                'success': False,
                'service': service,
                'region': self.region,
                'error': str(e)
            }

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main lambda handler"""
    logger.info(f"Received event: {json.dumps(event)}")

    # Extract parameters from event
    service = event.get('service')
    region = event.get('region')
    client_name = event.get('client_name')
    cyngular_bucket = event.get('cyngular_bucket')
    cyngular_role_arn = event.get('cyngular_role_arn')

    # Validate required parameters
    if not all([service, region, client_name, cyngular_bucket]):
        return {
            'statusCode': 400,
            'body': json.dumps({
                'success': False,
                'error': 'Missing required parameters: service, region, client_name, cyngular_bucket'
            })
        }
    
    try:
        # Initialize region processor
        processor = RegionProcessor(region, client_name, cyngular_bucket, cyngular_role_arn)
        
        # Process the service
        result = processor.process_service(service)
        
        logger.info(f"Processing complete: {result}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Error in lambda handler: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            })
        }