import boto3
import json
import cfnresponse

def handler(event, context):
    cloudtrail = boto3.client('cloudtrail')
    response_data = {}
    try:
        trails = cloudtrail.describe_trails()['trailList']
        for trail in trails:
            if trail.get('S3BucketName'):
                response_data['TrailExists'] = 'true'
                response_data['S3BucketName'] = trail['S3BucketName']
                break
        else:
            response_data['TrailExists'] = 'false'
        
        cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
    except Exception as e:
        print(f"Failed to describe trails: {e}")
        cfnresponse.send(event, context, cfnresponse.FAILED, response_data)