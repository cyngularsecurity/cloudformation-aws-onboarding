package main

import (
	"fmt"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/ssm"
)

func GetPrKeysFromParamStore(sess *session.Session) (keys []ParameterInfo) {
	parameterPath := "/"

	svc := ssm.New(sess)

	listInput := &ssm.DescribeParametersInput{
		ParameterFilters: []*ssm.ParameterStringFilter{
			{
				Key:    aws.String("Path"),
				Values: []*string{aws.String(parameterPath)},
			},
		},
	}

	listResult, err := svc.DescribeParameters(listInput)
	listResMsg := fmt.Sprint("Error listing parameters:")
	CheckErr(err, listResMsg)

	for _, parameter := range listResult.Parameters {
		fmt.Println("Retrieving parameter:", *parameter.Name)

		paramInput := &ssm.GetParameterInput{
			Name:           parameter.Name,
			WithDecryption: aws.Bool(true),
		}

		result, err := svc.GetParameter(paramInput)
		getMsg := fmt.Sprintf("Failed to retrieve private key for key pair '%s':", *parameter.KeyId)

		CheckErr(err, getMsg)

		keys = append(keys, ParameterInfo{
			name:  *parameter.Name,
			value: GetPrivateKey(*result.Parameter.Value),
		})

		fmt.Println("Retrieved Parameter:", *parameter.Name)
		// fmt.Println("Retrieved Parameter Value:", *result.Parameter.Value)
	}

	return keys
}
