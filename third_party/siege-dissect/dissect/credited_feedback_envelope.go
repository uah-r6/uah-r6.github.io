package dissect

// Opt-in development reader. Native callback ownership recovers a Death
// envelope boundary without rewriting frozen MatchFeedback or guessing from
// neighboring packets. The original ReadKillCredit stays unchanged.
import (
	"bytes"
	"fmt"
	"io"
)

const NativeCreditedKillSource = "stable_uid_scoreboard_delta_native_feedback_envelope_v1"

var nativeFeedbackMarker = []byte{0x59, 0x34, 0xe5, 0x8b, 0x04}

type NativeFeedbackEnvelope struct {
	FeedbackIndex int         `json:"feedbackIndex"`
	StartOffset   int         `json:"startOffset"`
	EndOffset     int         `json:"endOffset"`
	LegacyOffset  int         `json:"legacyOffset"`
	MarkerValid   bool        `json:"markerValid"`
	Feedback      MatchUpdate `json:"feedback"`
}

// The same callback must emit exactly one event for an unknown Death offset
// to be recoverable. Multi-event callbacks are retained but not repaired.
func feedbackEnvelopeListener(original func(*Reader) error, out *[]NativeFeedbackEnvelope) func(*Reader) error {
	return func(r *Reader) error {
		start := r.offset - len(nativeFeedbackMarker)
		before := len(r.MatchFeedback)
		valid := start > 0 && r.offset <= len(r.b) && bytes.Equal(r.b[start:r.offset], nativeFeedbackMarker)
		if err := original(r); err != nil {
			return err
		}
		for index := before; index < len(r.MatchFeedback); index++ {
			f := r.MatchFeedback[index]
			if f.Type == Kill || f.Type == Death {
				*out = append(*out, NativeFeedbackEnvelope{index, start, r.offset, f.killOffset,
					valid && r.offset > start && r.offset <= len(r.b) && len(r.MatchFeedback)-before == 1, f})
			}
		}
		return nil
	}
}

func installFeedbackEnvelopeObserver(r *Reader, out *[]NativeFeedbackEnvelope) error {
	index := -1
	for i, query := range r.queries {
		if bytes.Equal(query, nativeFeedbackMarker) {
			if index >= 0 || len(r.listeners[i]) != 1 {
				return fmt.Errorf("native feedback observer requires exactly one existing callback")
			}
			index = i
		}
	}
	if index < 0 {
		return fmt.Errorf("native feedback callback unavailable")
	}
	// Do not use Listen to add a duplicate pattern/callback or decode twice.
	r.listeners[index][0] = feedbackEnvelopeListener(r.listeners[index][0], out)
	return nil
}

func creditFinishesFromNativeEnvelopes(feedback []MatchUpdate, envelopes []NativeFeedbackEnvelope) ([]CreditFinish, []CreditFinish) {
	original, validated := []CreditFinish{}, []CreditFinish{}
	for index, f := range feedback {
		if f.Type != Kill && f.Type != Death {
			continue
		}
		legacy := CreditFinish{Offset: f.killOffset, Feedback: f}
		original = append(original, legacy)
		observed := legacy
		if f.Type == Death && f.killOffset <= 0 {
			found := []NativeFeedbackEnvelope{}
			for _, envelope := range envelopes {
				if envelope.FeedbackIndex == index {
					found = append(found, envelope)
				}
			}
			if len(found) == 1 {
				e := found[0]
				if e.MarkerValid && e.StartOffset > 0 && e.EndOffset > e.StartOffset &&
					e.LegacyOffset == f.killOffset && e.Feedback.Type == Death &&
					e.Feedback.Username == f.Username && e.Feedback.Target == f.Target && e.Feedback.Time == f.Time &&
					e.Feedback.TimeInSeconds == f.TimeInSeconds {
					observed.Offset = e.StartOffset
				}
			}
		}
		validated = append(validated, observed)
	}
	return original, validated
}

func ReadKillCreditNativeEnvelopes(in io.Reader) (Header, RoundKillCredit, []CreditFinish, []NativeFeedbackEnvelope, error) {
	r, err := NewReader(in)
	if err != nil {
		return Header{}, RoundKillCredit{}, nil, nil, err
	}
	data := r.b
	envelopes := []NativeFeedbackEnvelope{}
	if err = installFeedbackEnvelopeObserver(r, &envelopes); err != nil {
		return r.Header, RoundKillCredit{}, nil, nil, err
	}
	if err = r.Read(); !Ok(err) {
		return r.Header, RoundKillCredit{}, nil, envelopes, err
	}
	original, observed := creditFinishesFromNativeEnvelopes(r.MatchFeedback, envelopes)
	credit := deriveKillCredit(r.Header, data, observed)
	credit.Source = NativeCreditedKillSource
	if credit.Complete {
		credit.Reason = NativeCreditedKillSource
	}
	return r.Header, credit, original, envelopes, nil
}
