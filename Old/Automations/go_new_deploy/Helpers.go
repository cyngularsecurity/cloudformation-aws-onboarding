package main

import (
	"errors"

	"github.com/fatih/color"
	"github.com/ichtrojan/thoth"
	log "github.com/rs/zerolog/log"
)

func CheckErr(err error, msg string) {
	genLogger, _ := thoth.Init("log")

	// init a general file for logging
	if err != nil {
		color.Red(msg)
		// color.Green(msg)
		genLogger.Log(errors.New(msg))
		log.Info().Msg(msg)
		log.Fatal()

		// clog.SetFlags(log.Ldate | log.Ltime | log.Lshortfile)
		// clog.Fatalf("Error: %v\n Error Message: %v", err, msg)

		// panic(err.Error())
		// os.Exit(-1)
		// return nil
	}
}
