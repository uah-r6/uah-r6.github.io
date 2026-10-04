// Opt-in local evidence command. No credited policy, SQLite or public export.
package main

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/lumina-r6/siege-dissect/dissect"
	"github.com/rs/zerolog"
)

func main() {
	zerolog.SetGlobalLevel(zerolog.Disabled)
	var result dissect.EventHistoryEvidence
	var err error
	if len(os.Args) == 4 && os.Args[1] == "--buffer" {
		var header struct {
			Header dissect.Header `json:"header"`
		}
		var b []byte
		b, err = os.ReadFile(os.Args[2])
		if err == nil {
			err = json.Unmarshal(b, &header)
		}
		if err == nil {
			b, err = os.ReadFile(os.Args[3])
		}
		if err == nil {
			result = dissect.InspectEventHistoryBuffer(b, header.Header)
		}
	} else if len(os.Args) == 3 && os.Args[1] == "--replay" {
		var f *os.File
		f, err = os.Open(os.Args[2])
		if err == nil {
			_, result, err = dissect.ReadEventHistoryEvidence(f)
			f.Close()
		}
	} else {
		fmt.Fprintln(os.Stderr, "usage: history-inspect --buffer observation.json round.dump | --replay ROUND.rec")
		os.Exit(2)
	}
	if err == nil {
		err = json.NewEncoder(os.Stdout).Encode(result)
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
