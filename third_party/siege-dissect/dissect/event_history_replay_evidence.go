package dissect

import "io"

// ReadEventHistoryEvidence explicitly retains a local decompressed-buffer
// reference while normal reading resolves the final header. Default Read still
// releases its own buffer. No callback, event, operator or stats path changes.
func ReadEventHistoryEvidence(in io.Reader) (Header, EventHistoryEvidence, error) {
	r, err := NewReader(in)
	if err != nil {
		return Header{}, EventHistoryEvidence{Source: EventHistoryEvidenceSource, Reason: "reader_initialization_failed"}, err
	}
	buffer := r.b
	if err = r.Read(); err != nil {
		return r.Header, EventHistoryEvidence{Source: EventHistoryEvidenceSource, Reason: "normal_reader_failed"}, err
	}
	return r.Header, InspectEventHistoryBuffer(buffer, r.Header), nil
}
