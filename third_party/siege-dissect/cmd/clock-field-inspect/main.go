package main

import (
	"encoding/json"
	"fmt"
	"github.com/lumina-r6/siege-dissect/dissect"
	"os"
)

func main() {
	if len(os.Args) != 3 {
		fmt.Fprintln(os.Stderr, "usage: clock-field-inspect round.dump round.rec")
		os.Exit(2)
	}
	b, err := os.ReadFile(os.Args[1])
	var header []byte
	if err == nil {
		header, err = os.ReadFile(os.Args[2])
	}
	if err == nil {
		err = json.NewEncoder(os.Stdout).Encode(struct {
			Clock  dissect.ClockFieldEvidence      `json:"clock"`
			Header dissect.RecordingHeaderEvidence `json:"raw_header"`
		}{dissect.InspectClockFieldPrefixesBuffer(b), dissect.InspectRecordingHeaderFields(header)})
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
