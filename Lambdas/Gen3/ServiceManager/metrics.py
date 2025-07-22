"""
CloudWatch metrics utility for Cyngular Lambda functions.

This module provides centralized metrics collection and publishing functionality
for monitoring Lambda function performance and business metrics.
"""

import boto3
import logging
from typing import Dict, List, Any, Optional
from botocore.config import Config
from botocore.exceptions import ClientError

# Use Lambda runtime logger properly
logger = logging.getLogger(__name__)


class MetricsCollector:
    """Centralized metrics collection and publishing for Lambda functions"""

    def __init__(self, client_name: str, lambda_function_type: str):
        """
        Initialize metrics collector

        Args:
            client_name: The client name for dimension tagging
            lambda_function_type: The type of Lambda function (ServiceOrchestrator, RegionalServiceManager, etc.)
        """
        self.client_name = client_name
        self.lambda_function_type = lambda_function_type

        # Configure CloudWatch client with retry settings
        retry_config = Config(retries={"max_attempts": 3, "mode": "adaptive"})
        self.cloudwatch_client = boto3.client("cloudwatch", config=retry_config)

    def put_metric(
        self,
        namespace: str,
        metric_name: str,
        value: float,
        unit: str = "Count",
        dimensions: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Put a single metric to CloudWatch

        Args:
            namespace: CloudWatch namespace
            metric_name: Name of the metric
            value: Metric value
            unit: Metric unit (Count, Seconds, Percent, etc.)
            dimensions: Additional dimensions (client_name and function_type are added automatically)
        """
        try:
            # Validate that value is numeric
            if not isinstance(value, (int, float)):
                logger.warning(f"Invalid metric value for {metric_name}: {value} (type: {type(value)}). Expected numeric value. Skipping metric.")
                return
            # Default dimensions
            metric_dimensions = [
                {"Name": "ClientName", "Value": self.client_name},
                {"Name": "LambdaFunction", "Value": self.lambda_function_type},
            ]

            # Add custom dimensions
            if dimensions:
                for key, value in dimensions.items():
                    metric_dimensions.append({"Name": key, "Value": value})

            metric_data = {
                "MetricName": metric_name,
                "Value": value,
                "Unit": unit,
                "Dimensions": metric_dimensions,
            }

            self.cloudwatch_client.put_metric_data(
                Namespace=namespace, MetricData=[metric_data]
            )

            logger.info(f"Metric sent: {namespace}/{metric_name} = {value} {unit}")

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.warning(
                f"Failed to send metric {namespace}/{metric_name}: {error_code} - {str(e)}"
            )
        except Exception as e:
            logger.warning(
                f"Unexpected error sending metric {namespace}/{metric_name}: {str(e)}"
            )

    def put_metrics_batch(self, namespace: str, metrics: List[Dict[str, Any]]) -> None:
        """
        Put multiple metrics to CloudWatch in a single batch

        Args:
            namespace: CloudWatch namespace
            metrics: List of metric dictionaries with keys: name, value, unit, dimensions (optional)
        """
        if not metrics:
            return

        try:
            metric_data = []

            for metric in metrics:
                # Default dimensions
                dimensions = [
                    {"Name": "ClientName", "Value": self.client_name},
                    {"Name": "LambdaFunction", "Value": self.lambda_function_type},
                ]

                # Add custom dimensions
                if "dimensions" in metric:
                    for key, value in metric["dimensions"].items():
                        dimensions.append({"Name": key, "Value": value})

                # Ensure metric value is numeric
                metric_value = metric["value"]
                if not isinstance(metric_value, (int, float)):
                    logger.warning(f"Invalid metric value for {metric['name']}: {metric_value} (type: {type(metric_value)}). Skipping metric.")
                    continue

                metric_data.append(
                    {
                        "MetricName": metric["name"],
                        "Value": metric_value,
                        "Unit": metric.get("unit", "Count"),
                        "Dimensions": dimensions,
                    }
                )

            # CloudWatch supports max 20 metrics per batch
            for i in range(0, len(metric_data), 20):
                batch = metric_data[i : i + 20]
                self.cloudwatch_client.put_metric_data(
                    Namespace=namespace, MetricData=batch
                )

            logger.info(f"Batch metrics sent: {len(metrics)} metrics to {namespace}")

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.warning(
                f"Failed to send batch metrics to {namespace}: {error_code} - {str(e)}"
            )
        except Exception as e:
            logger.warning(
                f"Unexpected error sending batch metrics to {namespace}: {str(e)}"
            )

    def record_processing_results(
        self, results: Dict[str, Any], namespace: str = "Cyngular/Lambda"
    ) -> None:
        """
        Record standard processing results metrics

        Args:
            results: Processing results dictionary with standard keys
            namespace: CloudWatch namespace to use
        """
        metrics = []

        # Standard processing metrics
        if "total_tasks" in results:
            metrics.append({"name": "TasksProcessed", "value": results["total_tasks"]})

        if "services_done" in results:
            metrics.append(
                {"name": "TasksSuccessful", "value": results["services_done"]}
            )

        if "services_failed" in results:
            metrics.append({"name": "TasksFailed", "value": results["services_failed"]})

        if "success_rate" in results:
            metrics.append(
                {
                    "name": "SuccessRate",
                    "value": results["success_rate"],
                    "unit": "Percent",
                }
            )

        if "processing_time_seconds" in results:
            metrics.append(
                {
                    "name": "ProcessingTime",
                    "value": results["processing_time_seconds"],
                    "unit": "Seconds",
                }
            )

        # Custom metrics from results
        if "metrics" in results:
            for metric in results["metrics"]:
                metrics.append(metric)

        self.put_metrics_batch(namespace, metrics)

    def record_error(
        self, error_type: str, error_message: str, namespace: str = "Cyngular/Lambda"
    ) -> None:
        """
        Record error occurrence

        Args:
            error_type: Type of error (e.g., 'ValueError', 'ClientError')
            error_message: Error message
            namespace: CloudWatch namespace to use
        """
        self.put_metric(
            namespace=namespace,
            metric_name="Errors",
            value=1,
            dimensions={"ErrorType": error_type},
        )

        logger.error(f"Error recorded: {error_type} - {error_message}")

    def record_invocation(
        self, event_type: str = "Unknown", namespace: str = "Cyngular/Lambda"
    ) -> None:
        """
        Record Lambda function invocation

        Args:
            event_type: Type of invocation (CloudFormation, Scheduled, Direct, etc.)
            namespace: CloudWatch namespace to use
        """
        # Defensive check - ensure event_type is a string and value is always 1
        if not isinstance(event_type, str):
            logger.warning(f"Invalid event_type type: {type(event_type)}. Using 'Unknown'.")
            event_type = "Unknown"
            
        self.put_metric(
            namespace=namespace,
            metric_name="Invocations",
            value=1,
            dimensions={"EventType": event_type},
        )
