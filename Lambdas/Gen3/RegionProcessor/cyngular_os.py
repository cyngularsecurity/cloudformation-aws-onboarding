import boto3
import logging
from typing import Dict, Any
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class OSProcessor:
    def __init__(self, service_info: Dict[str, Any]):
        self.region = service_info['region']
        self.client_name = service_info['client_name']
        self.cyngular_bucket = service_info['cyngular_bucket']
        self.cyngular_role_arn = service_info['cyngular_role_arn']
        
        # Initialize AWS clients for the specific region
        self.ec2_client = boto3.client('ec2', region_name=self.region)
        self.ssm_client = boto3.client('ssm', region_name=self.region)

    @staticmethod
    def process_os_service(service_info: Dict[str, Any]) -> Dict[str, Any]:
        """Configure OS internals (auditd) for the region"""
        # Create an instance of OSProcessor with the service info
        processor = OSProcessor(service_info)
        return processor._process_os_service()
        
    def _process_os_service(self) -> Dict[str, Any]:
        """Internal method to configure OS internals (auditd) for the region"""
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
                    logger.info(f'[{self.region} | OS | {instance_id}] COMMAND SUCCEEDED')
                    processed_instances.append({
                        'instance_id': instance_id,
                        'command_id': response['Command']['CommandId'],
                        'status': 'sent'
                    })
                except Exception as e:
                    logger.error(f'[{self.region} | OS | {instance_id}] COMMAND FAILED: {str(e)}')
                    processed_instances.append({
                        'instance_id': instance_id,
                        'error': str(e)
                    })

            return {
                'success': True,
                'processed_instances': processed_instances
            }

        except ClientError as e:
            logger.error(f'[{self.region} | OS | ClientError] OS processing failed: {str(e)}')
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f'[{self.region} | OS | Exception] OS processing failed: {str(e)}')
            return {'success': False, 'error': str(e)}
