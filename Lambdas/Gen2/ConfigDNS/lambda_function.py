import boto3
import os
import logging

import uuid  # Added for unique CreatorRequestId

def dnslogs(curr_region, bucket_name):
    logging.info(f'STARTING DNSLOGS IN {curr_region}...')
    try:
        r_53_client = boto3.client('route53resolver', region_name=curr_region)
        ec2_client = boto3.client('ec2', region_name=curr_region)
        
        # Check for existing QLC
        region_query_log_configs = r_53_client.list_resolver_query_log_configs()['ResolverQueryLogConfigs']
        cyngular_resolver_id = ''
        
        for config in region_query_log_configs:
            if config.get('Name') == 'cyngular_dns':
                cyngular_resolver_id = config['Id']
                logging.info(f'EXISTING QLC FOUND: {cyngular_resolver_id}')
                break

        # Create QLC if not found
        if not cyngular_resolver_id:
            logging.info('NO EXISTING QLC FOUND - CREATING NEW')
            try:
                response = r_53_client.create_resolver_query_log_config(
                    Name='cyngular_dns',
                    DestinationArn=f"arn:aws:s3:::{bucket_name}",  # REPLACE WITH YOUR BUCKET ARN
                    CreatorRequestId=str(uuid.uuid4()),  # Ensures idempotency
                    Tags=[{'Key': 'Purpose', 'Value': 'DNS Logging'},{'Key': 'Vendor', 'Value': 'Cyngular Security'}]
                )
                cyngular_resolver_id = response['ResolverQueryLogConfig']['Id']
                logging.info(f'NEW QLC CREATED: {cyngular_resolver_id}')
            except Exception as e:
                logging.critical(f'QLC CREATION FAILED: {str(e)}')
                return  # Exit if creation fails

        # Associate with all VPCs
        vpc_list = ec2_client.describe_vpcs().get('Vpcs', [])
        logging.info(f'FOUND {len(vpc_list)} VPCS TO PROCESS')
        
        for vpc in vpc_list:
            vpc_id = vpc['VpcId']
            try:
                logging.info(f'ASSOCIATING {vpc_id} WITH QLC')
                r_53_client.associate_resolver_query_log_config(
                    ResolverQueryLogConfigId=cyngular_resolver_id,
                    ResourceId=vpc_id
                )
                logging.info(f'SUCCESS: {vpc_id} associated')
            except Exception as e:
                if 'InvalidRequestException' in str(e) and "The specified resource is already associated with the specified query logging configuration" in str(e):
                    logging.info(f'1. Already associated: {vpc_id}, with requested config')
                if 'ResourceInUseException' in str(e):
                    logging.info(f'2. Already associated: {vpc_id}')
                else:
                    logging.error(f'3. Association failed for {vpc_id}: {str(e)}')

    except Exception as e:
        logging.critical(f'FATAL ERROR: {str(e)}')
        raise

def cyngular_function(event, context):
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.info('STRATING CYNGULARS FUNCTION...')

    LAMBDA_NAME=context.function_name
    REGIONS=os.environ['CLIENT_REGIONS']
    BUCKET_NAME = os.environ['CYNGULAR_BUCKET']

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
                    Environment={'Variables': {"FIRST_RUN": "false", "CLIENT_REGIONS": REGIONS, "CYNGULAR_BUCKET": BUCKET_NAME}}
                )
                logger.info('Successfully updated the function configuration: %s', response)
            except Exception as e:
                logger.critical('Error updating the EventBridge rule: %s', str(e))
                raise

        logger.info('STARTING DNSLOGS...')                    
        for curr_region in REGIONS.split(' '):
            logging.info(f'AWS REGION: {curr_region}')
            try:
                dnslogs(curr_region, BUCKET_NAME)
            except Exception as e:
                logging.critical(str(e))
        logging.info('DONE!')

    except Exception as e:
        logging.critical(str(e))
