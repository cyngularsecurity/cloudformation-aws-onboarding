import boto3
import logging
from typing import Dict, Any
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def check_access_entry_exists(
    region: str, eks_client, cluster_name: str, role_arn: str
) -> bool:
    """Check if EKS access entry exists for the role"""
    try:
        response = eks_client.list_access_entries(clusterName=cluster_name)
        if "accessEntries" in response:
            return role_arn in response["accessEntries"]
        return False
    except eks_client.exceptions.ResourceNotFoundException:
        logger.error(f"[{region} | EKS] Cluster {cluster_name} not found")
        return False

    except ClientError as e:
        if e.response["Error"][
            "Code"
        ] == "InvalidRequestException" and "authentication mode" in str(e):
            logger.warning(
                f"[{region} | EKS] Cluster {cluster_name} has incompatible authentication mode for access entries"
            )
            return False
    except Exception as e:
        logger.error(f"[{region} | EKS] Error checking access entries: {str(e)}")
        return False


def create_cyngular_access_entry(
    region: str, eks_client, cluster_name: str, role_arn: str
) -> Dict[str, Any]:
    """Create EKS access entry for the role"""
    try:
        cluster_info = eks_client.describe_cluster(name=cluster_name)
        auth_mode = (
            cluster_info["cluster"]
            .get("accessConfig", {})
            .get("authenticationMode", "CONFIG_MAP")
        )

        if auth_mode not in ["API", "API_AND_CONFIG_MAP"]:
            logger.warning(
                f"[{region} | EKS] Skipping access entry creation for cluster {cluster_name} - incompatible authentication mode: {auth_mode}"
            )
            return {"success": False, "reason": "Incompatible authentication mode"}

        eks_client.create_access_entry(
            clusterName=cluster_name, principalArn=role_arn, type="STANDARD"
        )

        eks_client.associate_access_policy(
            clusterName=cluster_name,
            principalArn=role_arn,
            policyArn="arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy",
            accessScope={"type": "cluster"},
        )

        logger.info(
            f"[{region} | EKS] Successfully created access entry for {cluster_name}"
        )
        return {"success": True, "cluster": cluster_name}

    except eks_client.exceptions.ResourceNotFoundException as e_not_found:
        logger.error(
            f"[{region} | EKS] Cluster {cluster_name} not found -- {str(e_not_found)}"
        )
        return {"success": False, "error": str(e_not_found), "cluster": cluster_name}
    except eks_client.exceptions.AccessDeniedException as e_access_denied:
        logger.error(
            f"[{region} | EKS] Access denied when creating access entry for cluster {cluster_name} -- {str(e_access_denied)}"
        )
        return {
            "success": False,
            "error": str(e_access_denied),
            "cluster": cluster_name,
        }
    except Exception as e:
        logger.error(
            f"[{region} | EKS] Failed to create access entry for {cluster_name}: {str(e)}"
        )
        return {"success": False, "error": str(e), "cluster": cluster_name}


def tag_cyngular_bucket(bucket_name: str, service_tags: dict) -> Dict[str, Any]:
    """
    Add service-specific tags to the Cyngular S3 bucket

    Args:
        bucket_name: Name of the S3 bucket to tag
        service_tags: Dictionary of tags to add (e.g., {'cyngular-dnslogs': 'true'})

    Returns:
        Dictionary with success status and details
    """
    try:
        logger.info(f"Tagging bucket {bucket_name} with tags: {service_tags}")

        s3_client = boto3.client("s3")

        # Get existing bucket tags
        try:
            response = s3_client.get_bucket_tagging(Bucket=bucket_name)
            existing_tags = {
                tag["Key"]: tag["Value"] for tag in response.get("TagSet", [])
            }
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchTagSet':
                existing_tags = {}
            else:
                raise e
        except Exception as e:
            logger.warning(
                f"Could not retrieve existing tags for {bucket_name}: {str(e)}"
            )
            existing_tags = {}

        # Merge existing tags with new service tags
        updated_tags = existing_tags.copy()
        updated_tags.update(service_tags)

        # Convert back to TagSet format
        tag_set = [{"Key": k, "Value": v} for k, v in updated_tags.items()]

        # Apply updated tags to bucket
        s3_client.put_bucket_tagging(Bucket=bucket_name, Tagging={"TagSet": tag_set})

        logger.info(f"Successfully tagged bucket {bucket_name} with service tags")
        return {
            "success": True,
            "bucket": bucket_name,
            "applied_tags": service_tags,
            "all_tags": updated_tags,
        }

    except Exception as e:
        logger.error(f"Failed to tag bucket {bucket_name}: {str(e)}")
        return {"success": False, "error": str(e)}


def tag_custom_bucket_if_specified(
    enable_param: str, service_tag_key: str, default_bucket: str
) -> Dict[str, Any]:
    """
    Tag custom bucket if specified in enable parameter, otherwise tag default bucket

    Args:
        enable_param: The service enable parameter (true/false/custom-bucket-name)
        service_tag_key: The tag key to apply (e.g., 'cyngular-dnslogs')
        default_bucket: Default Cyngular bucket name

    Returns:
        Dictionary with success status and details
    """
    try:
        # Determine which bucket to tag
        if enable_param.lower() == "true":
            bucket_to_tag = default_bucket
            logger.info(f"Service enabled with default bucket: {bucket_to_tag}")
        elif enable_param.lower() == "false":
            logger.info("Service disabled, skipping bucket tagging")
            return {"success": True, "message": "Service disabled, no tagging needed"}
        else:
            # Custom bucket name provided
            bucket_to_tag = enable_param
            logger.info(f"Service enabled with custom bucket: {bucket_to_tag}")

        # Apply the service tag
        service_tags = {service_tag_key: "true"}
        return tag_cyngular_bucket(bucket_to_tag, service_tags)

    except Exception as e:
        logger.error(
            f"Failed to process bucket tagging for {service_tag_key}: {str(e)}"
        )
        return {"success": False, "error": str(e)}
