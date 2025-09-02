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
