package dissect

import "strings"

// Prove the legacy "disable" was the second zero-valued sample of the SAME
// planting timer, before the global plant transition. This is stronger than
// an absent parser event or a guessed actor. A completed disable is impossible
// in the single-plant, independently observed Attack-win outcome.
func (e *objectiveEvidence) noDisableProof(h Header, feedback []MatchUpdate, o ObjectiveOccurrence) map[string]any {
	if o.Kind != "plant" || o.Actor == nil || len(h.ObjectiveOccurrences) != 1 || o.PlantStateOffset <= 0 {
		return nil
	}
	winning := -1
	for i, t := range h.Teams {
		if t.Score-t.StartingScore == 1 {
			if winning >= 0 {
				return nil
			}
			winning = i
		} else if t.Score != t.StartingScore {
			return nil
		}
	}
	if winning < 0 || !h.Teams[winning].Won || h.Teams[winning].Role != Attack {
		return nil
	}
	legacy := 0
	for _, f := range feedback {
		if f.Type == DefuserDisableComplete {
			legacy++
		}
	}
	if legacy == 0 {
		return nil
	}
	var complete *objectiveEpisode
	for i := range e.episodes {
		ep := &e.episodes[i]
		if ep.phase == 1 {
			return nil
		}
		if e.complete(*ep, 0) {
			if complete != nil {
				return nil
			}
			complete = ep
		}
	}
	if complete == nil || complete.end >= int(o.PlantStateOffset) || len(e.orphans) > 0 {
		return nil
	}
	zeros := []map[string]any{}
	for _, p := range e.properties {
		if p.tag != objectiveTimerTag || !strings.HasPrefix(p.text, "0.00") {
			continue
		}
		if p.entity != complete.entity || p.offset < complete.start || p.offset >= complete.end || p.end > complete.end {
			return nil
		}
		zeros = append(zeros, map[string]any{"offset": p.offset, "text": p.text, "entity": p.entity})
	}
	if len(zeros) != legacy+1 {
		return nil
	}
	return map[string]any{"source": "repeated_plant_zero_before_transition_v1", "actor_uid": o.ActorID,
		"plant_offset": o.PlantStateOffset, "start": complete.start, "end": complete.end, "zero_samples": zeros,
		"legacy_disable_count": legacy, "winning_team": winning,
		"starting_scores": []int{h.Teams[0].StartingScore, h.Teams[1].StartingScore},
		"ending_scores":   []int{h.Teams[0].Score, h.Teams[1].Score}}
}
