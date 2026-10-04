// Opt-in cached-buffer research command. Never assigns credited kills.
package main

import (
	"encoding/json"
	"fmt"
	"github.com/lumina-r6/siege-dissect/dissect"
	"os"
)

func main() {
	if len(os.Args) != 4 {
		fmt.Fprintln(os.Stderr, "usage: owned-property-inspect header.json round.dump query.json")
		os.Exit(2)
	}
	var h struct {
		Header dissect.Header `json:"header"`
	}
	var q dissect.OwnedPropertyQuery
	b, err := os.ReadFile(os.Args[1])
	if err == nil {
		err = json.Unmarshal(b, &h)
	}
	if err == nil {
		b, err = os.ReadFile(os.Args[3])
	}
	if err == nil {
		err = json.Unmarshal(b, &q)
	}
	if err == nil {
		b, err = os.ReadFile(os.Args[2])
	}
	if err == nil {
		err = json.NewEncoder(os.Stdout).Encode(dissect.InspectOwnedPropertyFramesBuffer(b, h.Header, q))
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
