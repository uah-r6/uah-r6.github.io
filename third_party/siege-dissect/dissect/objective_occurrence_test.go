package dissect

import (
	"encoding/hex"
	"testing"
)

func objectiveFixture(t *testing.T, encoded string) []byte {
	t.Helper()
	b, err := hex.DecodeString(encoded)
	if err != nil {
		t.Fatal(err)
	}
	return b
}

func TestObjectiveContiguousPropertyGrammar(t *testing.T) {
	const ref = "237b00000000000000"
	const site = "2f5e64410402000000"
	const state = "ff39f4080101"
	for _, encoded := range []string{ref + state, ref + site + "22" + state} {
		events := objectiveStates(objectiveFixture(t, encoded))
		if len(events) != 1 || events[0].entity != 123 || events[0].value != 1 {
			t.Fatalf("bad states: %+v", events)
		}
	}
	for _, encoded := range []string{ref + site + "2622" + state, "22" + state, ref + "ff39f40801", ref + "616263640378797a22" + state} {
		if events := objectiveStates(objectiveFixture(t, encoded)); len(events) != 0 {
			t.Fatalf("unknown/truncated record accepted: %+v", events)
		}
	}
}

func TestObjectiveOccurrenceSeparatesCleanupAndActor(t *testing.T) {
	states := []objectiveState{{100, 123, 1}, {200, 123, 0}}
	attack := inferObjectiveOccurrences(states, Attack)
	defense := inferObjectiveOccurrences(states[:1], Defense) // February disable lacks state0.
	if len(attack) != 1 || attack[0].Kind != "plant" || attack[0].Actor != nil {
		t.Fatal(attack)
	}
	if len(defense) != 2 || defense[1].Kind != "disable" || defense[1].Actor != nil {
		t.Fatal(defense)
	}
	for _, events := range [][]objectiveState{nil, {{100, 123, 0}}, {{100, 123, 1}, {101, 123, 1}}, {{100, 123, 1}, {101, 456, 0}}, {{90, 123, 0}, {100, 123, 1}}} {
		if result := inferObjectiveOccurrences(events, Defense); len(result) != 0 {
			t.Fatalf("ambiguous state accepted: %+v", result)
		}
	}
}

func TestObjectiveOccurrenceRequiresPhysicalScoreWinner(t *testing.T) {
	r := &Reader{b: objectiveFixture(t, "237b00000000000000ff39f4080101")}
	r.Header.GameMode = Bomb
	r.Header.Teams[0].Role = Attack
	r.Header.Teams[1].Role = Defense
	r.Header.Teams[1].Won = true // A legacy inferred flag alone is insufficient.
	r.Header.Teams[1].WinCondition = DisabledDefuser
	r.resolveObjectiveOccurrences()
	if len(r.Header.ObjectiveOccurrences) != 0 {
		t.Fatal("credited from heuristic winner")
	}
	r.Header.Teams[1].Score = 1
	r.resolveObjectiveOccurrences()
	if len(r.Header.ObjectiveOccurrences) != 2 || len(r.MatchFeedback) != 0 {
		t.Fatal("occurrence must not credit a player")
	}
	r.Header.Teams[0].Score = 1
	r.resolveObjectiveOccurrences()
	if len(r.Header.ObjectiveOccurrences) != 0 {
		t.Fatal("accepted two winners")
	}
}
