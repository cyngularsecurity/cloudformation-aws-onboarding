import json
import logging
import traceback
import time
from typing import Dict, Any
from service_registry import SERVICE_REGISTRY
# from cyngular_common.metrics import MetricsCollector

logger = logging.getLogger(__name__)

class RegionProcessor:
    def __init__(
        self,
        region: str,
        client_name: str,
        cyngular_bucket: str,
        cyngular_role_arn: str,
        enable_param: str = None,
    ):
        self.region = region
        self.client_name = client_name
        self.cyngular_bucket = cyngular_bucket
        self.cyngular_role_arn = cyngular_role_arn
        self.enable_param = enable_param

        # # Initialize metrics collector
        # self.metrics = MetricsCollector(client_name, "RegionalServiceManager")

    def process_service(self, service: str) -> Dict[str, Any]:
        """Process a specific service for the region"""

        if service not in SERVICE_REGISTRY:
            return {"success": False, "error": f"Unknown service: {service}"}

        try:
            service_config = SERVICE_REGISTRY[service]
            handler = service_config.handler
            required_params = service_config.required_params

            # Build parameters dynamically based on service requirements
            params = []
            for param in required_params:
                if param == "region":
                    params.append(self.region)
                elif param == "cyngular_bucket":
                    params.append(self.cyngular_bucket)
                elif param == "cyngular_role_arn":
                    params.append(self.cyngular_role_arn)
                elif param == "enable_param":
                    params.append(self.enable_param)
                else:
                    logger.error(
                        f"Unknown parameter {param} required for service {service}"
                    )
                    return {"success": False, "error": f"Unknown parameter: {param}"}

            result = handler(*params)
            result["service"] = service
            result["region"] = self.region

            # if result.get("success"):
            #     self.metrics.put_metric(
            #         namespace="Cyngular/Services",
            #         metric_name="ServiceProcessed",
            #         value=1,
            #         dimensions={"Service": service, "Region": self.region},
            #     )
            # else:
            #     self.metrics.put_metric(
            #         namespace="Cyngular/Services",
            #         metric_name="ServiceFailed",
            #         value=1,
            #         dimensions={"Service": service, "Region": self.region},
            #     )

            return result

        except Exception as e:
            logger.error(f"Error processing service {service}: {str(e)}")
            return {
                "success": False,
                "service": service,
                "region": self.region,
                "error": str(e),
            }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main lambda handler"""
    logger.info(f"Received event: {json.dumps(event)}")

    client_name = event["client_name"]
    # try:
    #     temp_metrics = MetricsCollector(client_name, "RegionalServiceManager")
    #     temp_metrics.record_invocation("Direct")
    # except Exception:
    #     logger.warning("Failed to record invocation metrics")

    # Extract and validate all required parameters
    try:
        service = event["service"]
        region = event["region"]
        client_name = event["client_name"]
        cyngular_bucket = event["cyngular_bucket"]
        cyngular_role_arn = event["cyngular_role_arn"]
        enable_param = event["enable_param"]
    except KeyError as e:
        missing_param = str(e).strip("'")
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "success": False,
                    "error": f"Missing required parameter: {missing_param}",
                }
            ),
        }

    try:
        processor = RegionProcessor(
            region, client_name, cyngular_bucket, cyngular_role_arn, enable_param
        )
        result = processor.process_service(service)
        logger.info(f"Processing complete: {result}")

        return {"statusCode": 200, "body": json.dumps(result)}

    except Exception as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "timestamp": time.time(),
        }

        logger.error(
            f"RegionProcessor handler failed: {error_details['error_type']} - {error_details['error_message']}"
        )
        logger.error(traceback.format_exc())  # Log full traceback for debugging

        # try:
        #     if "processor" in locals():
        #         processor.metrics.record_error(
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
