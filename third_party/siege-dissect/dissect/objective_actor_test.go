package dissect

import (
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"math"
	"os"
	"path/filepath"
	"strconv"
	"testing"
)

func objectiveFixtureHash(t *testing.T, s string) uint32 {
	t.Helper()
	b, err := hex.DecodeString(s)
	if err != nil || len(b) != 4 {
		t.Fatalf("invalid fixture hash %q", s)
	}
	return binary.LittleEndian.Uint32(b)
}

// These reduced public fixtures contain parsed structural evidence only,
// never replay bytes, UUIDs or private paths. They preserve all competitors.
type objectiveFixtureInput struct {
	Header Header            `json:"header"`
	Owners map[string]string `json:"owners"`
	Slots  []struct {
		Owner        uint32
		Slot         string
		Declarations []struct {
			Offset    int
			Component uint32
			Class     string `json:"class_hash"`
		}
	} `json:"slots"`
	Properties []struct {
		Entity       uint32
		Hash         string
		Size, Offset int
		Value        uint64
	} `json:"properties"`
	Deaths []struct {
		Offset   int
		Feedback MatchUpdate
	} `json:"deaths"`
	Feedback []MatchUpdate `json:"full_feedback"`
	Observed struct {
		Orphans []struct {
			Record int `json:"record_start"`
		} `json:"orphan_records"`
		Episodes []struct {
			Entity  uint32
			Phase   int    `json:"state"`
			Start   int    `json:"start_record"`
			End     int    `json:"end_offset"`
			Reason  string `json:"end_reason"`
			Binding struct {
				Owner        uint32
				Player, Slot string
				Class        string `json:"class_hash"`
				Declaration  int    `json:"declaration_offset"`
			}
			Samples []struct {
				Offset  int
				Seconds *float64
			}
			Records []struct{ Fields []struct{ Offset, Size int } }
		} `json:"episodes"`
	} `json:"observed"`
}

func fixtureEvidence(t *testing.T, in objectiveFixtureInput) (objectiveEvidence, []MatchUpdate) {
	t.Helper()
	e := objectiveEvidence{owners: map[uint32]int{}}
	for key, name := range in.Owners {
		entity, err := strconv.ParseUint(key, 10, 32)
		if err != nil {
			t.Fatal(err)
		}
		for i, p := range in.Header.Players {
			if p.Username == name {
				e.owners[uint32(entity)] = i
			}
		}
	}
	for _, s := range in.Slots {
		for _, d := range s.Declarations {
			e.declarations = append(e.declarations, objectiveDeclaration{d.Offset, s.Owner, objectiveFixtureHash(t, s.Slot), d.Component, objectiveFixtureHash(t, d.Class)})
		}
	}
	// Fixture slots are grouped by owner; runtime declarations are temporal.
	for i := 1; i < len(e.declarations); i++ {
		for j := i; j > 0 && e.declarations[j].offset < e.declarations[j-1].offset; j-- {
			e.declarations[j], e.declarations[j-1] = e.declarations[j-1], e.declarations[j]
		}
	}
	for _, p := range in.Properties {
		e.properties = append(e.properties, objectiveProperty{entity: p.Entity, tag: objectiveFixtureHash(t, p.Hash), size: p.Size, offset: p.Offset, bits: p.Value})
	}
	for _, r := range in.Observed.Episodes {
		player := -1
		for i, p := range in.Header.Players {
			if p.Username == r.Binding.Player {
				player = i
			}
		}
		ep := objectiveEpisode{entity: r.Entity, route: objectiveRoute{r.Binding.Owner, objectiveFixtureHash(t, r.Binding.Slot), objectiveFixtureHash(t, r.Binding.Class), r.Binding.Declaration, player}, phase: r.Phase, start: r.Start, end: r.End, terminal: r.Reason}
		if r.Reason != "ownership_declaration_boundary" {
			ep.end = 0
			if len(r.Records) > 0 {
				for _, p := range r.Records[len(r.Records)-1].Fields {
					if p.Offset+5+p.Size > ep.end {
						ep.end = p.Offset + 5 + p.Size
					}
				}
			}
		}
		for _, s := range r.Samples {
			seconds := math.NaN()
			if s.Seconds != nil {
				seconds = *s.Seconds
			}
			ep.samples = append(ep.samples, objectiveSample{s.Offset, seconds})
		}
		e.episodes = append(e.episodes, ep)
	}
	for _, o := range in.Observed.Orphans {
		e.orphans = append(e.orphans, o.Record)
	}
	feedback := []MatchUpdate{}
	for _, d := range in.Deaths {
		f := d.Feedback
		f.killOffset = d.Offset
		feedback = append(feedback, f)
	}
	for _, f := range in.Feedback {
		if f.Type == PlayerLeave {
			feedback = append(feedback, f)
		}
	}
	return e, feedback
}

func TestObjectiveActorRealConsumedCompleterAndDisableControls(t *testing.T) {
	for _, file := range []string{"objective-plant-completer.json", "objective-disable-owner.json"} {
		data, err := os.ReadFile(filepath.Join("..", "..", "..", "tests", "fixtures", file))
		if err != nil {
			t.Fatal(err)
		}
		var fixture struct {
			Cases []struct {
				Match, Round int
				Proposal     *string `json:"expected_proposal"`
				Input        objectiveFixtureInput
			}
		}
		if err = json.Unmarshal(data, &fixture); err != nil {
			t.Fatal(err)
		}
		for i, row := range fixture.Cases {
			t.Run(file+"/"+strconv.Itoa(i), func(t *testing.T) {
				kind := "plant"
				if file == "objective-disable-owner.json" {
					kind = "disable"
				}
				// This is the historical disable-only unsupported-plant record,
				// not an assertion that reviewed Aiden evidence must stay wrong.
				if kind == "disable" && len(row.Input.Header.ObjectiveOccurrences) == 1 && row.Input.Header.ObjectiveOccurrences[0].Kind == "plant" {
					return
				}
				e, feed := fixtureEvidence(t, row.Input)
				occurrence := ObjectiveOccurrence{Kind: kind}
				for _, o := range row.Input.Header.ObjectiveOccurrences {
					if o.Kind == kind {
						occurrence = o
					}
				}
				player, reason := e.selectActor(row.Input.Header, feed, occurrence)
				if row.Proposal == nil {
					if player >= 0 {
						t.Fatalf("expected abstention, got %s", row.Input.Header.Players[player].Username)
					}
					return
				}
				if player < 0 || row.Input.Header.Players[player].Username != *row.Proposal {
					t.Fatalf("wanted %s got player%d reason%s", *row.Proposal, player, reason)
				}
			})
		}
	}
}

func objectiveTestRecord(entity uint32, tag uint32, payload []byte) []byte {
	data := make([]byte, 14+len(payload))
	data[0] = 0x23
	binary.LittleEndian.PutUint32(data[1:5], entity)
	binary.LittleEndian.PutUint32(data[9:13], tag)
	data[13] = byte(len(payload))
	copy(data[14:], payload)
	return data
}
func objectiveTestContinuation(tag uint32, payload []byte) []byte {
	data := make([]byte, 6+len(payload))
	data[0] = 0x22
	binary.LittleEndian.PutUint32(data[1:5], tag)
	data[5] = byte(len(payload))
	copy(data[6:], payload)
	return data
}
func objectiveTestDeclaration(owner, slot, component, class uint32) []byte {
	data := make([]byte, 25)
	data[0] = 0x1b
	binary.LittleEndian.PutUint32(data[1:5], owner)
	binary.LittleEndian.PutUint32(data[9:13], slot)
	binary.LittleEndian.PutUint32(data[13:17], component)
	binary.LittleEndian.PutUint32(data[21:25], class)
	return data
}
func objectiveTestUint(value uint64, size int) []byte {
	data := make([]byte, size)
	for i := range data {
		data[i] = byte(value >> uint(8*i))
	}
	return data
}

func TestObjectiveComponentFramingIncludesFirstPropertyAndTerminalTimer(t *testing.T) {
	data := objectiveTestDeclaration(1, objectiveTimerSlot, 2, objectiveTimerClass)
	data = append(data, objectiveTestRecord(2, objectivePhaseTag, objectiveTestUint(0, 4))...)
	data = append(data, objectiveTestContinuation(objectiveTimerTag, []byte("7.000"))...)
	data = append(data, objectiveTestRecord(2, objectivePhaseTag, objectiveTestUint(2, 4))...)
	data = append(data, objectiveTestContinuation(objectiveTimerTag, []byte("0.004"))...)
	ds, ps := objectiveComponentFields(data)
	e := objectiveEvidence{declarations: ds, properties: ps, owners: map[uint32]int{1: 0}}
	e.splitEpisodes(9883691)
	if len(e.episodes) != 1 || !e.complete(e.episodes[0], 0) || e.episodes[0].end != len(data) || e.episodes[0].samples[1].seconds != .004 {
		t.Fatalf("bad complete episode %#v", e.episodes)
	}
	// Neither nearzero nor state2 creates occurrence or actor by itself.
	h := Header{GameMode: Bomb}
	if p, _ := e.selectActor(h, nil, ObjectiveOccurrence{Kind: "plant"}); p >= 0 {
		t.Fatal("actor without verified plant")
	}
}

func TestObjectiveNumericUIDOwnersNeverChooseDuplicatesOrChangedIdentity(t *testing.T) {
	players := []Player{{ID: 101, Username: "one"}, {ID: 102, Username: "two"}}
	fields := []objectiveProperty{{entity: 1, tag: objectiveUIDTag, size: 8, bits: 101}, {entity: 2, tag: objectiveUIDTag, size: 8, bits: 101}, {entity: 3, tag: objectiveUIDTag, size: 8, bits: 102}, {entity: 3, tag: objectiveUIDTag, size: 8, bits: 103}}
	if owners := objectiveOwners(players, fields); len(owners) != 0 {
		t.Fatalf("ambiguous identity accepted %v", owners)
	}
}

func TestObjectiveSharedUnknownOwnerAndSlotReplacementInvalidateRoute(t *testing.T) {
	e := objectiveEvidence{owners: map[uint32]int{1: 0}, declarations: []objectiveDeclaration{{1, 1, objectiveTimerSlot, 2, objectiveTimerClass}, {20, 99, objectiveTimerSlot, 2, objectiveTimerClass}, {30, 1, objectiveTimerSlot, 0, 0}}}
	if _, ok := e.binding(2, 10); !ok {
		t.Fatal("unique route missing")
	}
	if _, ok := e.binding(2, 25); ok {
		t.Fatal("unknown owner sharing accepted")
	}
	if _, ok := e.binding(2, 35); ok {
		t.Fatal("cleared ownership borrowed unknown player")
	}
}

func TestObjectivePlantEligibilityAndCompleterSafeguards(t *testing.T) {
	data, err := os.ReadFile(filepath.Join("..", "..", "..", "tests", "fixtures", "objective-plant-completer.json"))
	if err != nil {
		t.Fatal(err)
	}
	var fixture struct {
		Cases []struct{ Input objectiveFixtureInput }
	}
	if err = json.Unmarshal(data, &fixture); err != nil {
		t.Fatal(err)
	}
	for _, change := range []string{"death", "unknown_death", "last_opponents_dead", "body_dbno", "competing", "later_partial", "no_anchor", "leave", "unknown_class"} {
		t.Run(change, func(t *testing.T) {
			in := fixture.Cases[0].Input
			e, feed := fixtureEvidence(t, in)
			h := in.Header
			o := h.ObjectiveOccurrences[0]
			actor, reason := e.selectActor(h, feed, o)
			if actor < 0 {
				t.Fatal("positive fixture invalid", reason)
			}
			ep := e.episodes[0]
			switch change {
			case "death":
				feed = append(feed, MatchUpdate{Type: Death, Username: h.Players[actor].Username, killOffset: ep.start + 1})
			case "unknown_death":
				feed = append(feed, MatchUpdate{Type: Death, Username: h.Players[actor].Username})
			case "last_opponents_dead":
				for _, p := range h.Players {
					if p.TeamIndex != h.Players[actor].TeamIndex {
						feed = append(feed, MatchUpdate{Type: Kill, Username: h.Players[actor].Username, Target: p.Username, killOffset: ep.start + 1})
					}
				}
			case "body_dbno":
				for i := range e.properties {
					if e.properties[i].tag == objectiveBodyState {
						e.properties[i].bits = 3
					}
				}
			case "competing":
				e.episodes = append(e.episodes, ep)
			case "later_partial":
				ep.start = ep.end + 1
				ep.samples = []objectiveSample{{ep.start + 1, 7}, {ep.start + 2, 3}}
				ep.end = ep.start + 3
				e.episodes = append(e.episodes, ep)
			case "no_anchor":
				o.PlantStateOffset = 0
			case "leave":
				feed = append(feed, MatchUpdate{Type: PlayerLeave})
			case "unknown_class":
				e.episodes[0].route.class = 1
			}
			if p, r := e.selectActor(h, feed, o); p >= 0 {
				t.Fatal("unsafe credit", change, p, r)
			}
		})
	}
}
