package dissect

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"reflect"
	"testing"
)

type whiteDeathFixture struct {
	Provenance map[string]any           `json:"provenance"`
	Evidence   CreditStructuralEvidence `json:"evidence"`
	Envelopes  []NativeFeedbackEnvelope `json:"envelopes"`
}

func TestCreditWhiteY11FirstDeathBaseline(t *testing.T) {
	data, err := os.ReadFile("../../../tests/fixtures/credited-kills-white-first-death-y11.json")
	if err != nil {
		t.Fatal(err)
	}
	var fixture whiteDeathFixture
	if err = json.Unmarshal(data, &fixture); err != nil {
		t.Fatal(err)
	}
	e := fixture.Evidence
	legacy := ValidateKillCreditEvidence(e)
	if legacy.Complete || len(legacy.Players) != 10 {
		t.Fatal("zero-offset first death must still refuse every player baseline")
	}
	for _, p := range legacy.Players {
		if p.Reason != "baseline_not_before_first_elimination" {
			t.Fatalf("wrong original refusal: %+v", p)
		}
	}
	feedback := []MatchUpdate{}
	for _, finish := range e.Finishes {
		f := finish.Feedback
		f.killOffset = finish.Offset
		feedback = append(feedback, f)
	}
	original, observed := creditFinishesFromNativeEnvelopes(feedback, fixture.Envelopes)
	if original[0].Offset != 0 || observed[0].Offset != 72793401 || observed[0].OffsetEvidence == nil ||
		observed[0].Feedback.Type != Death || observed[0].Feedback.Username != "Player5" ||
		observed[0].Feedback.TimeInSeconds != 172 {
		t.Fatalf("first death did not retain exact callback/identity/clock proof: %+v", observed[0])
	}
	if !reflect.DeepEqual(original[1:], observed[1:]) {
		t.Fatal("unrelated kill offsets or feedback changed")
	}
	e.Finishes = observed
	recovered := ValidateKillCreditEvidence(e)
	want := []uint32{0, 0, 2, 3, 0, 0, 0, 0, 1, 1}
	if !recovered.Complete || recovered.ActionStartOffset != 72761607 {
		t.Fatalf("real structured round refused: %+v", recovered)
	}
	for i, p := range recovered.Players {
		if p.Kills == nil || *p.Kills != want[i] {
			t.Fatalf("wrong observed player delta: %+v", p)
		}
	}
	// Recovery supplies a real boundary; it never removes baseline checks.
	e.Finishes[0].Offset = 1
	if ValidateKillCreditEvidence(e).Complete {
		t.Fatal("a genuinely late baseline was accepted")
	}
}

// Optional real-file smoke/capture. No replay bytes, profile IDs or usernames
// enter the committed fixture. Run with a local archived first-Death round.
func TestCreditWhiteDeathRealReplay(t *testing.T) {
	path := os.Getenv("R6_TEST_CREDIT_DEATH_ROUND")
	if path == "" {
		t.Skip("optional real standalone-death replay")
	}
	in, err := os.Open(path)
	if err != nil {
		t.Fatal(err)
	}
	defer in.Close()
	_, credit, err := ReadKillCredit(in)
	if err != nil || !credit.Complete || credit.Source != CreditedKillSource || len(credit.Finishes) == 0 ||
		credit.Finishes[0].Feedback.Type != Death || credit.Finishes[0].OffsetEvidence == nil {
		t.Fatalf("production reader did not recover exact first Death: %v %+v", err, credit)
	}
	out := os.Getenv("R6_TEST_CREDIT_FIXTURE_OUT")
	if out == "" {
		return
	}
	if _, err = in.Seek(0, 0); err != nil {
		t.Fatal(err)
	}
	r, err := NewReader(in)
	if err != nil {
		t.Fatal(err)
	}
	data := r.b // Reader.Read releases its buffer after callbacks finish.
	envelopes := []NativeFeedbackEnvelope{}
	if err = installFeedbackEnvelopeObserver(r, &envelopes); err != nil {
		t.Fatal(err)
	}
	if err = r.Read(); !Ok(err) {
		t.Fatal(err)
	}
	names, uids := map[string]string{}, map[uint64]uint64{}
	h := Header{CodeVersion: r.Header.CodeVersion, RoundNumber: r.Header.RoundNumber,
		ActionPhaseStartOffset: r.Header.ActionPhaseStartOffset, Teams: r.Header.Teams}
	for i, p := range r.Header.Players {
		name, uid := fmt.Sprintf("Player%d", i+1), uint64(i+1)
		names[p.Username], uids[p.ID] = name, uid
		h.Players = append(h.Players, Player{ID: uid, Username: name, TeamIndex: p.TeamIndex})
	}
	for i := range h.Teams {
		h.Teams[i].Name = ""
	}
	anonymize := func(f MatchUpdate) MatchUpdate {
		f.Username, f.Target = names[f.Username], names[f.Target]
		return f
	}
	original, _ := creditFinishesFromNativeEnvelopes(r.MatchFeedback, nil)
	for i := range original {
		original[i].Feedback = anonymize(original[i].Feedback)
	}
	for i := range envelopes {
		envelopes[i].Feedback = anonymize(envelopes[i].Feedback)
	}
	components, owners := map[uint32]bool{}, map[uint32]bool{}
	for _, p := range credit.Players {
		for _, s := range p.Samples {
			components[s.Component], owners[s.Owner] = true, true
		}
	}
	e := CreditStructuralEvidence{Header: h, Finishes: original}
	declarations, uidFields := objectiveComponentFields(data)
	for _, d := range declarations {
		if components[d.component] {
			e.Declarations = append(e.Declarations, CreditDeclaration{d.offset, d.owner, d.slot, d.component, d.class})
		}
	}
	for _, f := range uidFields {
		if owners[f.entity] {
			uid, ok := uids[f.bits]
			if !ok {
				t.Fatal("cannot ordinalize an unexpected scoreboard UID")
			}
			e.Properties = append(e.Properties, CreditProperty{f.offset, f.entity, f.tag, f.size, uid})
		}
	}
	for _, f := range creditCounterFields(data) {
		if components[f.entity] {
			e.Properties = append(e.Properties, CreditProperty{f.offset, f.entity, f.tag, f.size, f.bits})
		}
	}
	fixture := whiteDeathFixture{map[string]any{
		"round": 8, "note": "Selected typed observations only; UIDs ordinalized and names anonymized; exact offsets/counters retained; no replay bytes.",
	}, e, envelopes}
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	fixture.Provenance["replay_sha256"] = fmt.Sprintf("%x", sha256.Sum256(raw))
	encoded, err := json.MarshalIndent(fixture, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(out, append(encoded, '\n'), 0600); err != nil {
		t.Fatal(err)
	}
}
