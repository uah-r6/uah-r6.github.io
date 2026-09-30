package dissect

import (
	"os"
	"testing"
)

// Opt-in regression using an official June 18 Y11S2_Alpha03 replay. That
// build has different player-ID and UI-ID property hashes than adjacent builds.
func TestProfessionalY11S2NALPlayerAndActionMarkers(t *testing.T) {
	path := os.Getenv("R6_PRO_NAL_Y11S2_ROUND")
	if path == "" {
		t.Skip("set R6_PRO_NAL_Y11S2_ROUND to an official June 18 .rec")
	}
	file, err := os.Open(path)
	if err != nil {
		t.Fatal(err)
	}
	defer file.Close()
	reader, err := NewReader(file)
	if err != nil {
		t.Fatal(err)
	}
	if reader.Header.CodeVersion != Y11S2_Alpha03NAL {
		t.Fatalf("unexpected replay build %d", reader.Header.CodeVersion)
	}
	if err := reader.Read(); !Ok(err) {
		t.Fatalf("failed to read official round: %v", err)
	}
	if len(reader.Header.Players) != 10 || len(reader.Scoreboard.Players) != 10 {
		t.Fatalf("incomplete players or scoreboard: %d / %d",
			len(reader.Header.Players), len(reader.Scoreboard.Players))
	}
	if !reader.Header.ActionPhaseDetected {
		t.Fatal("action-start marker was not detected")
	}
	attackers := 0
	for _, player := range reader.Header.Players {
		if len(player.DissectID) != 4 {
			t.Fatalf("missing physical identity for %s", player.Username)
		}
		if reader.Header.Teams[player.TeamIndex].Role == Attack {
			attackers++
			if player.OperatorSource != "action_start_header" ||
				!player.OperatorSeenBeforeAction || player.Operator == 0 {
				t.Fatalf("unresolved final attacker for %s", player.Username)
			}
		}
	}
	if attackers != 5 {
		t.Fatalf("expected five attackers, got %d", attackers)
	}
	if len(reader.PlayerStats()) != 10 {
		t.Fatal("player statistics incomplete")
	}
}
