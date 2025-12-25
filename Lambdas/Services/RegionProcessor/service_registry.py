from dataclasses import dataclass
from typing import Callable, List
from services import (
    process_dns_service,
    process_vfl_service,
    process_eks_service,
    process_os_service,
)


@dataclass
class ServiceConfig:
    handler: Callable
    required_params: List[str]
    batch_capable: bool = False


SERVICE_REGISTRY = {
    "dns": ServiceConfig(
        handler=process_dns_service,
        required_params=["region", "cyngular_bucket"],
    ),
    "vfl": ServiceConfig(
        handler=process_vfl_service,
        required_params=["region", "cyngular_bucket"],
    ),
    "eks": ServiceConfig(
        handler=process_eks_service,
        required_params=["region", "cyngular_role_arn"],
    ),
    "os": ServiceConfig(
        handler=process_os_service,
        required_params=["region"]
    ),
}
