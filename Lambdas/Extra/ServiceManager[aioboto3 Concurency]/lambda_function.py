import asyncio
import aioboto3
import json
import logging
import os
import time
import traceback
from typing import Dict, List, Any
import cfnresponse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class AsyncServiceManager:
    def __init__(self):        
        self.client_name = os.environ.get('CLIENT_NAME')
        self.region_processor_function = os.environ.get('REGION_PROCESSOR_FUNCTION_NAME')
        self.cyngular_bucket = os.environ.get('CYNGULAR_BUCKET')
        self.cyngular_role_arn = os.environ.get('CYNGULAR_ROLE_ARN')

        self.enable_dns = os.environ.get('ENABLE_DNS', 'false').lower() == 'true'
        self.enable_eks = os.environ.get('ENABLE_EKS', 'false').lower() == 'true'
        self.enable_vpc_flow_logs = os.environ.get('ENABLE_VPC_FLOW_LOGS', 'false').lower() == 'true'

        # throttling limits
        self.max_concurrent_invocations = int(os.environ.get('MAX_CONCURRENT_INVOCATIONS', '10'))
        self.invocation_delay = float(os.environ.get('INVOCATION_DELAY_SECONDS', '0.2'))
        
        self.session = aioboto3.Session()

    # async since is using aioboto3 client
    async def get_enabled_regions(self) -> List[str]:
        """Get list of enabled regions for the account"""
        try:
            async with self.session.client('ec2') as ec2_client:
                response = await ec2_client.describe_regions(AllRegions=False)
                regions = [r['RegionName'] for r in response['Regions']]
                
                logger.info(f"Found {len(regions)} enabled regions: {regions}")
                return regions
        except Exception as e:
            logger.error(f"Error getting enabled regions: {str(e)}")
            # Fallback to current region only
            current_region = os.environ.get('AWS_REGION', 'us-east-1')
            logger.info(f"Using current region: {current_region}")
            return [current_region]

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

    async def invoke_region_processor(self, service: str, region: str, semaphore: asyncio.Semaphore) -> Dict[str, Any]:
        """Invoke the region processor lambda for a specific service and region with concurrency control"""
        async with semaphore:  # Limit concurrent invocations
            payload = {
                'service': service,
                'region': region,
                'client_name': self.client_name,
                'cyngular_bucket': self.cyngular_bucket,
                'cyngular_role_arn': self.cyngular_role_arn
            }
            
            try:
                async with self.session.client('lambda') as lambda_client:
                    response = await lambda_client.invoke(
                        FunctionName=self.region_processor_function,
                        InvocationType='RequestResponse',
                        Payload=json.dumps(payload)
                    )
                    
                    payload_bytes = await response['Payload'].read()
                    response_payload = json.loads(payload_bytes)
                    
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
            finally:
                # avoid overwhelming downstream services
                if self.invocation_delay > 0:
                    await asyncio.sleep(self.invocation_delay)

    async def process_all_services(self) -> Dict[str, Any]:
        """Process all enabled services across all regions in parallel"""
        regions = await self.get_enabled_regions()
        services = self.get_services_to_configure()
        
        # concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent_invocations)
        
        tasks = []
        for service in services:
            for region in regions:
                task = self.invoke_region_processor(service, region, semaphore)
                tasks.append(task)
        
        logger.info(f"Starting parallel processing of {len(tasks)} tasks across {len(regions)} regions and {len(services)} services")
        
        start_time = time.time()
        try:
            results_list = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Unexpected error during parallel processing: {str(e)}")
            results_list = []
        
        end_time = time.time()
        
        # Process results and separate successful from failed
        successful_results = []
        failed_results = []
        
        for result in results_list:
            if isinstance(result, Exception):
                # Task raised an exception
                failed_results.append({
                    'success': False,
                    'service': 'unknown',
                    'region': 'unknown',
                    'error': str(result)
                })
            elif isinstance(result, dict):
                if result.get('success', False):
                    successful_results.append(result)
                else:
                    failed_results.append(result)
            else:
                # Unexpected result type
                failed_results.append({
                    'success': False,
                    'service': 'unknown',
                    'region': 'unknown',
                    'error': f"Unexpected result type: {type(result)}"
                })
        
        # Compile final results
        final_results = {
            'regions': regions,
            'services_processed': services,
            'total_tasks': len(tasks),
            'services_done': len(successful_results),
            'services_failed': len(failed_results),
            'success_rate': len(successful_results) / len(tasks) if tasks else 0,
            'processing_time_seconds': round(end_time - start_time, 2),
            'concurrency_limit': self.max_concurrent_invocations,
            'successful_results': successful_results,
            'failed_results': failed_results
        }
        
        logger.info(f"Parallel processing complete in {final_results['processing_time_seconds']}s. "
                   f"Success: {final_results['services_done']}, Failed: {final_results['services_failed']}, "
                   f"Success Rate: {final_results['success_rate']:.2%}")
        
        return final_results

    async def handle_cloudformation_event_async(self, event: Dict[str, Any], context: Any) -> None:
        """Handle CloudFormation custom resource events asynchronously"""
        try:
            request_type = event['RequestType']
            logger.info(f"CloudFormation request type: {request_type}")
            
            if request_type in ['Create', 'Update']:
                results = await self.process_all_services()
                
                # Determine if the overall operation was successful
                # Consider it successful if at least 80% of tasks succeed
                success_threshold = float(os.environ.get('SUCCESS_THRESHOLD', '0.8'))
                
                if results['success_rate'] >= success_threshold:
                    logger.info(f"Operation successful with {results['success_rate']:.2%} success rate")
                    cfnresponse.send(event, context, cfnresponse.SUCCESS, {
                        'message': f"Success: {results['services_done']}/{results['total_tasks']} tasks completed",
                        'success_rate': results['success_rate']
                    })
                else:
                    error_msg = f"Failed: Only {results['services_done']}/{results['total_tasks']} tasks completed ({results['success_rate']:.2%} success rate)"
                    logger.warning(f"Operation failed: {error_msg}")
                    cfnresponse.send(event, context, cfnresponse.FAILED, {
                        'message': error_msg,
                        'success_rate': results['success_rate'],
                        'failed_tasks': len(results['failed_results'])
                    })
                    
            elif request_type == 'Delete':
                # No cleanup needed for this implementation
                cfnresponse.send(event, context, cfnresponse.SUCCESS, {
                    'message': 'Delete operation completed'
                })
                
        except Exception as e:
            logger.error(f"Error handling CloudFormation event: {str(e)}")
            logger.error(traceback.format_exc())
            cfnresponse.send(event, context, cfnresponse.FAILED, {
                'message': str(e)
            })

    def handle_cloudformation_event(self, event: Dict[str, Any], context: Any) -> None:
        """Synchronous wrapper for CloudFormation events"""
        asyncio.run(self.handle_cloudformation_event_async(event, context))

    async def handle_scheduled_event_async(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle scheduled EventBridge events asynchronously"""
        logger.info("Handling scheduled event")
        return await self.process_all_services()

    def handle_scheduled_event(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Synchronous wrapper for scheduled events"""
        return asyncio.run(self.handle_scheduled_event_async(event, context))

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main lambda handler with async execution"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        service_manager = AsyncServiceManager()
    
        # Check if this is a CloudFormation custom resource event
        if 'RequestType' in event and 'StackId' in event:
            service_manager.handle_cloudformation_event(event, context)
            return {'statusCode': 200}
        
        # Check if this is a scheduled event or direct invocation
        elif 'source' in event and event['source'] == 'aws.events':
            result = service_manager.handle_scheduled_event(event, context)
            return {'statusCode': 200, 'body': json.dumps(result)}
        
        # Direct invocation
        else:
            result = asyncio.run(service_manager.process_all_services())
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