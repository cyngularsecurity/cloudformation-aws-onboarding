import boto3
import traceback
import os
import logging

def dnslogs(curr_region):
    logging.info(f'STARTING DNSLOGS...')
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
                        logging.info(f'CONFIGURING DNSLOGS ON VPC-ID: {vpc_id}')
                        resp = r_53_client.associate_resolver_query_log_config(ResolverQueryLogConfigId = cyngular_resolver_id, ResourceId = vpc_id )
                        logging.info(f'COMMAND SUCCEEDED.')
                    except Exception as e:
                        if not 'already associated' in str(e):
                            logging.critical(str(e))
    except Exception as e:
        logging.critical(str(e))

def cyngular_function(event, context):
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.info('STRATING CYNGULARS FUNCTION...')

    LAMBDA_NAME=context.function_name
    REGIONS=os.environ['CLIENT_REGIONS']
    try:
        if os.environ.get('FIRST_RUN') == 'true':
            logger.info('First run detected. Updating EventBridge rule schedule.')
            try:
                lambda_client = boto3.client('lambda')
                events_client = boto3.client('events')
                response = events_client.put_rule(
                    Name = f"{LAMBDA_NAME}-rule",
                    State = 'ENABLED',
                    ScheduleExpression = os.environ['FINAL_CRON'],
                    Description = 'LambdaDNS | Scheduled to run hourly',
                    EventBusName = 'default'
                )
                logger.info('Successfully updated the EventBridge rule: %s', response)
                response = lambda_client.update_function_configuration(
                    FunctionName=LAMBDA_NAME,
                    Environment={'Variables': {"FIRST_RUN": "false", "CLIENT_REGIONS": REGIONS}}
                )
                logger.info('Successfully updated the function configuration: %s', response)
            except Exception as e:
                logger.critical('Error updating the EventBridge rule: %s', str(e))
                raise

        logger.info('STARTING DNSLOGS...')                    
        for curr_region in REGIONS.split(' '):
            logging.info(f'AWS REGION: {curr_region}')
            try:
                dnslogs(curr_region)
            except Exception as e:
                logging.critical(str(e))
        logging.info('DONE!')

    except Exception as e:
        logging.critical(str(e))
