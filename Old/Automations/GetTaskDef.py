import boto3

def get_all_task_definitions(ecs_client):
    task_definitions = []
    paginator = ecs_client.get_paginator('list_task_definitions')

    for page in paginator.paginate():
        task_definitions.extend(page['taskDefinitionArns'])

    return task_definitions

def get_task_definition_details(ecs_client, task_definition):
    task_details = ecs_client.describe_task_definition(taskDefinition=task_definition)
    
    # tasks = ecs_client.list_task_definitions(status='ACTIVE', familyPrefix='Backend')
    # task_arns = tasks['taskDefinitionArns']
    
    return task_details['taskDefinition']

def main():
    regions = ['us-west-1'] 
    session = boto3.Session()

    for region in regions:
        ecs_client = session.client('ecs', region_name=region)
        clusters = ecs_client.list_clusters()['clusterArns']
        cluster_arns = clusters['clusterArns']

        for cluster, cluster_arn in clusters, cluster_arns:
            cluster_name = cluster.split('/')[-1]
            task_definitions = get_all_task_definitions(ecs_client)

            for task_definition in task_definitions:
                task_definition_details = get_task_definition_details(ecs_client, task_definition)
                
                print(f"Region: {region}, Cluster name: {cluster_name}, Cluster Arn: {cluster_arn}")
                print(f"Task Definition: {task_definition_details['family']}:{task_definition_details['revision']}")
                
                for container_def in task_definition_details['containerDefinitions']:
                    print(f"Container: {container_def['name']}")
                    print(f"Image: {container_def['image']}")
                    
                    if '.amazonaws.com' in container_def['image']:
                        repo_name, image_tag = container_def['image'].split('/')[-1].split(':')
                        print(f"ECR Repository: {repo_name}")
                        print(f"Image Tag: {image_tag}")
                        
                    if 'imageDigest' in container_def:
                        print(f"Image Digest: {container_def['imageDigest']}")
                    print("Tags:", container_def.get('imageConfig', {}).get('labels', {}))
                    print()

if __name__ == "__main__":
    main()
