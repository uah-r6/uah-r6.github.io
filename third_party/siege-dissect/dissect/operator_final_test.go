package dissect

import (
	"encoding/binary"
	"testing"
)

func feedTimer(t *testing.T, r *Reader, seconds uint32) {
	t.Helper()
	r.b = make([]byte, 6)
	r.b[0] = 4
	binary.LittleEndian.PutUint32(r.b[1:], seconds)
	r.offset = 0
	if err := readTime(r); err != nil {
		t.Fatal(err)
	}
}

func TestY11OperatorFreezesAtActionStart(t *testing.T) {
	r := &Reader{prepOperatorIDs: map[Operator]bool{Deimos: true, Zofia: true}, Header: Header{
		CodeVersion: Y11S3_Alpha04,
		Teams:       [2]Team{{Role: Attack}, {Role: Defense}},
		Players: []Player{
			{Username: "Lgon.", TeamIndex: 0, Operator: Deimos, RoleName: "ZOFIA"},
			{Username: "Defender", TeamIndex: 1, Operator: Jager, RoleName: "JÄGER"},
		},
	}}
	for _, second := range []uint32{44, 43, 0} {
		feedTimer(t, r, second)
	}
	if r.Header.Players[0].Operator != Deimos || r.Header.ActionPhaseDetected {
		t.Fatal("attacker changed before action phase")
	}
	feedTimer(t, r, 179)
	attacker := r.Header.Players[0]
	if !r.Header.ActionPhaseDetected || attacker.Operator != Zofia ||
		attacker.InitialOperator != Deimos || attacker.OperatorSource != "action_start_header" {
		t.Fatalf("wrong action-start selection: %+v", attacker)
	}
	r.b = make([]byte, 10)
	binary.LittleEndian.PutUint64(r.b[1:], uint64(Ash))
	r.offset = 0
	if err := readAtkOpSwap(r); err != nil {
		t.Fatal(err)
	}
	if r.Header.Players[0].Operator != Zofia || r.Header.Players[1].Operator != Jager {
		t.Fatal("later packets changed frozen attacker or defender")
	}
}

func TestY11UnknownOrMissingHeaderOperatorIsUnresolved(t *testing.T) {
	r := &Reader{prepOperatorIDs: map[Operator]bool{Capitao: true, Jager: true}, Header: Header{
		CodeVersion: Y11S3_Alpha04,
		Teams:       [2]Team{{Role: Attack}, {Role: Defense}},
		Players: []Player{
			{Username: "missing", TeamIndex: 0, Operator: Twitch},
			{Username: "new", TeamIndex: 0, Operator: Ash, RoleName: "SOLID SNAKE"},
			{Username: "accent", TeamIndex: 0, Operator: Zofia, RoleName: "CAPITÃO"},
			{Username: "wrong side", TeamIndex: 0, Operator: Buck, RoleName: "JÄGER"},
			{Username: "no packet", TeamIndex: 0, Operator: Ash, RoleName: "BUCK"},
			{Username: "defender", TeamIndex: 1, Operator: Jager},
		},
	}}
	r.resolveActionStartOperators()
	for _, p := range r.Header.Players[:2] {
		if p.Operator != 0 || p.OperatorSource != "unresolved" {
			t.Fatalf("expected unresolved: %+v", p)
		}
	}
	if r.Header.Players[2].Operator != Capitao || r.Header.Players[3].Operator != 0 {
		t.Fatal("accent mapping or wrong-side rejection failed")
	}
	if r.Header.Players[4].Operator != 0 || r.Header.Players[5].Operator != Jager {
		t.Fatal("unseen operator or defense preservation failed")
	}
}

func TestY11MalformedCandidateIsIgnored(t *testing.T) {
	r := &Reader{Header: Header{CodeVersion: Y11S3_Alpha04}, b: []byte{8, 1}}
	if err := readAtkOpSwap(r); err != nil || len(r.prepOperatorIDs) != 0 {
		t.Fatalf("malformed packet was accepted or fatal: %v", err)
	}
}
