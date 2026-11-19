package dissect

import (
	"os"
	"testing"
)

func TestInRoundUIDReplacementRequiresTwoDirectZeroCounters(t *testing.T) {
	const oldUID, newUID uint64 = 123, 456
	const owner uint32 = 77
	decls := []objectiveDeclaration{
		{offset: 10, owner: owner, slot: creditScoreSlot, component: 100, class: creditScoreClass},
		{offset: 120, owner: owner, slot: creditScoreSlot, component: 200, class: creditScoreClass},
	}
	uids := []objectiveProperty{
		{offset: 30, entity: owner, tag: objectiveUIDTag, size: 8, bits: oldUID},
		{offset: 140, entity: owner, tag: objectiveUIDTag, size: 8, bits: newUID},
	}
	counters := []objectiveProperty{
		{offset: 20, entity: 100, tag: creditKillTag, size: 4, bits: 0},
		{offset: 130, entity: 200, tag: creditKillTag, size: 4, bits: 0},
	}
	proof := inRoundUIDCounterGap(PlayerKillCredit{UID: oldUID}, 100, decls, uids, counters)
	if proof == nil || proof.OldSampleOffset != 20 || proof.NewSampleOffset != 130 || proof.NewUID != newUID {
		t.Fatalf("exact native zero bridge missing: %+v", proof)
	}
	for _, variant := range []struct {
		name     string
		decls    []objectiveDeclaration
		uids     []objectiveProperty
		counters []objectiveProperty
	}{
		{"positive counter", decls, uids, []objectiveProperty{counters[0], {offset: 130, entity: 200, tag: creditKillTag, size: 4, bits: 1}}},
		{"missing new counter", decls, uids, counters[:1]},
		{"third UID", decls, append(append([]objectiveProperty{}, uids...), objectiveProperty{offset: 150, entity: owner, tag: objectiveUIDTag, size: 8, bits: 789}), counters},
		{"different owner", decls, []objectiveProperty{uids[0], {offset: 140, entity: 88, tag: objectiveUIDTag, size: 8, bits: newUID}}, counters},
	} {
		t.Run(variant.name, func(t *testing.T) {
			if inRoundUIDCounterGap(PlayerKillCredit{UID: oldUID}, 100, variant.decls, variant.uids, variant.counters) != nil {
				t.Fatal("unsupported bridge was accepted")
			}
		})
	}
}

func TestMIZChaletNativeEvidenceRealReplay(t *testing.T) {
	first := os.Getenv("R6_TEST_MIZ_CHALET_R01")
	second := os.Getenv("R6_TEST_MIZ_CHALET_R02")
	if first == "" || second == "" {
		t.Skip("optional private R01/R02 replay files")
	}
	f, err := os.Open(first)
	if err != nil {
		t.Fatal(err)
	}
	_, credit, err := ReadKillCredit(f)
	f.Close()
	if err != nil {
		t.Fatal(err)
	}
	var gap *CreditCounterGap
	for _, p := range credit.Players {
		if p.Username == "rec-_-" {
			gap = p.CounterGap
		}
	}
	if gap == nil || gap.Source != "in_round_uid_replacement_zero_counters_v1" || credit.Complete {
		t.Fatalf("R01 direct zero proof missing or round falsely completed: %+v", gap)
	}
	f, err = os.Open(second)
	if err != nil {
		t.Fatal(err)
	}
	r, err := NewReader(f)
	if err != nil {
		t.Fatal(err)
	}
	if err = r.Read(); !Ok(err) {
		t.Fatal(err)
	}
	f.Close()
	if len(r.Header.ObjectiveOccurrences) != 1 || r.Header.ObjectiveOccurrences[0].Actor == nil || *r.Header.ObjectiveOccurrences[0].Actor != "rec-_-" {
		t.Fatalf("R02 native Death boundary did not resolve exact plant owner: %+v", r.Header.ObjectiveOccurrences)
	}
	for _, update := range r.MatchFeedback {
		if update.Type == Death && update.Username == "Leo.MIZ" && update.killOffset != 0 {
			t.Fatal("historical feedback offset was not restored")
		}
	}
}
