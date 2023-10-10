package main

import (
	"fmt"
	"io/ioutil"
	"log"
	"net"
	"os"

	// "log"

	"time"

	"golang.org/x/crypto/ssh"
	"golang.org/x/crypto/ssh/agent"

	// "github.com/gliderlabs/ssh"
	// "github.com/wangjia184/sortedset"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
)

type ParameterInfo struct {
	name  string
	value ssh.AuthMethod //[]byte
	// Value string
}

type Server struct {
	hostName string

	scriptPath string

	keyPath    string
	privateKey []byte
}

func main() {

	region := ""

	sess, err := session.NewSessionWithOptions(session.Options{
		// Specify profile to load for the session's config
		Profile: "prosuct_side_staging",

		// Provide SDK Config options, such as Region.
		Config: aws.Config{
			Region: aws.String(region),
			// LogLevel: aws.LogLevelType(2).value(),
		},

		// Force enable Shared Config support
		SharedConfigState: session.SharedConfigEnable,
	})

	SessMsg := fmt.Sprint("Error creating session:")
	CheckErr(err, SessMsg)

	InvokeLambdaRC(sess)

	// keys := GetPrKeysFromParamStore(region)
	Servers := GatherServersInfo(sess)

	jumpHost := Servers["BASTION"].hostName
	jumpPrivateKeyPath := Servers["BASTION"].keyPath
	jumpPort := 22

	// jumpKey, err := os.ReadFile(jumpPrivateKeyPath)
	// signer, err := ssh.ParsePrivateKey(jumpKey)
	jumpConfig := &ssh.ClientConfig{
		User: "ubuntu",
		Auth: []ssh.AuthMethod{
			// ssh.PublicKeys(signer),
			GetPrivateKey(jumpPrivateKeyPath),
		},
		Timeout:         5 * time.Second,
		HostKeyCallback: ssh.InsecureIgnoreHostKey(),
	}

	jumpClient, err := ssh.Dial("tcp", fmt.Sprintf("%s:%d", jumpHost, jumpPort), jumpConfig)
	dialMsg := fmt.Sprint("Failed to connect to bastion:")
	CheckErr(err, dialMsg)

	defer jumpClient.Close()
	// vs := vssh.New().Start()

	// config := vssh.GetConfigUserPass("vssh", "vssh")
	for _, srv := range Servers {
		fmt.Printf("Connecting to %s server...\n", srv)

		// Dial a connection to the target server through the jump server
		targetConn, err := jumpClient.Dial("tcp", fmt.Sprintf("%s:%d", srv.hostName, jumpPort))

		dialMsg := "Failed to connect to target server:"
		CheckErr(err, dialMsg)

		defer targetConn.Close()
		// config, _ := vssh.GetConfigPEM("ubuntu", string(srv.privateKey))

		// vs.AddClient(srv.hostName, config, vssh.SetMaxSessions(2))

	}

	// Now you can iterate through the servers and establish SSH connections
	for _, srv := range Servers {
		establishSSHConnection(srv)
	}

	// vs.Wait()

	// ctx, cancel := context.WithCancel(context.Background())
	// defer cancel()

	// cmd := "echo 'Hello, server!'"
	// timeout, _ := time.ParseDuration("30s")
	// respChan := vs.Run(ctx, cmd, timeout)

	// for resp := range respChan {
	// 	if err := resp.Err(); err != nil {
	// 		log.Println(err)
	// 		continue
	// 	}

	// 	outTxt, errTxt, _ := resp.GetText(vs)
	// 	fmt.Println(outTxt, errTxt, resp.ExitStatus())
	// }

}

func testIt() {

	// Load private key for SSH agent
	sshAuthSock := os.Getenv("SSH_AUTH_SOCK")
	sshAgent, err := net.Dial("unix", sshAuthSock)
	if err != nil {
		log.Fatalf("Failed to connect to SSH agent: %v", err)
	}
	agentClient := agent.NewClient(sshAgent)
	signers, err := agentClient.Signers()
	if err != nil {
		log.Fatalf("Failed to get signers from SSH agent: %v", err)
	}

	// Private key for bastion host
	bastionKeyPath := "/path/to/bastion/private/key"
	bastionPrivateKey, err := ioutil.ReadFile(bastionKeyPath)
	if err != nil {
		log.Fatalf("Failed to read bastion private key: %v", err)
	}
	bastionSigner, err := ssh.ParsePrivateKey(bastionPrivateKey)
	if err != nil {
		log.Fatalf("Failed to parse bastion private key: %v", err)
	}

	bastionConfig := &ssh.ClientConfig{
		User: "bastion-user",
		Auth: []ssh.AuthMethod{
			ssh.PublicKeys(bastionSigner),
			ssh.PublicKeys(signers...),
		},
		HostKeyCallback: ssh.InsecureIgnoreHostKey(), // Be cautious in production
	}

	bastionConn, err := ssh.Dial("tcp", "bastion-host:22", bastionConfig)
	if err != nil {
		log.Fatalf("Failed to connect to bastion host: %v", err)
	}
	defer bastionConn.Close()

	// Now you can create a session on the bastion host
	session, err := bastionConn.NewSession()
	if err != nil {
		log.Fatalf("Failed to create session on bastion host: %v", err)
	}
	defer session.Close()

	// Use session to execute commands on bastion host
	session.Run("echo 'Hello from bastion host'")

	// Continue by opening another session on target server via bastion
	targetConfig := &ssh.ClientConfig{
		User: "target-user",
		Auth: []ssh.AuthMethod{
			ssh.PublicKeys(signers...),
		},
		HostKeyCallback: ssh.InsecureIgnoreHostKey(), // Be cautious in production
	}

	targetConn, err := bastionConn.Dial("tcp", "target-host:22")
	if err != nil {
		log.Fatalf("Failed to connect to target host via bastion: %v", err)
	}
	defer targetConn.Close()

	targetSSHClient, targetSSHSession, err := targetConn.Conn.OpenSSH(targetConfig)
	if err != nil {
		log.Fatalf("Failed to open SSH session on target host: %v", err)
	}
	defer targetSSHSession.Close()

	// Use targetSSHSession to execute commands on target server
	targetSSHSession.Run("echo 'Hello from target host'")
}
