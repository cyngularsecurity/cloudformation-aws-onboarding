import json
import logging
import traceback
from typing import Dict, Any
from service_registry import SERVICE_REGISTRY

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
        
        if service not in SERVICE_REGISTRY:
            return {'success': False, 'error': f'Unknown service: {service}'}
        
        try:
            service_config = SERVICE_REGISTRY[service]
            handler = service_config.handler
            required_params = service_config.required_params
            
            # Build parameters dynamically based on service requirements
            params = []
            for param in required_params:
                if param == 'region':
                    params.append(self.region)
                elif param == 'cyngular_bucket':
                    params.append(self.cyngular_bucket)
                elif param == 'cyngular_role_arn':
                    params.append(self.cyngular_role_arn)
                else:
                    logger.error(f'Unknown parameter {param} required for service {service}')
                    return {'success': False, 'error': f'Unknown parameter: {param}'}
            
            result = handler(*params)
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

    service = event.get('service')
    region = event.get('region')
    client_name = event.get('client_name')
    cyngular_bucket = event.get('cyngular_bucket')
    cyngular_role_arn = event.get('cyngular_role_arn')

    if not all([service, region, client_name, cyngular_bucket]):
        return {
            'statusCode': 400,
            'body': json.dumps({
                'success': False,
                'error': 'Missing required parameters: service / region / client_name / cyngular_bucket'
            })
        }

    try:
        processor = RegionProcessor(region, client_name, cyngular_bucket, cyngular_role_arn)
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
