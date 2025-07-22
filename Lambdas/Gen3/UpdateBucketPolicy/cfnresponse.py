import json
import urllib3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SUCCESS = "SUCCESS"
FAILED = "FAILED"

http = urllib3.PoolManager()


def send(
    event,
    context,
    responseStatus,
    responseData,
    physicalResourceId=None,
    noEcho=False,
    reason=None,
):
    """
    Send a response to CloudFormation regarding the status of a custom resource.
    """
    responseUrl = event["ResponseURL"]

    logger.info(f"Sending CloudFormation response: {responseStatus}")

    responseBody = {
        "Status": responseStatus,
        "Reason": reason
        or f"See the details in CloudWatch Log Stream: {context.log_stream_name}",
        "PhysicalResourceId": physicalResourceId or context.log_stream_name,
        "StackId": event["StackId"],
        "RequestId": event["RequestId"],
        "LogicalResourceId": event["LogicalResourceId"],
        "NoEcho": noEcho,
        "Data": responseData,
    }

    json_responseBody = json.dumps(responseBody)

    logger.info(f"Response body: {json_responseBody}")

    headers = {"content-type": "", "content-length": str(len(json_responseBody))}

    try:
        response = http.request(
            "PUT", responseUrl, headers=headers, body=json_responseBody
        )
        logger.info(f"Status code: {response.status}")

    except Exception as e:
        logger.error(f"send(..) failed executing http.request(..): {e}")
