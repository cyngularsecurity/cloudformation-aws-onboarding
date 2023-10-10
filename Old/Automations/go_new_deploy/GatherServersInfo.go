package main

import (
	"os"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/joho/godotenv"
)

func GatherServersInfo(sess *session.Session) (servers map[string]Server) {

	err := godotenv.Load(".env")
	loadMsg := "Error loading .env file:"
	CheckErr(err, loadMsg)

	bastion_ip := os.Getenv("BASTION_SERVER_IP")
	api_ip := os.Getenv("API_SERVER_IP")
	lb_ip := os.Getenv("LOAD_BALANCER_SERVER_IP")
	frontend_ip := os.Getenv("FRONTEND_SERVER_IP")
	backend_ip := os.Getenv("BACKEND_SERVER_IP")

	bastion_key_path := os.Getenv("BASTION_SERVER_KEY_PATH")
	api_key_path := os.Getenv("API_SERVER_KEY_PATH")
	lb_key_path := os.Getenv("LOAD_BALANCER_SERVER_KEY_PATH")
	frontend_key_path := os.Getenv("FRONEND_SERVER_KEY_PATH")
	backend_key_path := os.Getenv("BACKEND_SERVER_KEY_PATH")

	keys := GetPrKeysFromParamStore(sess)

	// loop through ec2 instance and describe keypair ID, search for ids in param store
	Servers := map[string]Server{
		"API":     {hostName: api_ip, keyPath: api_key_path},
		"LB":      {hostName: lb_ip, keyPath: lb_key_path},
		"BE":      {hostName: backend_ip, keyPath: frontend_key_path},
		"FE":      {hostName: frontend_ip, keyPath: backend_key_path},
		"BASTION": {hostName: bastion_ip, keyPath: bastion_key_path},
	}

	// Create a list of servers with private keys
	for _, reservation := range result.Reservations {
		for _, instance := range reservation.Instances {
			keyName := aws.StringValue(instance.KeyName)
			if keyName != "" {
				servers = append(servers, Server{
					Hostname:   aws.StringValue(instance.PrivateIpAddress),
					PrivateKey: privateKeys[keyName],
				})
			}
		}
	}

	return servers
}
