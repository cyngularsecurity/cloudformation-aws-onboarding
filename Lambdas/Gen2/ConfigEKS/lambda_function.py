import boto3
import traceback
import os
import logging
from botocore.exceptions import ClientError

def check_access_entry_exists(eks_client, cluster_name, role_arn):
    try:
        response = eks_client.list_access_entries(clusterName=cluster_name)
        if 'accessEntries' in response:
            return role_arn in response['accessEntries']
        return False
    except eks_client.exceptions.ResourceNotFoundException:
        logging.error(f'Cluster {cluster_name} not found')
        return False
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidRequestException' and 'authentication mode' in str(e):
            logging.warning(f'Cluster {cluster_name} has incompatible authentication mode for access entries')
            return False
    except Exception as e:
        logging.error(f'Error checking access entries: {str(e)}')
        return False

def create_access_entry(eks_client, logger, cluster_name, role_arn):
    try:
        try:
            cluster_info = eks_client.describe_cluster(name=cluster_name)
            auth_mode = cluster_info['cluster'].get('accessConfig', {}).get('authenticationMode', 'CONFIG_MAP')
            if auth_mode not in ['API', 'API_AND_CONFIG_MAP']:
                logger.warning(f'Skipping access entry creation for cluster {cluster_name} - incompatible authentication mode: {auth_mode}')
                return
        except Exception as e:
            logger.error(f'Error checking cluster authentication mode: {str(e)}')
            return

        if check_access_entry_exists(eks_client, cluster_name, role_arn):
            logger.info(f'Access entry for role {role_arn} already exists in cluster {cluster_name}.')
            return

        logger.info(f'Creating access entry for cluster: {cluster_name}')
        response = eks_client.create_access_entry(
            clusterName=cluster_name,
            principalArn=role_arn,
            type='STANDARD'
        )
        logger.info(f'Access entry created successfully: {response["accessEntry"]["accessEntryArn"]}')

        logger.info(f'Associating access policy for cluster: {cluster_name}')
        eks_client.associate_access_policy(
            clusterName=cluster_name,
            principalArn=role_arn,
            policyArn='arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy',
            accessScope={
                'type': 'cluster'
            }
        )
        logger.info('Access policy associated successfully')
    except eks_client.exceptions.ResourceNotFoundException as e_not_found:
        logger.error(f'Cluster {cluster_name} not found -- {str(e_not_found)}')
    except eks_client.exceptions.AccessDeniedException as e_access_denied:
        logger.error(f'Access denied when creating access entry for cluster {cluster_name} -- {str(e_access_denied)}')
    except Exception as e:
        logger.error(f'Error creating access entry: {str(e)}')

def ekslogs(curr_region, logger, role_arn):
    try:
        logger.info('STARTING EKSLOGS...')
        wanted_cluster_logging_config = {
            'clusterLogging': [{
                'types': ['audit', 'authenticator'],
                'enabled': True
            }]
        }
        eks_client = boto3.client('eks', region_name=curr_region)        
        clusters = eks_client.list_clusters()['clusters']
        logger.info(f'Found {len(clusters)} clusters in region {curr_region}')

        for cluster_name in clusters:
            logger.info(f'CONFIGURING EKSLOGS ON CLUSTER: {cluster_name}')
            try:
                eks_client.update_cluster_config(
                    name=cluster_name,
                    logging=wanted_cluster_logging_config
                )
                logger.info(f'COMMAND SUCCEEDED.')
            except Exception as e:
                if 'No changes needed for the logging config provided' not in str(e):
                    logger.critical(f'COMMAND FAILED - {str(e)}')
                else:
                    logger.info(f'No changes needed for cluster {cluster_name}')
            create_access_entry(eks_client, logger, cluster_name, role_arn)

    except Exception as e:
        logger.critical(f'Error in ekslogs function: {str(e)}')
        logger.critical(traceback.format_exc())
        
def cyngular_function(event, context):
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.info('STARTING CYNGULARS FUNCTION...')

    LAMBDA_NAME = context.function_name
    REGIONS = os.environ['CLIENT_REGIONS']
    ROLE_ARN = os.environ['ROLE_ARN']
    try:
        if os.environ.get('FIRST_RUN') == 'true':
            logger.info('First run detected. Updating EventBridge rule schedule.')
            try:
                lambda_client = boto3.client('lambda')
                events_client = boto3.client('events')
                response = events_client.put_rule(
                    Name=f"{LAMBDA_NAME}-rule",
                    State='ENABLED',
                    ScheduleExpression=os.environ['FINAL_CRON'],
                    Description='LambdaEKS | Scheduled to run hourly',
                    EventBusName='default'
                )
                logger.info('Successfully updated the EventBridge rule: %s', response)
                response = lambda_client.update_function_configuration(
                    FunctionName=LAMBDA_NAME,
                    Environment={'Variables': {"FIRST_RUN": "false", "CLIENT_REGIONS": REGIONS, "ROLE_ARN": ROLE_ARN}}
                )
                logger.info('Successfully updated the function configuration: %s', response)
            except Exception as e:
                logger.critical('Error updating the EventBridge rule: %s', str(e))
                raise

        logger.info('STARTING EKSLOGS...')                    
        for curr_region in REGIONS.split(' '):
            logger.info(f'AWS REGION: {curr_region}')
            try:
                ekslogs(curr_region, logger, ROLE_ARN)
            except Exception as e:
                logger.critical(str(e))
        logger.info('DONE!')
        return {
            'statusCode': 200,
            'body': 'Function executed successfully'
        }

    except Exception as e:
        logger.critical(str(e))
        return {
            'statusCode': 500,
            'body': f'Error occurred: {str(e)}'
        }