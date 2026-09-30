package dissect

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"os"
	"path/filepath"
	"sort"
	"testing"
)

// Opt-in investigation of scoreboard kill counters versus kill feed names.
// Run with R6_PRO_REPLAY_FOLDER set to an extracted complete match folder.
func TestProfessionalScoreboardDiagnostic(t *testing.T) {
	folder := os.Getenv("R6_PRO_REPLAY_FOLDER")
	if folder == "" {
		t.Skip("set R6_PRO_REPLAY_FOLDER for real replay diagnostics")
	}
	files, err := filepath.Glob(filepath.Join(folder, "*.rec"))
	if err != nil || len(files) == 0 {
		t.Fatalf("no replay files: %v", err)
	}
	sort.Strings(files)
	feedTotals := make(map[string]int)
	scoreboardTotals := make(map[string]int)
	byDelta := make(map[uint32]map[string]int)
	deltaCounts := make(map[uint32]int)
	envelopeCount := 0
	tagCount := 0
	for _, path := range files {
		file, err := os.Open(path)
		if err != nil {
			t.Fatal(err)
		}
		r, err := NewReader(file)
		file.Close()
		if err != nil {
			t.Fatal(err)
		}
		data := r.b // Read() releases its own reference; keep bytes for the probe.
		if err := r.Read(); err != nil {
			t.Fatal(err)
		}
		feed := make(map[string]int)
		for _, event := range r.MatchFeedback {
			if event.Type == Kill {
				feed[event.Username]++
			}
		}
		// Same 23-prefix envelope used by score/assists, with a uint32 kill
		// count. Keep the largest value per entity during this round.
		entities := make(map[uint32]uint32)
		tag := []byte{0x1C, 0xD2, 0xB1, 0x9D}
		for start := 0; start < len(data); {
			rel := bytes.Index(data[start:], tag)
			if rel < 0 {
				break
			}
			pos := start + rel
			start = pos + len(tag)
			tagCount++
			if pos < 9 || pos+9 > len(data) || data[pos-9] != 0x23 ||
				!bytes.Equal(data[pos-4:pos], []byte{0, 0, 0, 0}) || data[pos+4] != 4 {
				continue
			}
			entity := binary.LittleEndian.Uint32(data[pos-8 : pos-4])
			envelopeCount++
			value := binary.LittleEndian.Uint32(data[pos+5 : pos+9])
			if _, delta := r.playerForEntity(entity); delta > 0 {
				deltaCounts[delta]++
			}
			if value > entities[entity] {
				entities[entity] = value
			}
		}
		scoreboard := make(map[string]uint32)
		for entity, value := range entities {
			index, delta := r.playerForEntity(entity)
			if index >= 0 {
				name := r.Header.Players[index].Username
				if byDelta[delta] == nil {
					byDelta[delta] = make(map[string]int)
				}
				if int(value) > byDelta[delta][name] {
					byDelta[delta][name] = int(value)
				}
				if delta != 12 {
					continue
				}
				if value > scoreboard[name] {
					scoreboard[name] = value
				}
			}
		}
		for _, player := range r.Header.Players {
			name := player.Username
			feedTotals[name] += feed[name]
			if int(scoreboard[name]) > scoreboardTotals[name] {
				scoreboardTotals[name] = int(scoreboard[name])
			}
			if feed[name] != int(scoreboard[name]) {
				t.Logf("%s %s feed=%d scoreboard=%d", filepath.Base(path), name,
					feed[name], scoreboard[name])
			}
		}
	}
	t.Logf("feed totals: %v", feedTotals)
	t.Logf("scoreboard totals: %v", scoreboardTotals)
	if destination := os.Getenv("R6_PRO_SCOREBOARD_OUTPUT"); destination != "" {
		encoded, err := json.MarshalIndent(map[string]interface{}{"feed": feedTotals, "scoreboard": scoreboardTotals,
			"by_delta":  byDelta,
			"tag_count": tagCount, "envelope_count": envelopeCount, "entity_deltas": deltaCounts}, "", "  ")
		if err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(destination, encoded, 0600); err != nil {
			t.Fatal(err)
		}
	}
}
