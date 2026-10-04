package main

import (
	"encoding/json"
	"fmt"
	"github.com/lumina-r6/siege-dissect/dissect"
	"os"
)

func main() {
	if len(os.Args) != 2 {
		fmt.Fprintln(os.Stderr, "usage: clock-prefix-inspect round.dump")
		os.Exit(2)
	}
	b, err := os.ReadFile(os.Args[1])
	if err == nil {
		err = json.NewEncoder(os.Stdout).Encode(dissect.InspectClockPrefixGroupsBuffer(b))
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
