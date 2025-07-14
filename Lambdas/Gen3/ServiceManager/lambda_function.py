import boto3
import json
import logging
import os
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any
import cfnresponse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class ServiceManager:
    # concurrency limits
    MAX_CONCURRENT_WORKERS = 8
    INVOCATION_DELAY_SECONDS = 0.1

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
            excluded_regions = os.environ.get('EXCLUDED_REGIONS', '').split(',')
            response = self.ec2_client.describe_regions(AllRegions=False)
            regions = [
                r['RegionName'] for r in response['Regions']
                if r['RegionName'] not in excluded_regions
            ]
            
            logger.info(f"Found {len(regions)} enabled regions: {regions}")
            return regions
        except Exception as e:
            logger.error(f"Error getting enabled regions: {str(e)}")
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

    def invoke_region_processor_task(self, service: str, region: str) -> Dict[str, Any]:
        """Single task to invoke region processor - designed for thread pool"""
        payload = {
            'service': service,
            'region': region,
            'client_name': self.client_name,
            'cyngular_bucket': self.cyngular_bucket,
            'cyngular_role_arn': self.cyngular_role_arn
        }
        
        try:
            if self.INVOCATION_DELAY_SECONDS > 0:
                time.sleep(self.INVOCATION_DELAY_SECONDS)
            
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
        """Process all enabled services across all regions in parallel"""
        regions = self.get_enabled_regions()
        services = self.get_services_to_configure()

        tasks = [
            (service, region) for service in services
            for region in regions
        ]

        logger.info(f"Starting parallel processing of {len(tasks)} tasks across {len(regions)} regions and {len(services)} services")

        start_time = time.time()
        successful_results = []
        failed_results = []

        with ThreadPoolExecutor(max_workers=self.MAX_CONCURRENT_WORKERS) as executor:
            future_to_task = {
                executor.submit(self.invoke_region_processor_task, service, region): (service, region)
                for service, region in tasks
            }

            for future in as_completed(future_to_task):
                service, region = future_to_task[future]
                try:
                    result = future.result()
                    if result['success']:
                        successful_results.append(result)
                    else:
                        failed_results.append(result)
                except Exception as e:
                    logger.error(f"Task {service}/{region} generated exception: {str(e)}")
                    failed_results.append({
                        'success': False,
                        'service': service,
                        'region': region,
                        'error': str(e)
                    })

        end_time = time.time()

        final_results = {
            'regions': regions,
            'services_processed': services,
            'total_tasks': len(tasks),
            'services_done': len(successful_results),
            'services_failed': len(failed_results),
            'success_rate': (len(successful_results) / len(tasks) * 100) if tasks else 0,
            'processing_time_seconds': round(end_time - start_time, 2),
            'max_workers': self.MAX_CONCURRENT_WORKERS,
            'successful_results': successful_results,
            'failed_results': failed_results
        }

        logger.info(f"Parallel processing complete in {final_results['processing_time_seconds']}s. "
                   f"Success: {final_results['services_done']}, Failed: {final_results['services_failed']}, "
                   f"Success Rate: {final_results['success_rate']:.2%}")

        return final_results

    # [Rest of the CloudFormation and event handling methods remain the same as original]
    def handle_cloudformation_event(self, event: Dict[str, Any], context: Any) -> None:
        """Handle CloudFormation custom resource events"""
        try:
            request_type = event['RequestType']
            logger.info(f"CloudFormation request type: {request_type}")

            if request_type in ['Create', 'Update']:
                results = self.process_all_services()

                success_threshold = float(os.environ.get('SUCCESS_THRESHOLD', '0.8'))

                if results['success_rate'] >= success_threshold:
                    logger.info(f"Operation successful with {results['success_rate']:.2%} success rate")
                    cfnresponse.send(event, context, cfnresponse.SUCCESS, {
                        'message': f"Success: {results['services_done']}/{results['total_tasks']} tasks completed"
                    })
                else:
                    error_msg = f"Failed: Only {results['services_done']}/{results['total_tasks']} tasks completed"
                    logger.warning(f"Operation failed: {error_msg}")
                    cfnresponse.send(event, context, cfnresponse.FAILED, {'message': error_msg})

            elif request_type == 'Delete':
                cfnresponse.send(event, context, cfnresponse.SUCCESS, {
                    'message': 'Delete operation completed'
                })

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
