package main

import (
	"fmt"

	// "io/ioutil"
	"os"
	"strings"

	log "github.com/rs/zerolog/log"
)

func PopulateDotEnv() {

	replacements := map[string]string{
		"{{DB_HOST}}": "db.example.com",
		"{{DB_USER}}": "username",
		"{{DB_PASS}}": "password",
	}

	// Read .env.example content
	fileContent, err := os.ReadFile(".env.example")
	if err != nil {
		log.Fatal("Error reading .env.example:", err)
	}

	// Replace placeholders with actual values
	envContent := string(fileContent)
	for placeholder, value := range replacements {
		envContent = strings.ReplaceAll(envContent, placeholder, value)
	}

	// Write populated content to .env file
	err = os.WriteFile(".env", []byte(envContent), 0644)
	if err != nil {
		log.Fatal("Error writing .env:", err)
	}

	// Replace placeholders with actual values
	envContent := strings.ReplaceAll(string(exampleContent), "{{DB_HOST}}", "db.example.com")
	envContent = strings.ReplaceAll(envContent, "{{DB_USER}}", "username")
	envContent = strings.ReplaceAll(envContent, "{{DB_PASS}}", "password")

	// Write populated content to .env file
	err = os.WriteFile(".env", []byte(envContent), 0644)
	if err != nil {
		log.Fatal("Error writing .env:", err)
	}

	fmt.Println(".env file populated and saved.")
}
