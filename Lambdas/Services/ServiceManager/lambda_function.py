import boto3
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any
from botocore.config import Config
from cyngular_common import cfnresponse
# from cyngular_common.metrics import MetricsCollector

# Use Lambda runtime logger properly
logger = logging.getLogger(__name__)


class ServiceManager:
    MAX_CONCURRENT_WORKERS = 4
    INVOCATION_DELAY_SECONDS = 0.1

    def __init__(self, lambda_context):
        # Required environment variables - fail if not present
        self.client_name = os.environ["CLIENT_NAME"]
        self.region_processor_function = os.environ[
            "REGIONAL_SERVICE_MANAGER_FUNCTION_NAME"
        ]
        self.cyngular_bucket = os.environ["CYNGULAR_BUCKET"]
        self.cyngular_role_arn = os.environ["CYNGULAR_ROLE_ARN"]
        self.context = lambda_context

        # Service enable flags with defaults
        self.enable_dns = os.environ.get("ENABLE_DNS", "false")
        self.enable_eks = os.environ.get("ENABLE_EKS", "false")
        self.enable_vpc_flow_logs = os.environ.get("ENABLE_VPC_FLOW_LOGS", "false")

        # Configure clients with retry settings
        retry_config = Config(retries={"max_attempts": 3, "mode": "adaptive"})
        self.lambda_client = boto3.client("lambda", config=retry_config)
        self.ec2_client = boto3.client("ec2", config=retry_config)

        self.fallback_lambda_region = self.context.invoked_function_arn.split(":")[3]

        # self.metrics = MetricsCollector(self.client_name, "ServiceOrchestrator")

    def get_enabled_regions(self) -> List[str]:
        """Get list of enabled regions for the account"""
        try:
            excluded_regions = (
                os.environ.get("EXCLUDED_REGIONS", "").split(",")
                if os.environ.get("EXCLUDED_REGIONS")
                else []
            )
            response = self.ec2_client.describe_regions(AllRegions=False)
            regions = [
                r["RegionName"]
                for r in response["Regions"]
                if r["RegionName"] not in excluded_regions
            ]

            logger.info(
                f"[{self.fallback_lambda_region} | ServiceManager] Found {len(regions)} enabled regions: {regions}"
            )
            return regions
        except Exception as e:
            logger.error(
                f"[{self.fallback_lambda_region} | ServiceManager] Error getting enabled regions: {str(e)}"
            )
            current_lambda_region = self.fallback_lambda_region
            logger.warning(
                f"[{self.fallback_lambda_region} | ServiceManager] Falling back to current region: {current_lambda_region}"
            )
            return [current_lambda_region]

    def get_services_to_configure(self) -> List[str]:
        """Get list of services that need to be configured"""
        services = ["os"]

        if self.enable_dns.lower() != "false":
            services.append("dns")
        if self.enable_eks.lower() != "false":
            services.append("eks")
        if self.enable_vpc_flow_logs.lower() != "false":
            services.append("vfl")

        logger.info(
            f"[{self.fallback_lambda_region} | ServiceManager] Services to configure: {services}"
        )
        return services

    def invoke_region_processor_task(self, service: str, region: str) -> Dict[str, Any]:
        """Task to invoke region processor - designed for thread pool"""
        payload = {
            "service": service,
            "region": region,
            "client_name": self.client_name,
            "cyngular_bucket": self.cyngular_bucket,
            "cyngular_role_arn": self.cyngular_role_arn,
        }

        try:
            if self.INVOCATION_DELAY_SECONDS > 0:
                time.sleep(self.INVOCATION_DELAY_SECONDS)

            response = self.lambda_client.invoke(
                FunctionName=self.region_processor_function,
                InvocationType="Event",  # Asynchronous - no waiting for response
                Payload=json.dumps(payload),
            )

            # For Event invocations, AWS returns 202 immediately and runs async
            if response["StatusCode"] == 202:
                logger.info(
                    f"[{region} | ServiceManager] Successfully invoked {service} processing for {region}"
                )
                return {
                    "success": True,
                    "service": service,
                    "region": region,
                    "status": "invoked_async",
                }
            else:
                logger.error(
                    f"[{region} | ServiceManager] Failed to invoke {service} for {region}: Status {response['StatusCode']}"
                )
                return {
                    "success": False,
                    "service": service,
                    "region": region,
                    "error": f"Invocation failed with status {response['StatusCode']}",
                }

        except Exception as e:
            logger.error(
                f"[{region} | ServiceManager] Error invoking region processor for {service} in {region}: {str(e)}"
            )
            return {
                "success": False,
                "service": service,
                "region": region,
                "error": str(e),
            }

    def process_all_services(self) -> Dict[str, Any]:
        """Process all enabled services across all regions in parallel"""
        regions = self.get_enabled_regions()
        services = self.get_services_to_configure()

        tasks = [(service, region) for service in services for region in regions]

        logger.info(
            f"Starting parallel processing of {len(tasks)} tasks across {len(regions)} regions and {len(services)} services"
        )

        start_time = time.time()
        successful_results = []
        failed_results = []

        with ThreadPoolExecutor(max_workers=self.MAX_CONCURRENT_WORKERS) as executor:
            future_to_task = {
                executor.submit(self.invoke_region_processor_task, service, region): (
                    service,
                    region,
                )
                for service, region in tasks
            }

            for future in as_completed(future_to_task):
                service, region = future_to_task[future]
                try:
                    result = future.result()
                    if result["success"]:
                        successful_results.append(result)
                    else:
                        failed_results.append(result)
                except Exception as e:
                    error_details = {
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "service": service,
                        "region": region,
                    }

                    logger.error(
                        f"[{region} | ServiceManager] Task {service}/{region} failed with {error_details['error_type']}: {error_details['error_message']}"
                    )

                    failed_results.append(
                        {
                            "success": False,
                            "service": service,
                            "region": region,
                            "error": error_details["error_message"],
                            "error_type": error_details["error_type"],
                            "timestamp": time.time(),
                        }
                    )

        end_time = time.time()

        final_results = {
            "regions": regions,
            "services_processed": services,
            "total_tasks": len(tasks),
            "services_done": len(successful_results),
            "services_failed": len(failed_results),
            "success_rate": (len(successful_results) / len(tasks) * 100)
            if tasks
            else 0,
            "processing_time_seconds": round(end_time - start_time, 2),
            "max_workers": self.MAX_CONCURRENT_WORKERS,
            "successful_results": successful_results,
            "failed_results": failed_results,
        }

        logger.info(
            f"[{self.fallback_lambda_region} | ServiceManager] Parallel processing complete in {final_results['processing_time_seconds']}s. "
            f"Success: {final_results['services_done']}, Failed: {final_results['services_failed']}, "
            f"Success Rate: {final_results['success_rate']:.2%}"
        )

        # self.metrics.record_processing_results(final_results)

        return final_results

    # [Rest of the CloudFormation and event handling methods remain the same as original]
    def handle_cloudformation_event(self, event: Dict[str, Any], context: Any) -> None:
        """Handle CloudFormation custom resource events"""
        try:
            request_type = event["RequestType"]
            logger.info(f"CloudFormation request type: {request_type}")

            if request_type in ["Create", "Update"]:
                results = self.process_all_services()

                success_threshold = float(os.environ.get("SUCCESS_THRESHOLD", "0.8"))

                if results["success_rate"] >= success_threshold:
                    logger.info(
                        f"[{self.fallback_lambda_region} | ServiceManager] Operation successful with {results['success_rate']:.2%} success rate"
                    )
                    cfnresponse.send(
                        event,
                        context,
                        cfnresponse.SUCCESS,
                        {
                            "message": f"Success: {results['services_done']}/{results['total_tasks']} tasks completed"
                        },
                    )
                else:
                    error_msg = f"Failed: Only {results['services_done']}/{results['total_tasks']} tasks completed"
                    logger.warning(
                        f"[{self.fallback_lambda_region} | ServiceManager] Operation failed: {error_msg}"
                    )
                    cfnresponse.send(
                        event, context, cfnresponse.FAILED, {"message": error_msg}
                    )

            elif request_type == "Delete":
                cfnresponse.send(
                    event,
                    context,
                    cfnresponse.SUCCESS,
                    {"message": "Delete operation completed"},
                )

        except Exception as e:
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "request_type": event.get("RequestType", "Unknown"),
                "stack_id": event.get("StackId", "Unknown")[:100]
                if event.get("StackId")
                else "Unknown",
            }

            logger.error(
                f"[{self.fallback_lambda_region} | ServiceManager] CloudFormation event handling failed: {error_details['error_type']} - {error_details['error_message']}"
            )
            logger.error(
                f"[{self.fallback_lambda_region} | ServiceManager] Event context: RequestType={error_details['request_type']}, StackId={error_details['stack_id']}"
            )

            cfnresponse.send(
                event,
                context,
                cfnresponse.FAILED,
                {
                    "message": f"{error_details['error_type']}: {error_details['error_message']}",
                    "error_type": error_details["error_type"],
                },
            )

    def handle_scheduled_event(
        self, event: Dict[str, Any], context: Any
    ) -> Dict[str, Any]:
        """Handle scheduled EventBridge events"""
        logger.info("Handling scheduled event")
        return self.process_all_services()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main lambda handler"""
    logger.info(f"Received event: {json.dumps(event)}")

    event_type = "Unknown"
    if "RequestType" in event and "StackId" in event:
        event_type = "CloudFormation"
    elif "source" in event and event["source"] == "aws.events":
        event_type = "Scheduled"
    else:
        event_type = "Direct"

    try:
        service_manager = ServiceManager(context)

        # service_manager.metrics.record_invocation(event_type)

        # CloudFormation event
        if "RequestType" in event and "StackId" in event:
            service_manager.handle_cloudformation_event(event, context)
            return {"statusCode": 200}

        # scheduled event
        elif "source" in event and event["source"] == "aws.events":
            result = service_manager.handle_scheduled_event(event, context)
            return {"statusCode": 200, "body": json.dumps(result)}

        # Direct invocation
        else:
            result = service_manager.process_all_services()
            return {"statusCode": 200, "body": json.dumps(result)}
    except Exception as e:
        fallback_region = "unknown"
        try:
            if "service_manager" in locals():
                fallback_region = service_manager.fallback_lambda_region
        except Exception:
            logger.error(
                f"[{fallback_region} | ServiceManager] Lambda handler failed: {type(e).__name__} - {str(e)}"
            )

        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "timestamp": time.time(),
            "event_type": event_type,
        }

        logger.error(
            f"[{fallback_region} | ServiceManager] Lambda handler failed: {error_details['error_type']} - {error_details['error_message']}"
        )
        logger.error(
            f"[{fallback_region} | ServiceManager] Event type: {error_details['event_type']}"
        )

        # try:
        #     if "service_manager" in locals():
        #         service_manager.metrics.record_error(
        #             error_details["error_type"], error_details["error_message"]
        #         )
        # except Exception:
        #     logger.warning(traceback.format_exc())

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "success": False,
                    "error": error_details["error_message"],
                    "error_type": error_details["error_type"],
                    "timestamp": error_details["timestamp"],
                }
            ),
        }
