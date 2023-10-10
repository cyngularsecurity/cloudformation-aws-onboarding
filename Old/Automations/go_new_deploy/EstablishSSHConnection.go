package main

import (
	"time"

	"golang.org/x/crypto/ssh"
)

func establishSSHConnection(server Server) (client *ssh.Client) {

	sshUser := "ubuntu"
	sshPort := 22

	signer, err := ssh.ParsePrivateKey(server.privateKey)
	signErr := "Failed to sign private key:"
	CheckErr(err, signErr)

	config := &ssh.ClientConfig{
		User: sshUser,
		Auth: []ssh.AuthMethod{
			ssh.PublicKeys(signer),
		},
		Timeout:         5 * time.Second,
		HostKeyCallback: ssh.InsecureIgnoreHostKey(),
	}

	client, err = ssh.Dial("tcp", server.hostName+":"+string(sshPort), config)

	dialMsg := "Failed to dial bastion host:"
	CheckErr(err, dialMsg)

	defer client.Close()

	// Now you have an SSH connection to the server
	// You can execute commands or perform other operations here
	return client
}
