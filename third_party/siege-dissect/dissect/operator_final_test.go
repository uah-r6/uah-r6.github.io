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

func TestProfessionalY11BuildsUseVerifiedActionStartSelection(t *testing.T) {
	for _, code := range []int{Y11S1_Alpha03Pro, Y11S1_Alpha03SLC, Y11S2_Alpha04Pro, Y11S2_Alpha04EML, Y11S2_Alpha04EWC, Y11S3_Alpha04EML} {
		r := &Reader{prepOperatorIDs: map[Operator]bool{Deimos: true, Zofia: true, SolidSnake: true}, Header: Header{
			CodeVersion: code,
			Teams:       [2]Team{{Role: Attack}, {Role: Defense}},
			Players: []Player{
				{Username: "repick", TeamIndex: 0, Operator: Deimos, RoleName: "ZOFIA"},
				{Username: "new operator", TeamIndex: 0, Operator: SolidSnake, RoleName: "SOLID SNAKE"},
				{Username: "defender", TeamIndex: 1, Operator: Jager, RoleName: "JAGER"},
			},
		}}
		for _, second := range []uint32{44, 43, 0, 179} {
			feedTimer(t, r, second)
		}
		if !r.Header.ActionPhaseDetected || r.Header.Players[0].Operator != Zofia ||
			r.Header.Players[0].InitialOperator != Deimos ||
			r.Header.Players[0].OperatorSource != "action_start_header" ||
			r.Header.Players[1].Operator != SolidSnake ||
			r.Header.Players[1].OperatorSource != "action_start_header" ||
			r.Header.Players[2].Operator != Jager {
			t.Fatalf("professional build %d did not select verified final operators: %+v", code, r.Header.Players)
		}
	}
	if supportsActionStartOperators(Y11S1_Alpha03) || supportsActionStartOperators(Y11S2_Alpha04Pro-1) {
		t.Fatal("unverified build was enabled")
	}
	if SolidSnake.String() != "Solid Snake" || SolidSnake.Role() != Attack {
		t.Fatal("confirmed Solid Snake ID was not mapped")
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
