package dissect

import (
	"bytes"
	"testing"
)

func TestHistoryInspectionExplainsReleasedReaderBuffer(t *testing.T) {
	r := &Reader{Header: historyTestHeader()}
	x := r.InspectEventHistory()
	if x.Complete || x.ProductionAuthoritative || x.Reason != "reader_buffer_released_use_ReadEventHistoryEvidence" {
		t.Fatalf("released buffer misclassified as missing replay data: %+v", x)
	}
}

func TestReadHistoryEvidenceMalformedReplayDoesNotEmitAuthority(t *testing.T) {
	_, x, err := ReadEventHistoryEvidence(bytes.NewReader([]byte("invalid replay")))
	if err == nil || x.Complete || x.ProductionAuthoritative || x.Reason != "reader_initialization_failed" {
		t.Fatalf("malformed replay became valid history: %+v %v", x, err)
	}
}
