package dissect

import "testing"

func TestFalseDisableRequiresRepeatedZerosOfSamePlantBeforeTransition(t *testing.T) {
	e, h, o := terminalSnapshotFixture()
	e.splitEpisodes(h.CodeVersion)
	h.Teams[0].Won = true
	h.Teams[0].StartingScore = 2
	h.Teams[0].Score = 3
	h.Teams[1].StartingScore = 3
	h.Teams[1].Score = 3
	name := h.Players[0].Username
	o.Actor = &name
	o.ActorID = h.Players[0].ID
	h.ObjectiveOccurrences = []ObjectiveOccurrence{o}
	e.properties = append(e.properties, objectiveProperty{offset: 119, end: 120, entity: 200, tag: objectiveTimerTag, text: "0.008"}, objectiveProperty{offset: 121, end: 124, entity: 200, tag: objectiveTimerTag, text: "0.004"})
	feed := []MatchUpdate{{Type: DefuserDisableComplete}}
	if e.noDisableProof(h, feed, o) == nil {
		t.Fatal("repeated plant-zero proof missing")
	}
	for _, mutation := range []string{"wrong_winner", "score_conflict", "second_plant", "after_plant", "different_timer", "orphan", "phase1"} {
		t.Run(mutation, func(t *testing.T) {
			copy := e
			copy.properties = append([]objectiveProperty(nil), e.properties...)
			copy.episodes = append([]objectiveEpisode(nil), e.episodes...)
			header := h
			switch mutation {
			case "wrong_winner":
				header.Teams[0].Role = Defense
			case "score_conflict":
				header.Teams[1].Score++
			case "second_plant":
				header.ObjectiveOccurrences = append(header.ObjectiveOccurrences, o)
			case "after_plant":
				copy.properties[len(copy.properties)-1].offset = 160
			case "different_timer":
				copy.properties[len(copy.properties)-1].entity = 999
			case "orphan":
				copy.orphans = []int{105}
			case "phase1":
				copy.episodes[0].phase = 1
			}
			if copy.noDisableProof(header, feed, o) != nil {
				t.Fatalf("unsafe %s removal proof accepted", mutation)
			}
		})
	}
}
