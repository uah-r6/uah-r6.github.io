package dissect

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"testing"
)

func reconnectFixture(t *testing.T) CreditStructuralEvidence {
	t.Helper()
	b, err := os.ReadFile("../../../tests/fixtures/participant-inactive-reconnect-y11.json")
	if err != nil {
		t.Fatal(err)
	}
	var e CreditStructuralEvidence
	decoder := json.NewDecoder(bytes.NewReader(b))
	decoder.UseNumber()
	if err = decoder.Decode(&e); err != nil {
		t.Fatal(err)
	}
	return e
}

func TestInactiveReconnectRealStructure(t *testing.T) {
	e := reconnectFixture(t)
	credit := ValidateKillCreditEvidence(e)
	if !credit.Complete || len(credit.Players) != 9 || !explicitInventoryValid(e.Header) || explicitEmptyInventoryValid(e.Header) {
		t.Fatalf("inactive reconnect refused: %+v", credit)
	}
	want := []uint32{0, 2, 0, 1, 1, 0, 0, 2, 0}
	for i, p := range credit.Players {
		if p.Kills == nil || *p.Kills != want[i] {
			t.Fatalf("wrong direct counter: %+v", p)
		}
	}
	if credit.ActionStartOffset != 72026634 {
		t.Fatal("action boundary changed")
	}
}

func TestInactiveReconnectProofRefusesUnsafeMutations(t *testing.T) {
	for _, kind := range []string{"missing_proof", "source", "slot_name", "slot_profile", "slot_uid", "operator", "action", "body_present_at_action", "late_uid", "known_uid", "active_body", "health", "missing_vital", "repeated_vital", "score_owner", "score_component", "score_declaration", "initial_counter", "restored_range", "missing_counter", "wrong_team"} {
		t.Run(kind, func(t *testing.T) {
			e := reconnectFixture(t)
			h := e.Header
			var p inactiveReconnect
			raw, _ := json.Marshal(h.ParticipantEvidence["inactive_reconnect"])
			json.Unmarshal(raw, &p)
			proof := h.ParticipantEvidence
			slots := proof["slots"].([]any)
			slot := slots[p.Slot].(map[string]any)
			switch kind {
			case "missing_proof":
				h.ParticipantEvidence = nil
			case "source":
				proof["source"] = "unsupported"
			case "slot_name":
				slot["username"] = "unknown"
			case "slot_profile":
				slot["profile_id"] = h.Players[0].ProfileID
			case "slot_uid":
				slot["uid"] = uint64(10)
			case "operator":
				slot["operator_id"] = uint64(1)
			case "action":
				h.ActionPhaseStartOffset++
			case "body_present_at_action":
				p.BodyOffset = int(h.ActionPhaseStartOffset) - 1
			case "late_uid":
				p.UIDOffset = p.ScoreOffset
			case "known_uid":
				p.UID = h.Players[0].ID
			case "active_body":
				for i := range p.BodyFields {
					if p.BodyFields[i].Tag == objectiveBodyState {
						p.BodyFields[i].Bits = 0
					}
				}
			case "health":
				p.BodyFields[0].Bits = 100
			case "missing_vital":
				p.BodyFields = p.BodyFields[1:]
			case "repeated_vital":
				p.BodyFields[1] = p.BodyFields[0]
			case "score_owner":
				p.Counters[1].Owner++
			case "score_component":
				p.Counters[1].Component++
			case "score_declaration":
				p.Counters[1].DeclarationOffset++
			case "initial_counter":
				p.Counters[0].Value = 1
			case "restored_range":
				p.Counters[1].Value = 251
			case "missing_counter":
				p.Counters = p.Counters[:1]
			case "wrong_team":
				p.Team = 0
			}
			if h.ParticipantEvidence != nil {
				proof["inactive_reconnect"] = p
			}
			if explicitInventoryValid(h) {
				t.Fatalf("unsafe %s accepted", kind)
			}
		})
	}
}

// Optional smoke/capture uses only a local .rec, never SQLite. Capture retains
// typed observations, replacing every account/profile/name with an ordinal.
func TestInactiveReconnectLocalReplay(t *testing.T) {
	path := os.Getenv("R6_TEST_INACTIVE_REPLAY")
	if path == "" {
		t.Skip("optional local inactive-reconnect replay")
	}
	in, err := os.Open(path)
	if err != nil {
		t.Fatal(err)
	}
	defer in.Close()
	h, credit, err := ReadKillCredit(in)
	if err != nil || !credit.Complete || len(h.Players) != 9 || h.ParticipantEvidence == nil || h.ParticipantEvidence["source"] != inactiveReconnectSource {
		t.Fatalf("production reader: %v %+v", err, credit)
	}
	out := os.Getenv("R6_TEST_INACTIVE_FIXTURE")
	if out == "" {
		return
	}
	in.Seek(0, 0)
	r, err := NewReader(in)
	if err != nil {
		t.Fatal(err)
	}
	data := r.b
	if err = r.Read(); !Ok(err) {
		t.Fatal(err)
	}
	names, profiles, uids := map[string]string{}, map[string]string{}, map[uint64]uint64{}
	anonymous := Header{CodeVersion: h.CodeVersion, ActionPhaseDetected: true, ActionPhaseStartOffset: h.ActionPhaseStartOffset, Teams: h.Teams}
	for i, p := range h.Players {
		name := fmt.Sprintf("Player%d", i+1)
		profile := fmt.Sprintf("00000000-0000-0000-0000-%012d", i+1)
		uid := uint64(i + 1)
		names[p.Username] = name
		profiles[p.Username] = profile
		uids[p.ID] = uid
		anonymous.Players = append(anonymous.Players, Player{Username: name, ProfileID: profile, ID: uid, TeamIndex: p.TeamIndex})
	}
	for i := range anonymous.Teams {
		anonymous.Teams[i].Name = ""
	}
	proof := h.ParticipantEvidence
	slots := proof["slots"].([]map[string]any)
	var reconnect inactiveReconnect
	raw, _ := json.Marshal(proof["inactive_reconnect"])
	json.Unmarshal(raw, &reconnect)
	uids[reconnect.UID] = 10
	names[reconnect.Name] = "Player10"
	reconnect.UID = 10
	reconnect.Name = "Player10"
	proof["inactive_reconnect"] = reconnect
	for i, s := range slots {
		name := s["username"].(string)
		s["username"] = names[name]
		if i != reconnect.Slot {
			s["profile_id"] = profiles[name]
			s["uid"] = uids[s["uid"].(uint64)]
		}
	}
	anonymous.ParticipantEvidence = proof
	e := CreditStructuralEvidence{Header: anonymous}
	decls, fields := objectiveComponentFields(data)
	owners := objectiveOwners(h.Players, fields)
	owners[reconnect.Owner] = 9
	components := map[uint32]bool{}
	for _, d := range decls {
		if _, ok := owners[d.owner]; ok {
			components[d.component] = true
			e.Declarations = append(e.Declarations, CreditDeclaration{d.offset, d.owner, d.slot, d.component, d.class})
		}
	}
	for _, f := range fields {
		if f.tag == objectiveUIDTag {
			uid, ok := uids[f.bits]
			if !ok {
				t.Fatal("unexpected UID")
			}
			e.Properties = append(e.Properties, CreditProperty{f.offset, f.entity, f.tag, f.size, uid})
		}
	}
	for _, f := range creditCounterFields(data) {
		if components[f.entity] {
			e.Properties = append(e.Properties, CreditProperty{f.offset, f.entity, f.tag, f.size, f.bits})
		}
	}
	for _, f := range credit.Finishes {
		f.Feedback.Username = names[f.Feedback.Username]
		f.Feedback.Target = names[f.Feedback.Target]
		e.Finishes = append(e.Finishes, f)
	}
	if !ValidateKillCreditEvidence(e).Complete {
		t.Fatal("sanitized structural fixture invalid")
	}
	raw, err = json.MarshalIndent(e, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(out, append(raw, '\n'), 0600); err != nil {
		t.Fatal(err)
	}
}
