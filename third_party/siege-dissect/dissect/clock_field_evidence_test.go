package dissect

import "testing"

func TestRecordingHeaderFieldsKeepDuplicatesAndRefuseTruncation(t *testing.T) {
	b := append([]byte("dissect"), make([]byte, 14)...)
	str := func(value string) {
		b = append(b, byte(len(value)), 0, 0, 0, 0, 0, 0, 0)
		b = append(b, []byte(value)...)
	}
	for _, v := range []string{"code", "123", "gmsetting", "45", "gmsetting", "7", "teamscore1", "0"} {
		str(v)
	}
	r := InspectRecordingHeaderFields(b)
	if r.Reason != "exact_plain_header_through_teamscore1" || len(r.Fields) != 4 || r.Fields[1].Key != r.Fields[2].Key {
		t.Fatalf("header fields lost: %+v", r)
	}
	r = InspectRecordingHeaderFields(b[:len(b)-1])
	if r.Reason != "invalid_or_truncated_header_value" {
		t.Fatal("truncated header accepted")
	}
	r = InspectRecordingHeaderFields([]byte{0x28, 0xb5, 0x2f, 0xfd})
	if r.Reason != "plain_chunked_header_required" {
		t.Fatal("compressed header guessed")
	}
}

func TestClockFieldInventoryPreservesZeroAndUnsignedValues(t *testing.T) {
	b := ownedTestProperty(321, 0x6c463718, 4, 0)
	b = append(b, ownedTestProperty(321, 0xa374f4b6, 4, 0xffffffff)...)
	b = append(b, 0x1f, 0x07, 0xef, 0xc9, 4, 0, 0, 0, 0)
	r := InspectClockFieldPrefixesBuffer(b)
	if len(r.Fields) != 2 || r.Fields[0].UnsignedBits != 0 || r.Fields[1].UnsignedBits != 0xffffffff {
		t.Fatal("raw zero/unsigned field lost")
	}
	if len(r.Countdown) != 1 || r.Countdown[0].Value == nil || *r.Countdown[0].Value != 0 || r.Countdown[0].Width != 4 {
		t.Fatal("zero countdown lost")
	}
	if r.ProductionAuthoritative || r.ElapsedSeconds != nil {
		t.Fatal("clock units were promoted")
	}
}
func TestClockFieldInventoryDoesNotSkipUnknownMiddleField(t *testing.T) {
	b := ownedTestProperty(321, 123, 4, 1)
	b = append(b, 0x22, 1, 2, 3, 4, 3, 1, 2, 3, 0x22, 0x18, 0x37, 0x46, 0x6c, 4, 0, 0, 0, 0)
	r := InspectClockFieldPrefixesBuffer(b)
	if len(r.Fields) != 0 {
		t.Fatal("clock field behind unsupported width was inferred")
	}
}
func TestClockFieldInventoryKeepsWrongWidthAndTruncatedMarkers(t *testing.T) {
	b := []byte{0x1f, 0x07, 0xef, 0xc9, 8, 1, 0, 0, 0, 0xff, 0x1f, 0x07, 0xef, 0xc9, 4, 1}
	r := InspectClockFieldPrefixesBuffer(b)
	if len(r.Countdown) != 2 || r.Countdown[0].Reason != "unsupported_width_not_accepted_as_countdown" || r.Countdown[1].Value != nil {
		t.Fatalf("unsupported/truncated marker accepted: %+v", r)
	}
}
