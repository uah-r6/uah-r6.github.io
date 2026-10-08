package dissect

import (
	"fmt"
	"testing"
)

// Reduced structural shape of current Y11: a canceled 7 -> 5.737 plant,
// same-component declaration plus identical terminal snapshot, then a separate
// player's completed plant. No replay bytes, private identities or paths.
func terminalSnapshotFixture() (objectiveEvidence, Header, ObjectiveOccurrence) {
	h := Header{GameMode: Bomb, CodeVersion: 9918362}
	h.Teams[0].Role = Attack
	h.Teams[1].Role = Defense
	for i := 0; i < 10; i++ {
		h.Players = append(h.Players, Player{ID: uint64(i + 1), Username: fmt.Sprintf("Player%d", i), TeamIndex: i / 5})
	}
	e := objectiveEvidence{owners: map[uint32]int{100: 0, 101: 1}, declarations: []objectiveDeclaration{
		{1, 100, objectiveTimerSlot, 200, objectiveTimerClass},
		{2, 101, objectiveTimerSlot, 201, objectiveTimerClass},
		{3, 100, objectiveBodySlot, 300, objectiveBodyClass},
		{4, 101, objectiveBodySlot, 301, objectiveBodyClass},
		{60, 101, objectiveTimerSlot, 201, objectiveTimerClass},
	}}
	phase := func(record int, entity uint32, value uint64, timer string, progress uint64) {
		e.properties = append(e.properties, objectiveProperty{record: record, offset: record + 1, end: record + 2, entity: entity, tag: objectivePhaseTag, size: 4, bits: value},
			objectiveProperty{record: record, offset: record + 3, end: record + 4, entity: entity, tag: objectiveProgressTag, size: 4, bits: progress},
			objectiveProperty{record: record, offset: record + 5, end: record + 6, entity: entity, tag: objectiveTimerTag, size: len(timer), text: timer})
	}
	e.properties = append(e.properties, objectiveProperty{record: 5, offset: 5, end: 6, entity: 300, tag: objectiveBodyState, size: 4, bits: 0},
		objectiveProperty{record: 6, offset: 6, end: 7, entity: 301, tag: objectiveBodyState, size: 4, bits: 0})
	phase(10, 201, 0, "6.968", 0)
	phase(20, 201, 2, "5.737", 1062342746)
	phase(70, 201, 2, "5.737", 1062342746) // same terminal update after same-component redeclaration
	phase(100, 200, 0, "6.986", 0)
	phase(120, 200, 2, "0", 0)
	return e, h, ObjectiveOccurrence{Kind: "plant", Source: "defuser_state_v1", PlantStateOffset: 150}
}

func TestIdenticalClosedObjectiveTerminalIsNotAnUnboundInteraction(t *testing.T) {
	e, h, o := terminalSnapshotFixture()
	e.splitEpisodes(h.CodeVersion)
	if len(e.orphans) != 0 || len(e.episodes) != 2 {
		t.Fatalf("duplicate terminal changed inventory: %+v", e)
	}
	actor, reason := e.selectActor(h, nil, o)
	if actor != 0 || reason != "completing_timer_owner_v1" {
		t.Fatalf("completed player must win over canceled snapshot: %d %s", actor, reason)
	}
	if e.complete(e.episodes[0], 0) {
		t.Fatal("canceled attempt became a completed attempt")
	}
}

func TestClosedTerminalSnapshotStillRequiresExactFieldsAndContinuousOwnership(t *testing.T) {
	for _, mutation := range []string{"timer", "progress", "phase", "width", "missing_field", "new_run", "intervening_state", "intervening_progress", "new_owner", "shared_owner", "clear_restore", "class"} {
		t.Run(mutation, func(t *testing.T) {
			e, h, o := terminalSnapshotFixture()
			for i := range e.properties {
				p := &e.properties[i]
				if p.record != 70 {
					continue
				}
				switch mutation {
				case "timer":
					if p.tag == objectiveTimerTag {
						p.text = "5.736"
					}
				case "progress":
					if p.tag == objectiveProgressTag {
						p.bits++
					}
				case "phase":
					if p.tag == objectivePhaseTag {
						p.bits = 3
					}
				case "width":
					if p.tag == objectivePhaseTag {
						p.size = 1
					}
				case "missing_field":
					if p.tag == objectiveProgressTag {
						p.tag = 0
					}
				}
			}
			switch mutation {
			case "new_run":
				e.properties = append(e.properties, objectiveProperty{record: 50, offset: 51, end: 52, entity: 201, tag: objectivePhaseTag, size: 4, bits: 0})
			case "intervening_state":
				e.properties = append(e.properties, objectiveProperty{record: 50, offset: 51, end: 52, entity: 201, tag: objectivePhaseTag, size: 4, bits: 3})
			case "intervening_progress":
				e.properties = append(e.properties, objectiveProperty{record: 50, offset: 51, end: 52, entity: 201, tag: objectiveProgressTag, size: 4, bits: 1062342747})
			case "new_owner":
				e.declarations = append(e.declarations[:4], objectiveDeclaration{60, 101, objectiveTimerSlot, 0, 0}, objectiveDeclaration{61, 100, objectiveTimerSlot, 201, objectiveTimerClass})
			case "shared_owner":
				e.declarations = append(e.declarations, objectiveDeclaration{61, 100, objectiveTimerSlot, 201, objectiveTimerClass})
			case "clear_restore":
				e.declarations = append(e.declarations[:4], objectiveDeclaration{50, 101, objectiveTimerSlot, 0, 0}, objectiveDeclaration{60, 101, objectiveTimerSlot, 201, objectiveTimerClass})
			case "class":
				e.declarations[4].class = objectiveVariantClass
			}
			e.splitEpisodes(h.CodeVersion)
			actor, reason := e.selectActor(h, nil, o)
			if actor >= 0 {
				t.Fatalf("uncertain %s snapshot attributed an actor (%s)", mutation, reason)
			}
		})
	}
}
