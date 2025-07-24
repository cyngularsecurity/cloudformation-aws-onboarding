import boto3
import os
import logging


def vpcflowlogs(curr_region):
    try:
        logging.info(f"DELETING VPCFLOWLOGS... {curr_region}")

        flowlogs_ids_list = []
        ec2_client = boto3.client("ec2", region_name=curr_region)

        response = ec2_client.describe_flow_logs(
            Filters=[
                {"Name": "tag:Name", "Values": ["Cyngular-vpc-flowlogs"]},
            ]
        )
        for flow_log in response["FlowLogs"]:
            flowlogs_ids_list.append(flow_log["FlowLogId"])

        logging.info(f"DELETING THE VPCFLOWLOGS: {flowlogs_ids_list}")
        response = ec2_client.delete_flow_logs(FlowLogIds=flowlogs_ids_list)
        logging.info(f"COMMAND SUCCEEDED. {response}")
    except Exception as e:
        logging.critical(f"{curr_region} - {str(e)}")


def cyngular_function(event, context):
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    try:
        logger.info("STRATING CYNGULARS FUNCTION...")
        events_client = boto3.client("events")
        REGIONS = os.environ["CLIENT_REGIONS"]

        for curr_region in REGIONS.split(" "):
            logger.info(f"AWS REGION: {curr_region}")
            try:
                vpcflowlogs(curr_region)
            except Exception as e:
                logger.critical(f"{curr_region} - {str(e)}")
        logger.info("DEACTIVATING EVENT BUS RULE")
        response = events_client.disable_rule(
            Name="cyngular-lambda-config-vpcflowlogs-rule", EventBusName="default"
        )
        logger.info(f"DONE! {response}")
    except Exception as e:
        logger.critical(f"CYNGULARS FUNCTION FAILED. {str(e)}")
