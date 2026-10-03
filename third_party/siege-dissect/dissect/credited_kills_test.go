package dissect

import (
	"encoding/binary"
	"encoding/json"
	"os"
	"testing"
)

func TestCreditCurrentY11IndependentStkFixture(t *testing.T) {
	// Parsed summaries only, with header UIDs ordinalized and profile UUIDs
	// removed. Actual offsets/classes/counters/finishes retained from8580R06.
	data, err := os.ReadFile("../../../tests/fixtures/credited-kills-stk-y11.json")
	if err != nil {
		t.Fatal(err)
	}
	var e CreditStructuralEvidence
	if err = json.Unmarshal(data, &e); err != nil {
		t.Fatal(err)
	}
	r := ValidateKillCreditEvidence(e)
	if !r.Complete {
		t.Fatalf("real structured control refused: %+v", r)
	}
	for _, p := range r.Players {
		if p.Username == "Kheyze.TLAW" && (*p.Kills != 1 || *p.Initial != 5 || *p.Terminal != 6) {
			t.Fatalf("Kheyze credit wrong: %+v", p)
		}
		if p.Username == "Maia.TLAW" && *p.Kills != 0 {
			t.Fatal("finisher received kill credit")
		}
	}
	found := false
	for _, f := range r.Finishes {
		if f.Offset == 74276292 && f.Feedback.Username == "Maia.TLAW" && f.Feedback.Target == "Stk.INTZ" {
			found = true
		}
	}
	if !found {
		t.Fatal("original finisher event lost")
	}
}

func creditFixture() (Header, []byte, []CreditFinish) {
	h := Header{ActionPhaseStartOffset: 1000}
	h.Teams[0].Won = true
	data := make([]byte, 2500)
	for i := 0; i < 10; i++ {
		h.Players = append(h.Players, Player{ID: uint64(i + 1), Username: string(rune('a' + i)), TeamIndex: i / 5})
		owner, component := uint32(i+101), uint32(i+201)
		at := i * 40
		data[at] = 0x1b
		binary.LittleEndian.PutUint32(data[at+1:], owner)
		binary.LittleEndian.PutUint32(data[at+9:], creditScoreSlot)
		binary.LittleEndian.PutUint32(data[at+13:], component)
		binary.LittleEndian.PutUint32(data[at+21:], creditScoreClass)
		creditFixtureProperty(data, 400+i*30, owner, objectiveUIDTag, 8, uint64(i+1))
		creditFixtureProperty(data, 750+i*20, component, creditKillTag, 4, 3)
		creditFixtureProperty(data, 1500+i*20, component, creditKillTag, 4, 4)
	}
	return h, data, []CreditFinish{{Offset: 1200, Feedback: MatchUpdate{Type: Kill, Username: "b", Target: "f"}}}
}

func creditFixtureProperty(data []byte, at int, entity, tag uint32, size int, value uint64) {
	data[at] = 0x23
	binary.LittleEndian.PutUint32(data[at+1:], entity)
	binary.LittleEndian.PutUint32(data[at+9:], tag)
	data[at+13] = byte(size)
	for i := 0; i < size; i++ {
		data[at+14+i] = byte(value >> uint(8*i))
	}
}

func TestCreditSeparateFromFinisherAndDeadOwner(t *testing.T) {
	h, data, finishes := creditFixture()
	// "a" is already dead when its scoreboard credit arrives. The replay
	// finisher is "b". Do not derive/guess a victim for "a"'s credit.
	finishes = append(finishes, CreditFinish{Offset: 1400, Feedback: MatchUpdate{Type: Death, Username: "a"}})
	r := deriveKillCredit(h, data, finishes)
	if !r.Complete || *r.Players[0].Kills != 1 || r.Finishes[0].Feedback.Username != "b" || r.Finishes[1].Feedback.Username != "a" {
		t.Fatalf("wrong credit/finish distinction: %+v", r)
	}
}

func TestCreditRefusesInvalidStructure(t *testing.T) {
	tests := map[string]func(*Header, []byte){
		"unfinished_round":  func(h *Header, b []byte) { h.Teams[0].Won = false },
		"ambiguous_winner":  func(h *Header, b []byte) { h.Teams[1].Won = true },
		"duplicate_uid":     func(h *Header, b []byte) { h.Players[1].ID = h.Players[0].ID },
		"missing_player":    func(h *Header, b []byte) { h.Players = h.Players[:9] },
		"counter_drop":      func(h *Header, b []byte) { binary.LittleEndian.PutUint32(b[1514:], 2) },
		"counter_width":     func(h *Header, b []byte) { b[1513] = 2 },
		"counter_range":     func(h *Header, b []byte) { binary.LittleEndian.PutUint32(b[1514:], 251) },
		"late_baseline":     func(h *Header, b []byte) { h.ActionPhaseStartOffset = 700 },
		"prep_increment":    func(h *Header, b []byte) { h.ActionPhaseStartOffset = 1800 },
		"wrong_class":       func(h *Header, b []byte) { binary.LittleEndian.PutUint32(b[21:], 1) },
		"owner_uid_changed": func(h *Header, b []byte) { creditFixtureProperty(b, 1900, 101, objectiveUIDTag, 8, 2) },
		"shared_unknown_owner": func(h *Header, b []byte) {
			b[1800] = 0x1b
			binary.LittleEndian.PutUint32(b[1801:], 999)
			binary.LittleEndian.PutUint32(b[1809:], creditScoreSlot)
			binary.LittleEndian.PutUint32(b[1813:], 201)
			binary.LittleEndian.PutUint32(b[1821:], creditScoreClass)
			creditFixtureProperty(b, 1900, 201, creditKillTag, 4, 4)
		},
	}
	for name, change := range tests {
		t.Run(name, func(t *testing.T) {
			h, b, f := creditFixture()
			change(&h, b)
			r := deriveKillCredit(h, b, f)
			if r.Complete {
				t.Fatalf("accepted invalid %s", name)
			}
		})
	}
}

func TestCreditRefusesUnknownDeathOffset(t *testing.T) {
	h, b, f := creditFixture()
	f[0].Offset = 0
	if deriveKillCredit(h, b, f).Complete {
		t.Fatal("unknown feed boundary accepted")
	}
}

func TestCreditZeroRoundAndInheritedProperty(t *testing.T) {
	h, b, f := creditFixture()
	for i := 0; i < 10; i++ {
		binary.LittleEndian.PutUint32(b[1514+i*20:], 3)
	}
	// Counter is the second property in an explicitly framed entity record.
	at := 2000
	creditFixtureProperty(b, at, 201, 0x12345678, 4, 9)
	b[at+18] = 0x22
	binary.LittleEndian.PutUint32(b[at+19:], creditKillTag)
	b[at+23] = 4
	binary.LittleEndian.PutUint32(b[at+24:], 3)
	r := deriveKillCredit(h, b, f)
	if !r.Complete || *r.Players[0].Kills != 0 || len(r.Players[0].Samples) != 3 {
		t.Fatalf("zero/inherited mismatch %+v", r)
	}
}
