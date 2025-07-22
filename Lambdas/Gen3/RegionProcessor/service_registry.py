
from dataclasses import dataclass
from typing import Callable, List
from utils import process_dns_service, process_vfl_service, process_eks_service, process_os_service

@dataclass
class ServiceConfig:
    handler: Callable
    required_params: List[str]
    batch_capable: bool = False

SERVICE_REGISTRY = {
    'dns': ServiceConfig(process_dns_service, ['region', 'cyngular_bucket', 'enable_param']),
    'vfl': ServiceConfig(process_vfl_service, ['region', 'cyngular_bucket', 'enable_param']),
    'eks': ServiceConfig(process_eks_service, ['region', 'cyngular_role_arn', 'enable_param', 'cyngular_bucket']),
    'os': ServiceConfig(process_os_service, ['region'])
}