// Read-only research helper: emit each replay round's player DissectID values.
// Run from third_party/siege-dissect with:
// go run ../../research/defuser_identity_probe.go MATCH_FOLDER
package main

import (
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"sort"

	"github.com/lumina-r6/siege-dissect/dissect"
	"github.com/rs/zerolog"
)

func main() {
	zerolog.SetGlobalLevel(zerolog.Disabled)
	files, err := filepath.Glob(filepath.Join(os.Args[1], "*.rec"))
	if err != nil || len(files) == 0 {
		panic("no replay rounds")
	}
	sort.Strings(files)
	rounds := make(map[string]map[string]string)
	for _, path := range files {
		file, err := os.Open(path)
		if err != nil {
			panic(err)
		}
		reader, err := dissect.NewReader(file)
		file.Close()
		if err != nil {
			panic(err)
		}
		if err := reader.Read(); !dissect.Ok(err) {
			panic(err)
		}
		players := make(map[string]string)
		for _, player := range reader.Header.Players {
			players[player.Username] = hex.EncodeToString(player.DissectID)
		}
		rounds[filepath.Base(path)] = players
	}
	if err := json.NewEncoder(os.Stdout).Encode(rounds); err != nil {
		panic(err)
	}
}
