// Separate opt-in native-envelope diagnostic; no SQLite/public writes.
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
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: kill-credit-envelope ROUND.rec [...]")
		os.Exit(2)
	}
	for _, path := range os.Args[1:] {
		f, err := os.Open(path)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		header, credit, original, envelopes, err := dissect.ReadKillCreditNativeEnvelopes(f)
		f.Close()
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		if err := json.NewEncoder(os.Stdout).Encode(struct {
			File             string                           `json:"file"`
			Header           dissect.Header                   `json:"header"`
			Credit           dissect.RoundKillCredit          `json:"credit"`
			OriginalFinishes []dissect.CreditFinish           `json:"originalFinishes"`
			Envelopes        []dissect.NativeFeedbackEnvelope `json:"nativeEnvelopes"`
		}{path, header, credit, original, envelopes}); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	}
}
