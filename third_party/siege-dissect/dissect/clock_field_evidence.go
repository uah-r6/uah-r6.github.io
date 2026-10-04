package dissect

// Research-only raw clock-field inventory. External names and units are
// hypotheses. No conversion to seconds, listener changes or phase inference.
import (
	"bytes"
	"encoding/binary"
	"encoding/hex"
)

const ClockFieldEvidenceSource = "bounded_clock_field_prefix_inventory_v1"

type ClockScalarField struct {
	Record       int    `json:"record"`
	Offset       int    `json:"offset"`
	Entity       uint32 `json:"entity"`
	TagHex       string `json:"tag_hex"`
	Width        int    `json:"width"`
	UnsignedBits uint64 `json:"unsigned_bits"`
	RawHex       string `json:"raw_hex"`
	PrefixEnd    int    `json:"prefix_end"`
	StopOffset   int    `json:"stop_offset"`
	StopReason   string `json:"stop_reason"`
}
type CountdownField struct {
	MarkerOffset int     `json:"marker_offset"`
	ValueOffset  int     `json:"value_offset"`
	Width        int     `json:"width"`
	Value        *uint32 `json:"value"`
	RawHex       string  `json:"raw_hex"`
	ContextStart int     `json:"context_start"`
	ContextHex   string  `json:"context_hex"`
	Reason       string  `json:"reason"`
}
type ClockFieldEvidence struct {
	Source                  string             `json:"source"`
	Fields                  []ClockScalarField `json:"fields"`
	Countdown               []CountdownField   `json:"countdown"`
	ProductionAuthoritative bool               `json:"production_authoritative"`
	ElapsedSeconds          *float64           `json:"elapsed_seconds"`
}

type RecordingHeaderField struct {
	Offset int    `json:"offset"`
	Key    string `json:"key"`
	Value  string `json:"value"`
}
type RecordingHeaderEvidence struct {
	Reason string                 `json:"reason"`
	Fields []RecordingHeaderField `json:"fields"`
	End    int                    `json:"end"`
}

// Chunked modern files have a plain framed header. This inspects that header
// only and never decompresses or invokes the default reader. Other layouts
// explicitly refuse. Keep every key/value in physical order, including repeats.
func InspectRecordingHeaderFields(b []byte) RecordingHeaderEvidence {
	r := RecordingHeaderEvidence{Fields: []RecordingHeaderField{}}
	if len(b) < 7 || string(b[:7]) != "dissect" {
		r.Reason = "plain_chunked_header_required"
		return r
	}
	at, n, groups := 7, 0, 0
	for at < len(b) && groups < 2 {
		if b[at] == 0 {
			n++
			if n == 7 {
				groups++
				n = 0
			}
		} else {
			n = 0
		}
		at++
	}
	if groups != 2 {
		r.Reason = "truncated_header_magic"
		return r
	}
	read := func() (string, bool) {
		if at+8 > len(b) {
			return "", false
		}
		if !bytes.Equal(b[at+1:at+8], make([]byte, 7)) {
			return "", false
		}
		size := int(b[at])
		at += 8
		if at+size > len(b) {
			return "", false
		}
		value := string(b[at : at+size])
		at += size
		return value, true
	}
	for len(r.Fields) < 1024 {
		start := at
		key, ok := read()
		if !ok {
			r.Reason = "invalid_or_truncated_header_key"
			return r
		}
		value, ok := read()
		if !ok {
			r.Reason = "invalid_or_truncated_header_value"
			return r
		}
		r.Fields = append(r.Fields, RecordingHeaderField{start, key, value})
		r.End = at
		if key == "teamscore1" {
			r.Reason = "exact_plain_header_through_teamscore1"
			return r
		}
	}
	r.Reason = "header_field_limit"
	return r
}

func InspectClockFieldPrefixesBuffer(b []byte) ClockFieldEvidence {
	r := ClockFieldEvidence{Source: ClockFieldEvidenceSource, Fields: []ClockScalarField{}, Countdown: []CountdownField{}}
	for _, prefix := range ownedRawPrefixes(b) {
		for _, p := range prefix.fields {
			if p.tag != 0x6c463718 && p.tag != 0xa374f4b6 {
				continue
			}
			r.Fields = append(r.Fields, ClockScalarField{prefix.record, p.offset, p.entity, hex.EncodeToString(b[p.offset : p.offset+4]), p.size, p.bits, hex.EncodeToString(b[p.offset+5 : p.end]), prefix.end, prefix.stop, prefix.reason})
		}
	}
	marker := []byte{0x1f, 0x07, 0xef, 0xc9}
	for cursor := 0; cursor < len(b); {
		rel := bytes.Index(b[cursor:], marker)
		if rel < 0 {
			break
		}
		at := cursor + rel
		cursor = at + 1
		x := CountdownField{MarkerOffset: at, ValueOffset: at + 5, Reason: "truncated_countdown_field"}
		if at+5 <= len(b) {
			x.Width = int(b[at+4])
		}
		if at+9 <= len(b) {
			v := binary.LittleEndian.Uint32(b[at+5 : at+9])
			x.Value = &v
			x.RawHex = hex.EncodeToString(b[at+4 : at+9])
			if x.Width == 4 {
				x.Reason = "exact_listener_marker_width4_raw_uint32"
			} else {
				x.Reason = "unsupported_width_not_accepted_as_countdown"
			}
		}
		start, end := at-32, at+41
		if start < 0 {
			start = 0
		}
		if end > len(b) {
			end = len(b)
		}
		x.ContextStart = start
		x.ContextHex = hex.EncodeToString(b[start:end])
		r.Countdown = append(r.Countdown, x)
	}
	return r
}
