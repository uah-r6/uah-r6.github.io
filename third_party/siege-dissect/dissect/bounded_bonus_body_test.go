package dissect

import (
	"math"
	"sort"
	"testing"
)

func boundedBonusFixture() (objectiveEvidence, Header, ObjectiveOccurrence) {
	e, h, o := terminalSnapshotFixture()
	e.properties[0].bits = 1
	for i, p := range []objectiveProperty{
		{tag: 0xc9762625, bits: 117}, {tag: 0x72a64911, bits: 110},
		{tag: 0xdad23f01, bits: 130}, {tag: 0x7bcfad80, bits: uint64(math.Float32bits(7.0 / 110.0))},
	} {
		p.offset = 30 + 10*i
		p.record = p.offset
		p.end = p.offset + 9
		p.entity = 300
		p.size = 4
		e.properties = append(e.properties, p)
	}
	e.properties = append(e.properties, objectiveProperty{offset: 111, record: 110, end: 120, entity: 300, tag: objectiveBodyState, size: 4, bits: 0})
	sort.Slice(e.properties, func(i, j int) bool { return e.properties[i].offset < e.properties[j].offset })
	return e, h, o
}

func TestBonusNumericsRequireReturnToKnownActiveBodyBeforeCompletion(t *testing.T) {
	e, h, o := boundedBonusFixture()
	e.splitEpisodes(h.CodeVersion)
	if e.activeBody(e.episodes[1]) {
		t.Fatal("raw state 1 must remain outside core allowlist")
	}
	actor, reason := e.selectActor(h, nil, o)
	if actor != 0 || reason != boundedBonusSource {
		t.Fatalf("bounded completion rejected: %d %s", actor, reason)
	}
}

func TestBoundedBonusProofFailsClosed(t *testing.T) {
	for _, mutation := range []string{"no_return", "late_return", "downed", "dead", "unknown", "missing_hp", "hp_low", "ceiling", "fraction", "width", "shared_body", "body_replace", "numeric_old_owner", "two_completers", "canceled", "wrong_side", "leave", "known_dead"} {
		t.Run(mutation, func(t *testing.T) {
			e, h, o := boundedBonusFixture()
			feed := []MatchUpdate{}
			for i := range e.properties {
				p := &e.properties[i]
				switch mutation {
				case "no_return":
					if p.entity == 300 && p.tag == objectiveBodyState {
						p.bits = 1
					}
				case "late_return":
					if p.offset == 111 {
						p.offset = 140
						p.end = 149
					}
				case "downed":
					if p.offset == 5 {
						p.bits = 3
					}
				case "dead":
					if p.offset == 5 {
						p.bits = 4
					}
				case "unknown":
					if p.offset == 5 {
						p.bits = 5
					}
				case "missing_hp":
					if p.tag == 0xc9762625 {
						p.tag = 0
					}
				case "hp_low":
					if p.tag == 0xc9762625 {
						p.bits = 90
					}
				case "ceiling":
					if p.tag == 0xdad23f01 {
						p.bits = 131
					}
				case "fraction":
					if p.tag == 0x7bcfad80 {
						p.bits = uint64(math.Float32bits(.4))
					}
				case "width":
					if p.tag == 0xc9762625 {
						p.size = 1
					}
				case "canceled":
					if p.entity == 200 && p.tag == objectiveTimerTag && p.record == 120 {
						p.text = "5.737"
					}
				case "two_completers":
					if p.entity == 201 && p.tag == objectiveTimerTag && p.record >= 20 {
						p.text = "0"
					}
				}
			}
			switch mutation {
			case "shared_body":
				e.declarations = append(e.declarations, objectiveDeclaration{90, 101, objectiveBodySlot, 300, objectiveBodyClass})
			case "body_replace":
				e.declarations = append(e.declarations, objectiveDeclaration{105, 100, objectiveBodySlot, 999, objectiveBodyClass})
			case "numeric_old_owner":
				e.declarations[2].offset = 80
			case "wrong_side":
				h.Players[0].TeamIndex = 1
			case "leave":
				feed = append(feed, MatchUpdate{Type: PlayerLeave})
			case "known_dead":
				f := MatchUpdate{Type: Death, Username: h.Players[0].Username}
				f.killOffset = 80
				feed = append(feed, f)
			}
			sort.Slice(e.properties, func(i, j int) bool { return e.properties[i].offset < e.properties[j].offset })
			sort.Slice(e.declarations, func(i, j int) bool { return e.declarations[i].offset < e.declarations[j].offset })
			e.splitEpisodes(h.CodeVersion)
			actor, _ := e.selectActor(h, feed, o)
			if actor >= 0 {
				t.Fatalf("unsafe %s accepted as %d", mutation, actor)
			}
		})
	}
}
