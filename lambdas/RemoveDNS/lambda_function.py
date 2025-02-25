import boto3
import os
import logging

def dnslogs(curr_region):
    try:
        r_53_client = boto3.client('route53resolver', region_name=curr_region)
        ec2_client = boto3.client('ec2', region_name=curr_region)
        
        region_query_log_configs = r_53_client.list_resolver_query_log_configs()['ResolverQueryLogConfigs']
        cyngular_resolver_id = ''
        
        for region_query_log_config in region_query_log_configs:
            try:
                if region_query_log_config['Name'] == 'cyngular_dns':
                    cyngular_resolver_id = region_query_log_config['Id']
                    break
            except:
                pass

        if cyngular_resolver_id:
            vpc_list = ec2_client.describe_vpcs()
            if "Vpcs" in vpc_list:                  
                for vpc in vpc_list["Vpcs"]:
                    try:
                        vpc_id = vpc["VpcId"]
                        logging.info (f'DELETING CONFIGURATION OF DNSLOGS ON VPC-ID: {vpc_id}')
                        resp = r_53_client.disassociate_resolver_query_log_config(ResolverQueryLogConfigId = cyngular_resolver_id, ResourceId = vpc_id )
                        logging.info(f'COMMAND SUCCEEDED.')
                    except Exception as e:
                        if "association doesn't exist" in str(e):
                            logging.critical(f'{vpc_id} - ResolverWasNotAssociated')
                        else:
                            logging.critical(str(e))
    except Exception as e:
        logging.critical(str(e))

def cyngular_function(event, context):
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    try:
        logger.info ('STRATING CYNGULARS FUNCTION...')
        logger.info(f'DELETING DNSLOGS...')
        events_client = boto3.client('events')
        REGIONS = os.environ['CLIENT_REGIONS']

        for curr_region in REGIONS.split(' '):
            logger.info(f'AWS REGION: {curr_region}')
            try:
                dnslogs(curr_region)
            except Exception as e:
                logger.critical(str(e))
        try:
            logger.info('DEACTIVATING EVENT BUS RULE')
            events_client.disable_rule(
                Name='cyngular-lambda-config-dns-rule',
                EventBusName='default'
            )
            logger.info('DONE!')
        except events_client.exceptions.ResourceNotFoundException:
            logger.warning('Rule cyngular-lambda-config-dns-rule does not exist on EventBus default. Continuing execution.')
        except Exception as e:
            logger.critical(str(e))

    except Exception as e:
        logger.critical(str(e))