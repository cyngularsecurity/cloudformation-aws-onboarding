import boto3
import traceback
import os
import logging

def vpcflowlogs(cur_region_name):
    try:
        logging.info('STARTING VPCFLOWLOGS...')

        vpc_id_list = []
        ec2 = boto3.client('ec2', region_name=cur_region_name)
                            
        vpc_list = ec2.describe_vpcs()
        if "Vpcs" in vpc_list:                  
            for vpc in vpc_list["Vpcs"]:
                vpc_id_list.append(vpc["VpcId"])

        logging.info(f'CONFIGURING VPCFLOWLOGS ON VPC-IDS: {vpc_id_list}')
        response = ec2.create_flow_logs(
            ResourceIds=vpc_id_list,
            ResourceType='VPC',
            TrafficType='ALL',
            LogDestinationType='s3',
            LogDestination='${CyngularS3Bucket.Arn}',
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
        logging.info(f'COMMAND SUCCEEDED.')

    except Exception as e:
        if 'FlowLogAlreadyExists' in str(e):
            pass
        else:
            logging.critical(str(e))

def cyngular_function(event, context):
    
    try:
        logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logging.info('STRATING CYNGULARS FUNCTION...')
        func_lst = [vpcflowlogs]
        ec2_client = boto3.client('ec2')
        events_client=boto3.client('events')
        regions = os.environ['LAMBDA_REGIONS'].split(' ')

        for cur_region_name in regions:
            logging.info(f'AWS REGION: {cur_region_name}')
            for func in func_lst:
                try:
                    func(cur_region_name)
                except Exception as e:
                    logging.critical(str(e))
        logging.info('ACTIVATING EVENT BUS RULE')
        response = events_client.put_rule(
            Name='cyngular-lambda-create-vpcflowlogs-rule',
            ScheduleExpression="cron(0 8 * * ? *)",
            State='ENABLED',
            Description='LambdaBScheduledRule',
            EventBusName='default'
        )
        logging.info('DONE!')

    except Exception as e:
        logging.critical(str(e))
