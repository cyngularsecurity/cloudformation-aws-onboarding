import boto3
import json
import logging
import os
import uuid
import traceback
from typing import Dict, Any, List
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class RegionProcessor:
    def __init__(self, region: str, client_name: str, cyngular_bucket: str, cyngular_role_arn: str):
        self.region = region
        self.client_name = client_name
        self.cyngular_bucket = cyngular_bucket
        self.cyngular_role_arn = cyngular_role_arn
        
        # Initialize AWS clients for the specific region
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.r53_client = boto3.client('route53resolver', region_name=region)
        self.ssm_client = boto3.client('ssm', region_name=region)
        self.eks_client = boto3.client('eks', region_name=region)

    def process_dns_service(self) -> Dict[str, Any]:
        """Configure DNS logging for the region"""
        try:
            logger.info(f'STARTING DNS LOGS IN {self.region}...')
            
            # Check for existing Query Log Config
            region_query_log_configs = self.r53_client.list_resolver_query_log_configs()['ResolverQueryLogConfigs']
            cyngular_resolver_id = ''
            
            for config in region_query_log_configs:
                if config.get('Name') == 'cyngular_dns':
                    cyngular_resolver_id = config['Id']
                    logger.info(f'EXISTING QLC FOUND: {cyngular_resolver_id}')
                    break

            # Create QLC if not found
            if not cyngular_resolver_id:
                logger.info('NO EXISTING QLC FOUND - CREATING NEW')
                try:
                    response = self.r53_client.create_resolver_query_log_config(
                        Name='cyngular_dns',
                        DestinationArn=f"arn:aws:s3:::{self.cyngular_bucket}",
                        CreatorRequestId=str(uuid.uuid4()),
                        Tags=[{'Key': 'Purpose', 'Value': 'DNS Logging'}]
                    )
                    cyngular_resolver_id = response['ResolverQueryLogConfig']['Id']
                    logger.info(f'NEW QLC CREATED: {cyngular_resolver_id}')
                except Exception as e:
                    logger.error(f'QLC CREATION FAILED: {str(e)}')
                    return {'success': False, 'error': str(e)}

            # Associate with all VPCs
            vpc_list = self.ec2_client.describe_vpcs().get('Vpcs', [])
            logger.info(f'FOUND {len(vpc_list)} VPCS TO PROCESS')
            
            processed_vpcs = []
            for vpc in vpc_list:
                vpc_id = vpc['VpcId']
                try:
                    logger.info(f'ASSOCIATING {vpc_id} WITH QLC')
                    self.r53_client.associate_resolver_query_log_config(
                        ResolverQueryLogConfigId=cyngular_resolver_id,
                        ResourceId=vpc_id
                    )
                    logger.info(f'SUCCESS: {vpc_id} associated')
                    processed_vpcs.append(vpc_id)
                except Exception as e:
                    if 'ResourceInUseException' in str(e) or 'already associated' in str(e):
                        logger.info(f'Already associated: {vpc_id}')
                        processed_vpcs.append(vpc_id)
                    else:
                        logger.error(f'Association failed for {vpc_id}: {str(e)}')

            return {
                'success': True,
                'resolver_id': cyngular_resolver_id,
                'processed_vpcs': processed_vpcs
            }

        except Exception as e:
            logger.error(f'DNS processing failed: {str(e)}')
            return {'success': False, 'error': str(e)}

    def process_vfl_service(self) -> Dict[str, Any]:
        """Configure VPC Flow Logs for the region"""
        try:
            logger.info(f'STARTING VPC FLOW LOGS IN {self.region}...')

            vpc_list = self.ec2_client.describe_vpcs()
            vpc_id_list = []
            
            if "Vpcs" in vpc_list:
                for vpc in vpc_list["Vpcs"]:
                    vpc_id_list.append(vpc["VpcId"])

            logger.info(f'CONFIGURING VPC FLOW LOGS ON VPC-IDS: {vpc_id_list}')
            
            if not vpc_id_list:
                return {'success': True, 'message': 'No VPCs found in region'}

            response = self.ec2_client.create_flow_logs(
                ResourceIds=vpc_id_list,
                ResourceType='VPC',
                TrafficType='ALL',
                LogDestinationType='s3',
                LogDestination=f"arn:aws:s3:::{self.cyngular_bucket}",
                TagSpecifications=[
                    {
                        'ResourceType': 'vpc-flow-log',
                        'Tags': [
                            {
                                'Key': 'Name',
                                'Value': 'Cyngular-vpc-flowlogs'
                            },
                        ]
                    },
                ]
            )
            
            logger.info(f'VPC FLOW LOGS COMMAND SUCCEEDED.')
            return {
                'success': True,
                'vpc_ids': vpc_id_list,
                'flow_log_ids': response.get('FlowLogIds', [])
            }

        except Exception as e:
            if 'FlowLogAlreadyExists' in str(e):
                logger.info('VPC Flow Logs already exist')
                return {'success': True, 'message': 'Flow logs already exist'}
            else:
                logger.error(f'VPC Flow Logs processing failed: {str(e)}')
                return {'success': False, 'error': str(e)}

    def check_access_entry_exists(self, cluster_name: str, role_arn: str) -> bool:
        """Check if EKS access entry exists for the role"""
        try:
            response = self.eks_client.list_access_entries(clusterName=cluster_name)
            if 'accessEntries' in response:
                return role_arn in response['accessEntries']
            return False
        except self.eks_client.exceptions.ResourceNotFoundException:
            logger.error(f'Cluster {cluster_name} not found')
            return False
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidRequestException' and 'authentication mode' in str(e):
                logger.warning(f'Cluster {cluster_name} has incompatible authentication mode for access entries')
                return False
        except Exception as e:
            logger.error(f'Error checking access entries: {str(e)}')
            return False

    def create_access_entry(self, cluster_name: str, role_arn: str) -> Dict[str, Any]:
        """Create EKS access entry for the role"""
        try:
            cluster_info = self.eks_client.describe_cluster(name=cluster_name)
            auth_mode = cluster_info['cluster'].get('accessConfig', {}).get('authenticationMode', 'CONFIG_MAP')
            
            if auth_mode not in ['API', 'API_AND_CONFIG_MAP']:
                logger.warning(f'Skipping access entry creation for cluster {cluster_name} - incompatible authentication mode: {auth_mode}')
                return {'success': False, 'reason': 'Incompatible authentication mode'}

            if self.check_access_entry_exists(cluster_name, role_arn):
                logger.info(f'Access entry already exists for {cluster_name}')
                return {'success': True, 'message': 'Access entry already exists'}

            # Create access entry
            self.eks_client.create_access_entry(
                clusterName=cluster_name,
                principalArn=role_arn,
                type='STANDARD'
            )

            # Associate access policy
            self.eks_client.associate_access_policy(
                clusterName=cluster_name,
                principalArn=role_arn,
                policyArn='arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy',
                accessScope={'type': 'cluster'}
            )

            logger.info(f'Successfully created access entry for {cluster_name}')
            return {'success': True, 'cluster': cluster_name}

        except Exception as e:
            logger.error(f'Failed to create access entry for {cluster_name}: {str(e)}')
            return {'success': False, 'error': str(e), 'cluster': cluster_name}

    def process_eks_service(self) -> Dict[str, Any]:
        """Configure EKS access for the region"""
        try:
            logger.info(f'STARTING EKS CONFIGURATION IN {self.region}...')
            
            # List all EKS clusters
            clusters_response = self.eks_client.list_clusters()
            clusters = clusters_response.get('clusters', [])
            
            if not clusters:
                logger.info(f'No EKS clusters found in {self.region}')
                return {'success': True, 'message': 'No EKS clusters found'}

            processed_clusters = []
            for cluster_name in clusters:
                try:
                    # Enable logging
                    self.eks_client.update_cluster_config(
                        name=cluster_name,
                        logging={
                            'enable': [
                                {
                                    'types': ['audit', 'authenticator', 'api', 'controllerManager', 'scheduler']
                                }
                            ]
                        }
                    )
                    
                    # Create access entry
                    access_result = self.create_access_entry(cluster_name, self.cyngular_role_arn)
                    processed_clusters.append({
                        'cluster': cluster_name,
                        'logging_enabled': True,
                        'access_entry': access_result
                    })
                    
                except Exception as e:
                    logger.error(f'Error processing cluster {cluster_name}: {str(e)}')
                    processed_clusters.append({
                        'cluster': cluster_name,
                        'error': str(e)
                    })

            return {
                'success': True,
                'processed_clusters': processed_clusters
            }

        except Exception as e:
            logger.error(f'EKS processing failed: {str(e)}')
            return {'success': False, 'error': str(e)}

    def process_os_service(self) -> Dict[str, Any]:
        """Configure OS internals (auditd) for the region"""
        try:
            logger.info(f'STARTING OS INTERNALS IN {self.region}...')
            
            all_instances = self.ec2_client.describe_instances()
            instance_ids = []
            
            for reservation in all_instances['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] == 'running':
                        instance_ids.append(instance['InstanceId'])

            if not instance_ids:
                logger.info(f'No running instances found in {self.region}')
                return {'success': True, 'message': 'No running instances found'}

            # Base64 encoded auditd rules (same as original)
            auditd_rules = 'IyAgICAgIF9fXyAgICAgICAgICAgICBfX18gX18gICAgICBfXwojICAgICAvICAgfCBfXyAgX19fX19fLyAoXykgL19fX19fLyAvCiMgICAgLyAvfCB8LyAvIC8gLyBfXyAgLyAvIF9fLyBfXyAgLwojICAgLyBfX18gLyAvXy8gLyAvXy8gLyAvIC9fLyAvXy8gLwojICAvXy8gIHxfXF9fLF8vXF9fLF8vXy9cX18vXF9fLF8vCiMKIyBMaW51eCBBdWRpdCBEYWVtb24gLSBCZXN0IFByYWN0aWNlIENvbmZpZ3VyYXRpb24KIyAvZXRjL2F1ZGl0L2F1ZGl0LnJ1bGVzCiMKIyBDb21waWxlZCBieSBDeW5ndWxhciBTZWN1cml0eQojCgojIFJlbW92ZSBhbnkgZXhpc3RpbmcgcnVsZXMKLUQKCiMgQnVmZmVyIFNpemUKIyMgRmVlbCBmcmVlIHRvIGluY3JlYXNlIHRoaXMgaWYgdGhlIG1hY2hpbmUgcGFuaWMncwotYiA4MTkyCgojIEZhaWx1cmUgTW9kZQojIyBQb3NzaWJsZSB2YWx1ZXM6IDAgKHNpbGVudCksIDEgKHByaW50aywgcHJpbnQgYSBmYWlsdXJlIG1lc3NhZ2UpLCAyIChwYW5pYywgaGFsdCB0aGUgc3lzdGVtKQotZiAxCgojIElnbm9yZSBlcnJvcnMKIyMgZS5nLiBjYXVzZWQgYnkgdXNlcnMgb3IgZmlsZXMgbm90IGZvdW5kIGluIHRoZSBsb2NhbCBlbnZpcm9ubWVudAotaQoKIyBTZWxmIEF1ZGl0aW5nIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLQoKIyMgQXVkaXQgdGhlIGF1ZGl0IGxvZ3MKIyMjIFN1Y2Nlc3NmdWwgYW5kIHVuc3VjY2Vzc2Z1bCBhdHRlbXB0cyB0byByZWFkIGluZm9ybWF0aW9uIGZyb20gdGhlIGF1ZGl0IHJlY29yZHMKLXcgL3Zhci9sb2cvYXVkaXQvIC1rIGF1ZGl0bG9nCgojIyBBdWRpdGQgY29uZmlndXJhdGlvbgojIyMgTW9kaWZpY2F0aW9ucyB0byBhdWRpdCBjb25maWd1cmF0aW9uIHRoYXQgb2NjdXIgd2hpbGUgdGhlIGF1ZGl0IGNvbGxlY3Rpb24gZnVuY3Rpb25zIGFyZSBvcGVyYXRpbmcKLXcgL2V0Yy9hdWRpdC8gLXAgd2EgLWsgYXVkaXRjb25maWcKLXcgL2V0Yy9saWJhdWRpdC5jb25mIC1wIHdhIC1rIGF1ZGl0Y29uZmlnCi13IC9ldGMvYXVkaXNwLyAtcCB3YSAtayBhdWRpc3Bjb25maWcKCiMjIE1vbml0b3IgZm9yIHVzZSBvZiBhdWRpdCBtYW5hZ2VtZW50IHRvb2xzCi13IC9zYmluL2F1ZGl0Y3RsIC1wIHggLWsgYXVkaXR0b29scwotdyAvc2Jpbi9hdWRpdGQgLXAgeCAtayBhdWRpdHRvb2xzCi13IC91c3Ivc2Jpbi9hdWdlbnJ1bGVzIC1wIHggLWsgYXVkaXR0b29scw=='

            processed_instances = []
            for instance_id in instance_ids:
                try:
                    logger.info(f'CONFIGURING OS INTERNALS ON INSTANCE-ID: {instance_id}')
                    response = self.ssm_client.send_command(
                        InstanceIds=[instance_id],
                        DocumentName="AWS-RunShellScript",
                        Parameters={
                            'commands': [
                                'apt-get update -y',
                                'apt-get install -y auditd',
                                'systemctl kill auditd.service',
                                'sleep 10',
                                f'echo {auditd_rules} | base64 --decode > "/etc/audit/rules.d/audit.rules"',
                                'sleep 10',
                                'systemctl start auditd.service'
                            ]
                        }
                    )
                    logger.info(f'COMMAND SUCCEEDED for {instance_id}')
                    processed_instances.append({
                        'instance_id': instance_id,
                        'command_id': response['Command']['CommandId'],
                        'status': 'sent'
                    })
                except Exception as e:
                    logger.error(f'Error processing instance {instance_id}: {str(e)}')
                    processed_instances.append({
                        'instance_id': instance_id,
                        'error': str(e)
                    })

            return {
                'success': True,
                'processed_instances': processed_instances
            }

        except Exception as e:
            logger.error(f'OS processing failed: {str(e)}')
            return {'success': False, 'error': str(e)}

    def process_service(self, service: str) -> Dict[str, Any]:
        """Process a specific service for the region"""
        service_map = {
            'dns': self.process_dns_service,
            'vfl': self.process_vfl_service,
            'eks': self.process_eks_service,
            'os': self.process_os_service
        }
        
        if service not in service_map:
            return {'success': False, 'error': f'Unknown service: {service}'}
        
        try:
            result = service_map[service]()
            result['service'] = service
            result['region'] = self.region
            return result
        except Exception as e:
            logger.error(f'Error processing service {service}: {str(e)}')
            return {
                'success': False,
                'service': service,
                'region': self.region,
                'error': str(e)
            }

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main lambda handler"""
    logger.info(f"Received event: {json.dumps(event)}")

    # Extract parameters from event
    service = event.get('service')
    region = event.get('region')
    client_name = event.get('client_name')
    cyngular_bucket = event.get('cyngular_bucket')
    cyngular_role_arn = event.get('cyngular_role_arn')

    # Validate required parameters
    if not all([service, region, client_name, cyngular_bucket]):
        return {
            'statusCode': 400,
            'body': json.dumps({
                'success': False,
                'error': 'Missing required parameters: service, region, client_name, cyngular_bucket'
            })
        }
    
    try:
        # Initialize region processor
        processor = RegionProcessor(region, client_name, cyngular_bucket, cyngular_role_arn)
        
        # Process the service
        result = processor.process_service(service)
        
        logger.info(f"Processing complete: {result}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Error in lambda handler: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            })
        }