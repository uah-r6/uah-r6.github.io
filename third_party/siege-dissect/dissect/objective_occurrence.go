package dissect

import (
	"bytes"
	"encoding/binary"
	"sort"
)

// ObjectiveOccurrence retains round-level completion evidence independently
// from conservative actor attribution. Unresolved actors remain nil.
type ObjectiveOccurrence struct {
	Kind             string  `json:"kind"`
	Source           string  `json:"source"`
	Actor            *string `json:"actor"`
	PlantStateOffset int64   `json:"plantStateOffset"`
	ActorID          uint64  `json:"actorID,omitempty"`
	ActorSource      string  `json:"actorSource,omitempty"`
	ActorReason      string  `json:"actorReason,omitempty"`
}

type objectiveState struct {
	offset int
	entity uint32
	value  byte
}

// objectiveStates follows contiguous typed fields only. 0x23 introduces an
// entity ref; 0x22 continues that same record. Unknown encodings stop the chain.
// This is deliberately not a backward proximity search for a convenient ID.
func objectiveStates(data []byte) []objectiveState {
	found := make(map[int]objectiveState)
	for cursor := 0; cursor < len(data); {
		rel := bytes.IndexByte(data[cursor:], 0x23)
		if rel < 0 {
			break
		}
		start := cursor + rel
		cursor = start + 1
		if start+14 > len(data) || binary.LittleEndian.Uint32(data[start+5:start+9]) != 0 {
			continue
		}
		entity := binary.LittleEndian.Uint32(data[start+1 : start+5])
		for at := start + 9; at+5 < len(data); {
			size := int(data[at+4])
			if (size != 1 && size != 2 && size != 4 && size != 8) || at+5+size > len(data) {
				break
			}
			if binary.LittleEndian.Uint32(data[at:at+4]) == 0x08F439FF && size == 1 {
				found[at] = objectiveState{at, entity, data[at+5]}
			}
			end := at + 5 + size
			if end >= len(data) || data[end] != 0x22 {
				break
			}
			at = end + 1
		}
	}
	states := make([]objectiveState, 0, len(found))
	for _, state := range found {
		states = append(states, state)
	}
	sort.Slice(states, func(i, j int) bool { return states[i].offset < states[j].offset })
	return states
}

func inferObjectiveOccurrences(states []objectiveState, side TeamRole) []ObjectiveOccurrence {
	if side != Attack && side != Defense {
		return nil
	}
	var plant *objectiveState
	for i := range states {
		if states[i].value == 1 {
			if plant != nil {
				return nil
			}
			plant = &states[i]
		}
	}
	if plant == nil {
		return nil
	}
	for _, state := range states {
		if state.entity != plant.entity || state.offset < plant.offset || state.value > 1 {
			return nil
		}
	}
	result := []ObjectiveOccurrence{{Kind: "plant", Source: "defuser_state_v1", PlantStateOffset: int64(plant.offset)}}
	// In Bomb, defenders winning after a completed plant requires a disable.
	// This also covers builds whose round end omits state0. State0 alone can
	// be cleanup after an Attack win, and is never sufficient for a disable.
	if side == Defense {
		result = append(result, ObjectiveOccurrence{Kind: "disable", Source: "defuser_state_and_defense_win_v1", PlantStateOffset: int64(plant.offset)})
	}
	return result
}

func (r *Reader) resolveObjectiveOccurrences() {
	r.Header.ObjectiveOccurrences = nil
	if r.Header.GameMode != Bomb {
		return
	}
	// Use an independently unambiguous physical score increment. Legacy
	// timer-derived WinCondition labels are not evidence for this detector.
	d0 := r.Header.Teams[0].Score - r.Header.Teams[0].StartingScore
	d1 := r.Header.Teams[1].Score - r.Header.Teams[1].StartingScore
	winner := -1
	if d0 == 1 && d1 == 0 {
		winner = 0
	} else if d1 == 1 && d0 == 0 {
		winner = 1
	}
	if winner < 0 {
		return
	}
	r.Header.ObjectiveOccurrences = inferObjectiveOccurrences(objectiveStates(r.b), r.Header.Teams[winner].Role)
}
