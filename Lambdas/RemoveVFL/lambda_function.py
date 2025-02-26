import boto3
import traceback
import os
import logging

def vpcflowlogs(curr_region):
    try:
        logging.info('DELETING VPCFLOWLOGS...')

        flowlogs_ids_list = []
        ec2_client = boto3.client('ec2', region_name=curr_region)
        
        response = ec2_client.describe_flow_logs(
            Filters=[
                {
                    'Name': 'tag:Name',
                    'Values': [
                        'Cyngular-vpc-flowlogs'
                    ]
                },
            ]
        )
        for flow_log in response['FlowLogs']:
            flowlogs_ids_list.append(flow_log['FlowLogId'])
        
        if not flowlogs_ids_list:
            logging.info('No VPC flow logs to delete.')
            return
        logging.info(f'DELETING THE VPCFLOWLOGS: {flowlogs_ids_list}')
        response = ec2_client.delete_flow_logs(
            FlowLogIds=flowlogs_ids_list
        )
        logging.info(f'COMMAND SUCCEEDED.')
    except Exception as e:
        logging.critical(str(e))
        
def cyngular_function(event, context):
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    try:
        logger.info('STRATING CYNGULARS FUNCTION...')
        events_client = boto3.client('events')
        REGIONS = os.environ['CLIENT_REGIONS']

        for curr_region in REGIONS.split(' '):
            logger.info(f'AWS REGION: {curr_region}')
            try:
                vpcflowlogs(curr_region)
            except Exception as e:
                logger.critical(str(e))

        try:
            logger.info('DEACTIVATING EVENT BUS RULE')
            events_client.disable_rule(
                Name='cyngular-lambda-config-vpcflowlogs-rule',
                EventBusName='default'
            )
            logger.info('DONE!')
        except events_client.exceptions.ResourceNotFoundException:
            logger.warning('Rule cyngular-lambda-config-vpcflowlogs-rule does not exist on EventBus default. Continuing execution.')
        except Exception as e:
            logger.critical(str(e))

    except Exception as e:
        logger.critical(str(e))