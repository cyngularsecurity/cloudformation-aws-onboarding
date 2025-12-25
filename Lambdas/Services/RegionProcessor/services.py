import boto3
import logging
import uuid
from typing import Dict, Any
from botocore.exceptions import ClientError
from utils import check_access_entry_exists, create_cyngular_access_entry

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def process_dns_service(
    region: str,
    cyngular_bucket: str
) -> Dict[str, Any]:
    """Configure DNS logging for the region"""
    try:
        logger.info(f"STARTING DNS LOGS IN {region}...")

        r53_client = boto3.client("route53resolver", region_name=region)
        ec2_client = boto3.client("ec2", region_name=region)

        region_query_log_configs = r53_client.list_resolver_query_log_configs()[
            "ResolverQueryLogConfigs"
        ]
        cyngular_resolver_id = ""

        for config in region_query_log_configs:
            if (
                config.get("Name") == "cyngular_dns"
            ):  ## TODO Check cases where another named already exist, and attempt to connetc to cyngular
                cyngular_resolver_id = config["Id"]
                logger.info(f"EXISTING QLC FOUND: {cyngular_resolver_id}")
                break

        if not cyngular_resolver_id:
            logger.info("NO EXISTING QLC FOUND - CREATING NEW")
            try:
                response = r53_client.create_resolver_query_log_config(
                    Name="cyngular_dns",
                    DestinationArn=f"arn:aws:s3:::{cyngular_bucket}",
                    CreatorRequestId=str(uuid.uuid4()),
                    Tags=[
                        {"Key": "Purpose", "Value": "DNS Logging"},
                        {"Key": "Vendor", "Value": "Cyngular Security"},
                    ],
                )
                cyngular_resolver_id = response["ResolverQueryLogConfig"]["Id"]
                logger.info(f"NEW QLC CREATED: {cyngular_resolver_id}")
            except Exception as e:
                logger.error(f"QLC CREATION FAILED: {str(e)}")
                return {"success": False, "error": str(e)}

        vpc_list = ec2_client.describe_vpcs().get("Vpcs", [])
        logger.info(f"FOUND {len(vpc_list)} VPCS TO PROCESS")

        processed_vpcs = []
        for vpc in vpc_list:
            vpc_id = vpc.get("VpcId")
            try:
                logger.info(f"ASSOCIATING {vpc_id} WITH QLC")
                r53_client.associate_resolver_query_log_config(
                    ResolverQueryLogConfigId=cyngular_resolver_id, ResourceId=vpc_id
                )
                logger.info(f"SUCCESS: {vpc_id} associated")
                processed_vpcs.append(vpc_id)
            except Exception as e:
                if "ResourceInUseException" in str(e) or "already associated" in str(e):
                    logger.info(f"Already associated: {vpc_id}")
                    processed_vpcs.append(vpc_id)
                else:
                    logger.error(f"Association failed for {vpc_id}: {str(e)}")

        return {
            "success": True,
            "resolver_id": cyngular_resolver_id,
            "processed_vpcs": processed_vpcs
        }

    except Exception as e:
        logger.error(f"DNS processing failed: {str(e)}")
        return {"success": False, "error": str(e)}


def process_vfl_service(
    region: str,
    cyngular_bucket: str
) -> Dict[str, Any]:
    """Configure VPC Flow Logs for the region"""
    try:
        logger.info(f"STARTING VPC FLOW LOGS IN {region}...")

        ec2_client = boto3.client("ec2", region_name=region)
        vpc_list = ec2_client.describe_vpcs()
        vpc_id_list = []

        if "Vpcs" in vpc_list:
            for vpc in vpc_list["Vpcs"]:
                vpc_id_list.append(vpc["VpcId"])

        logger.info(f"CONFIGURING VPC FLOW LOGS ON VPC-IDS: {vpc_id_list}")

        if not vpc_id_list:
            return {"success": True, "message": "No VPCs found in region"}

        response = ec2_client.create_flow_logs(
            ResourceIds=vpc_id_list,
            ResourceType="VPC",
            TrafficType="ALL",
            LogDestinationType="s3",
            LogDestination=f"arn:aws:s3:::{cyngular_bucket}",
            TagSpecifications=[
                {
                    "ResourceType": "vpc-flow-log",
                    "Tags": [
                        {"Key": "Name", "Value": "Cyngular-vpc-flowlogs"},
                    ],
                },
            ],
        )

        logger.info(f"[{region} | VPC FLOW LOGS] COMMAND SUCCEEDED.")

        return {
            "success": True,
            "vpc_ids": vpc_id_list,
            "flow_log_ids": response.get("FlowLogIds", [])
        }

    except Exception as e:
        if "FlowLogAlreadyExists" in str(e):
            logger.info(f"[{region} | VPC FLOW LOGS] VPC Flow Logs already exist")
            return {"success": True, "message": "Flow logs already exist"}
        else:
            logger.error(
                f"[{region} | VPC FLOW LOGS] VPC Flow Logs processing failed: {str(e)}"
            )
            return {"success": False, "error": str(e)}


def process_eks_service(
    region: str,
    cyngular_role_arn: str
) -> Dict[str, Any]:
    """Configure EKS access for the region"""
    try:
        logger.info(f"[{region} | EKS] STARTING CONFIGURATION...")

        wanted_cluster_logging_config = {
            "clusterLogging": [{"types": ["audit", "authenticator"], "enabled": True}]
        }

        eks_client = boto3.client("eks", region_name=region)
        clusters = eks_client.list_clusters()["clusters"]

        if not clusters:
            logger.info(f"[{region} | EKS] No EKS clusters found in {region}")
            return {"success": True, "message": "No EKS clusters found"}
        logger.info(
            f"[{region} | EKS] Found {len(clusters)} clusters in region {region}"
        )

        processed_clusters = []
        for cluster_name in clusters:
            try:
                logger.info(f"[{region} | EKS] CONFIGURING CLUSTER: {cluster_name}")

                current_config = eks_client.describe_cluster(name=cluster_name)
                current_logging = current_config.get("cluster", {}).get("logging", {})
                current_types = []

                for log_config in current_logging.get("clusterLogging", []):
                    if log_config.get("enabled", False):
                        current_types.extend(log_config.get("types", []))

                wanted_types = ["audit", "authenticator"]
                if all(log_type in current_types for log_type in wanted_types):
                    logger.info(
                        f"[{region} | EKS] Cluster {cluster_name} already has required logging enabled"
                    )
                else:
                    logger.info(
                        f"[{region} | EKS] Updating logging configuration for {cluster_name}"
                    )

                    merged_types = list(set(current_types + wanted_types))
                    # Override / Merge logging config
                    wanted_cluster_logging_config = {
                        "clusterLogging": [{"types": merged_types, "enabled": True}]
                    }

                    try:
                        eks_client.update_cluster_config(
                            name=cluster_name, logging=wanted_cluster_logging_config
                        )
                        logger.info(
                            f"[{region} | EKS] Successfully updated logging for {cluster_name}"
                        )
                    except ClientError as e:
                        if "No changes needed for the logging config provided" in str(
                            e
                        ):
                            logger.info(
                                f"[{region} | EKS] No changes needed for logging config in {cluster_name}"
                            )
                        else:
                            raise e

                if check_access_entry_exists(
                    region, eks_client, cluster_name, cyngular_role_arn
                ):
                    logger.info(
                        f"[{region} | EKS] Access entry already exists for {cluster_name}"
                    )
                else:
                    access_result = create_cyngular_access_entry(
                        region, eks_client, cluster_name, cyngular_role_arn
                    )
                    processed_clusters.append(
                        {
                            "cluster": cluster_name,
                            "logging_enabled": True,
                            "access_entry": access_result,
                        }
                    )

            except Exception as e:
                logger.error(
                    f"[{region} | EKS] Error processing cluster {cluster_name}: {str(e)}"
                )
                processed_clusters.append({"cluster": cluster_name, "error": str(e)})

        return {
            "success": True,
            "processed_clusters": processed_clusters
        }

    except Exception as e:
        logger.error(f"[{region} | EKS] Cluster processing failed: {str(e)}")
        return {"success": False, "error": str(e)}


def process_os_service(region: str) -> Dict[str, Any]:
    """Configure OS internals (auditd) for the region"""
    try:
        logger.info(f"[{region} | OS INTERNALS] STARTING...")

        ec2_client = boto3.client("ec2", region_name=region)
        ssm_client = boto3.client("ssm", region_name=region)

        all_instances = ec2_client.describe_instances()
        instance_ids = []

        for reservation in all_instances["Reservations"]:
            for instance in reservation["Instances"]:
                if instance["State"]["Name"] == "running":
                    instance_ids.append(instance["InstanceId"])

        if not instance_ids:
            logger.info(
                f"[{region} | OS INTERNALS] No running instances found in {region}"
            )
            return {"success": True, "message": "No running instances found"}

        auditd_rules = ""
        with open("auditd_rules", "r") as f:
            auditd_rules = f.read()

        processed_instances = []
        for instance_id in instance_ids:
            try:
                logger.info(
                    f"[{region} | OS INTERNALS] CONFIGURING INSTANCE-ID: {instance_id}"
                )
                response = ssm_client.send_command(
                    InstanceIds=[instance_id],
                    DocumentName="AWS-RunShellScript",
                    Parameters={
                        "commands": [
                            "apt-get update -y",
                            "apt-get install -y auditd",
                            "systemctl kill auditd.service",
                            "sleep 10",
                            f'echo {auditd_rules} | base64 --decode > "/etc/audit/rules.d/audit.rules"',
                            "sleep 10",
                            "systemctl start auditd.service",
                        ]
                    },
                )
                logger.info(
                    f"[{region} | OS INTERNALS | {instance_id}] COMMAND SUCCEEDED"
                )
                processed_instances.append(
                    {
                        "instance_id": instance_id,
                        "command_id": response["Command"]["CommandId"],
                        "status": "sent",
                    }
                )

            except ClientError as e:
                if e.response["Error"][
                    "Code"
                ] == "InvalidInstanceId" and "not in a valid state for account" in str(
                    e
                ):
                    logger.warning(
                        f"[{region} | OS INTERNALS | {instance_id}] COMMAND FAILED: {str(e)}"
                    )
                    processed_instances.append(
                        {"instance_id": instance_id, "error": str(e)}
                    )

                elif e.response["Error"]["Code"] == "UnsupportedPlatformType":
                    logger.warning(
                        f"[{region} | OS INTERNALS | {instance_id}] COMMAND FAILED: {str(e)}"
                    )
                    processed_instances.append(
                        {"instance_id": instance_id, "error": str(e)}
                    )

            except Exception as e:
                logger.error(
                    f"[{region} | OS INTERNALS | {instance_id}] COMMAND FAILED: {str(e)}"
                )
                processed_instances.append(
                    {"instance_id": instance_id, "error": str(e)}
                )

        return {"success": True, "processed_instances": processed_instances}

    except ClientError as e:
        logger.error(
            f"[{region} | OS INTERNALS | ClientError] OS processing failed: {str(e)}"
        )
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(
            f"[{region} | OS INTERNALS | Exception] OS processing failed: {str(e)}"
        )
        return {"success": False, "error": str(e)}
