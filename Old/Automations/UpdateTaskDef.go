package main

import (
	"fmt"

	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/ecs"
)

func main() {
	// Create a new AWS session
	sess, err := session.NewSession()
	if err != nil {
		panic(err)
	}

	// Create an ECS client
	ecsClient := ecs.New(sess)

	// List ECS clusters
	clusters, err := ecsClient.ListClusters(nil)
	if err != nil {
		panic(err)
	}

	// Iterate through clusters
	for _, clusterArn := range clusters.ClusterArns {
		fmt.Println("Cluster ARN:", *clusterArn)

		// List task definitions for the cluster
		tasks, err := ecsClient.ListTaskDefinitions(&ecs.ListTaskDefinitionsInput{
			Status:       aws.String("ACTIVE"),
			FamilyPrefix: aws.String("your-task-family-prefix"), // Replace with your task family prefix
		})
		if err != nil {
			panic(err)
		}

		// Iterate through task definitions
		for _, taskArn := range tasks.TaskDefinitionArns {
			fmt.Println("Task Definition ARN:", *taskArn)

			// Describe task definition to get container definitions
			taskDetails, err := ecsClient.DescribeTaskDefinition(&ecs.DescribeTaskDefinitionInput{
				TaskDefinition: taskArn,
			})
			if err != nil {
				panic(err)
			}

			// Iterate through container definitions
			for _, container := range taskDetails.TaskDefinition.ContainerDefinitions {
				fmt.Printf("Container Name: %s, Image: %s:%s\n",
					*container.Name, *container.Image, *container.ImageDigest)
			}
		}
	}
}
