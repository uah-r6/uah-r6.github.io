package dissect

import (
	"encoding/json"
	"errors"
	"os"
	"reflect"
	"testing"
)

func TestNativeEnvelopeCurrentY11JinDeathFixture(t *testing.T) {
	data, err := os.ReadFile("../../../tests/fixtures/credited-kills-death-envelope-y11.json")
	if err != nil {
		t.Fatal(err)
	}
	var fixture struct {
		Evidence  CreditStructuralEvidence `json:"evidence"`
		Envelopes []NativeFeedbackEnvelope `json:"envelopes"`
	}
	if err = json.Unmarshal(data, &fixture); err != nil {
		t.Fatal(err)
	}
	e := fixture.Evidence
	if ValidateKillCreditEvidence(e).Complete {
		t.Fatal("original unknown Death refusal lost")
	}
	feedback := []MatchUpdate{}
	for _, finish := range e.Finishes {
		f := finish.Feedback
		f.killOffset = finish.Offset
		feedback = append(feedback, f)
	}
	original, observed := creditFinishesFromNativeEnvelopes(feedback, fixture.Envelopes)
	if original[4].Offset != 0 || original[4].Feedback.Username != "Jin.RRX" || observed[4].Offset != 41873708 {
		t.Fatalf("wrong native death provenance: %+v %+v", original[4], observed[4])
	}
	e.Finishes = observed
	r := ValidateKillCreditEvidence(e)
	if !r.Complete {
		t.Fatalf("exact native Death evidence refused: %+v", r)
	}
	for _, p := range r.Players {
		if p.Username == "Jin.RRX" && *p.Kills != 2 {
			t.Fatal("wrong Jin credited kills")
		}
	}
	if len(r.Finishes) != 6 {
		t.Fatal("death/finish lost or extra DBNO death created")
	}
}

func TestNativeEnvelopeSingleDecodePreservesFeedback(t *testing.T) {
	r := &Reader{b: make([]byte, 200), offset: 105}
	copy(r.b[100:], nativeFeedbackMarker)
	calls := 0
	rows := []NativeFeedbackEnvelope{}
	wrapped := feedbackEnvelopeListener(func(r *Reader) error {
		calls++
		r.offset = 145
		r.MatchFeedback = append(r.MatchFeedback, MatchUpdate{Type: Death, Username: "victim", Time: "0:33", TimeInSeconds: 33})
		return nil
	}, &rows)
	if err := wrapped(r); err != nil {
		t.Fatal(err)
	}
	if calls != 1 || len(rows) != 1 || !rows[0].MarkerValid || rows[0].StartOffset != 100 || rows[0].EndOffset != 145 {
		t.Fatalf("wrong callback provenance: %d %+v", calls, rows)
	}
	before := append([]MatchUpdate{}, r.MatchFeedback...)
	original, corrected := creditFinishesFromNativeEnvelopes(r.MatchFeedback, rows)
	if original[0].Offset != 0 || corrected[0].Offset != 100 || !reflect.DeepEqual(before, r.MatchFeedback) {
		t.Fatalf("raw event changed: %+v %+v", original, corrected)
	}
	if !reflect.DeepEqual(original[0].Feedback, corrected[0].Feedback) {
		t.Fatal("native envelope changed raw victim/event")
	}
}

func TestNativeEnvelopeObserverRejectsUnavailableOrDuplicateCallback(t *testing.T) {
	callback := func(*Reader) error { return nil }
	for _, r := range []*Reader{
		{},
		{queries: [][]byte{nativeFeedbackMarker}, listeners: [][]func(*Reader) error{{callback, callback}}},
		{queries: [][]byte{nativeFeedbackMarker, nativeFeedbackMarker}, listeners: [][]func(*Reader) error{{callback}, {callback}}},
	} {
		rows := []NativeFeedbackEnvelope{}
		if installFeedbackEnvelopeObserver(r, &rows) == nil {
			t.Fatal("ambiguous registration accepted")
		}
	}
	r := &Reader{queries: [][]byte{nativeFeedbackMarker}, listeners: [][]func(*Reader) error{{callback}}}
	rows := []NativeFeedbackEnvelope{}
	if err := installFeedbackEnvelopeObserver(r, &rows); err != nil {
		t.Fatal(err)
	}
	if len(r.queries) != 1 || len(r.listeners[0]) != 1 {
		t.Fatal("duplicate listener/query added")
	}
}

func TestNativeEnvelopeAmbiguousOrFailedEmission(t *testing.T) {
	for _, n := range []int{0, 2} {
		r := &Reader{b: make([]byte, 200), offset: 105}
		copy(r.b[100:], nativeFeedbackMarker)
		rows := []NativeFeedbackEnvelope{}
		callback := feedbackEnvelopeListener(func(r *Reader) error {
			r.offset = 145
			for i := 0; i < n; i++ {
				r.MatchFeedback = append(r.MatchFeedback, MatchUpdate{Type: Death, Username: "victim"})
			}
			return nil
		}, &rows)
		if err := callback(r); err != nil {
			t.Fatal(err)
		}
		for _, e := range rows {
			if e.MarkerValid {
				t.Fatal("multi-event emission accepted")
			}
		}
		_, corrected := creditFinishesFromNativeEnvelopes(r.MatchFeedback, rows)
		for _, e := range corrected {
			if e.Offset != 0 {
				t.Fatal("ambiguous event offset repaired")
			}
		}
	}
	r := &Reader{b: make([]byte, 200), offset: 105}
	copy(r.b[100:], nativeFeedbackMarker)
	rows := []NativeFeedbackEnvelope{}
	want := errors.New("decode error")
	err := feedbackEnvelopeListener(func(r *Reader) error {
		r.MatchFeedback = append(r.MatchFeedback, MatchUpdate{Type: Death, Username: "victim"})
		return want
	}, &rows)(r)
	if err != want || len(rows) != 0 {
		t.Fatal("failed decode emitted provenance")
	}
}

func TestNativeEnvelopeRefusesBadProofAndUnknownKill(t *testing.T) {
	f := MatchUpdate{Type: Death, Username: "f", Time: "2:00", TimeInSeconds: 120}
	proof := NativeFeedbackEnvelope{FeedbackIndex: 0, StartOffset: 1200, EndOffset: 1290, MarkerValid: true, Feedback: f}
	tests := map[string]func(*NativeFeedbackEnvelope){
		"marker":   func(e *NativeFeedbackEnvelope) { e.MarkerValid = false },
		"zero":     func(e *NativeFeedbackEnvelope) { e.StartOffset = 0 },
		"end":      func(e *NativeFeedbackEnvelope) { e.EndOffset = e.StartOffset },
		"identity": func(e *NativeFeedbackEnvelope) { e.Feedback.Username = "other" },
		"clock":    func(e *NativeFeedbackEnvelope) { e.Feedback.TimeInSeconds = 119 },
		"index":    func(e *NativeFeedbackEnvelope) { e.FeedbackIndex = 1 },
		"legacy":   func(e *NativeFeedbackEnvelope) { e.LegacyOffset = 1 },
		"kind":     func(e *NativeFeedbackEnvelope) { e.Feedback.Type = Kill },
	}
	for name, modify := range tests {
		t.Run(name, func(t *testing.T) {
			e := proof
			modify(&e)
			_, actual := creditFinishesFromNativeEnvelopes([]MatchUpdate{f}, []NativeFeedbackEnvelope{e})
			if actual[0].Offset != 0 {
				t.Fatal("bad proof accepted")
			}
		})
	}
	_, duplicate := creditFinishesFromNativeEnvelopes([]MatchUpdate{f}, []NativeFeedbackEnvelope{proof, proof})
	if duplicate[0].Offset != 0 {
		t.Fatal("duplicate proof accepted")
	}
	f.Type = Kill
	proof.Feedback = f
	_, kill := creditFinishesFromNativeEnvelopes([]MatchUpdate{f}, []NativeFeedbackEnvelope{proof})
	if kill[0].Offset != 0 {
		t.Fatal("unknown Kill offset repaired")
	}
}

func TestNativeEnvelopeKeepsDeathBaselineGuard(t *testing.T) {
	h, data, _ := creditFixture()
	f := MatchUpdate{Type: Death, Username: "f", Time: "2:00", TimeInSeconds: 120}
	proof := NativeFeedbackEnvelope{FeedbackIndex: 0, StartOffset: 1200, EndOffset: 1290, MarkerValid: true, Feedback: f}
	original, validated := creditFinishesFromNativeEnvelopes([]MatchUpdate{f}, []NativeFeedbackEnvelope{proof})
	if deriveKillCredit(h, data, original).Complete {
		t.Fatal("original unknown Death accepted")
	}
	if !deriveKillCredit(h, data, validated).Complete {
		t.Fatal("exact native Death evidence refused")
	}
	proof.StartOffset = 800 // Some player baselines now come AFTER the death.
	_, late := creditFinishesFromNativeEnvelopes([]MatchUpdate{f}, []NativeFeedbackEnvelope{proof})
	if deriveKillCredit(h, data, late).Complete {
		t.Fatal("late baseline guard weakened")
	}
}
