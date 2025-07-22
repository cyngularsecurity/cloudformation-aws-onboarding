import boto3
import os
import logging

def vpcflowlogs(curr_region, bucket_name):
    try:
        logging.info('STARTING VPCFLOWLOGS...')

        ec2_client = boto3.client('ec2', region_name=curr_region)
        vpc_list = ec2_client.describe_vpcs()

        vpc_id_list = []
        if "Vpcs" in vpc_list:                  
            for vpc in vpc_list["Vpcs"]:
                vpc_id_list.append(vpc["VpcId"])

        logging.info(f'CONFIGURING VPCFLOWLOGS ON VPC-IDS: {vpc_id_list}')
        ec2_client.create_flow_logs(
            ResourceIds=vpc_id_list,
            ResourceType='VPC',
            TrafficType='ALL',
            LogDestinationType='s3',
            LogDestination=f"arn:aws:s3:::{bucket_name}",
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
        logging.info('COMMAND SUCCEEDED.')

    except Exception as e:
        if 'FlowLogAlreadyExists' in str(e):
            pass
        else:
            logging.critical(str(e))

def cyngular_function(event, context):
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.info('STRATING CYNGULARS FUNCTION...')

    LAMBDA_NAME = context.function_name
    REGIONS = os.environ['CLIENT_REGIONS']
    bucket_name = os.environ['CYNGULAR_BUCKET']
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
                    Description = 'LambdaVFL | Scheduled to run hourly',
                    EventBusName = 'default'
                )
                logger.info('Successfully updated the EventBridge rule: %s', response)
                response = lambda_client.update_function_configuration(
                    FunctionName=LAMBDA_NAME,
                    Environment={'Variables': {"FIRST_RUN": "false", "CLIENT_REGIONS": REGIONS, "CYNGULAR_BUCKET": bucket_name}}
                )
                logger.info('Successfully updated the function configuration: %s', response)
            except Exception as e:
                logger.critical('Error updating the EventBridge rule: %s', str(e))
                raise

        logger.info('STARTING VPCFLOWLOGS...')
        for curr_region in REGIONS.split(' '):
            logging.info(f'AWS REGION: {curr_region}')
            try:
                vpcflowlogs(curr_region, bucket_name)
            except Exception as e:
                logging.critical(str(e))
        logging.info('DONE!')

    except Exception as e:
        logging.critical(str(e))
