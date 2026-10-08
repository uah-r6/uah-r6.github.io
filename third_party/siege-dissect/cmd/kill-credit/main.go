// Local evidence command. It never opens SQLite or writes public statistics.
package main

import (
	"encoding/json"
	"fmt"
	"github.com/lumina-r6/siege-dissect/dissect"
	"github.com/rs/zerolog"
	"os"
)

func main() {
	zerolog.SetGlobalLevel(zerolog.Disabled)
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: kill-credit ROUND.rec [...]")
		os.Exit(2)
	}
	for _, path := range os.Args[1:] {
		if path == "--evidence" {
			continue
		}
		f, err := os.Open(path)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		var header dissect.Header
		var credit dissect.RoundKillCredit
		if os.Args[1] == "--evidence" {
			var evidence dissect.CreditStructuralEvidence
			decoder := json.NewDecoder(f)
			decoder.UseNumber()
			err = decoder.Decode(&evidence)
			header = evidence.Header
			if err == nil {
				credit = dissect.ValidateKillCreditEvidence(evidence)
			}
		} else {
			header, credit, err = dissect.ReadKillCredit(f)
		}
		f.Close()
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		if err = json.NewEncoder(os.Stdout).Encode(struct {
			File   string                  `json:"file"`
			Header dissect.Header          `json:"header"`
			Credit dissect.RoundKillCredit `json:"credit"`
		}{path, header, credit}); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	}
}
