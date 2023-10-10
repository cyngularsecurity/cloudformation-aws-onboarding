package main

import (
	"os"

	"golang.org/x/crypto/ssh"
)

// GetPrivateKey reads and returns the SSH private key from the given path.
func GetPrivateKey(file string) ssh.AuthMethod {
	bufferKey, err := os.ReadFile(file)
	readMsg := "Failed to Read private key:"
	CheckErr(err, readMsg)

	keySigner, err := ssh.ParsePrivateKey(bufferKey)
	parseMsg := "Failed to Parse private key:"
	CheckErr(err, parseMsg)
	return ssh.PublicKeys(keySigner)
}
