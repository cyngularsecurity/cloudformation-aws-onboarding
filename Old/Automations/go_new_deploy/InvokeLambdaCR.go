package main

import (
	"fmt"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/lambda"
)

func InvokeLambdaRC(sess *session.Session) {

	svc := lambda.New(sess)

	input := &lambda.InvokeInput{
		FunctionName: aws.String("function-name"),
	}

	result, err := svc.Invoke(input)
	resMsg := fmt.Sprint("Error invoking Lambda function:")
	CheckErr(err, resMsg)

	fmt.Println("Lambda Response:", string(result.Payload))
}
