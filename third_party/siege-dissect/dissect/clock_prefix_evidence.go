package dissect

// Additive structural controls: retain co-serialized countdown fields, never
// infer an event timestamp from a neighboring packet or assume recording rate.
import "encoding/hex"

const ClockPrefixEvidenceSource = "same_entity_countdown_property_prefix_v1"

type ClockPrefixGroup struct {
	Record     int                `json:"record"`
	Entity     uint32             `json:"entity"`
	Coarse     []ClockScalarField `json:"coarse"`
	Fine       []ClockScalarField `json:"fine"`
	PrefixEnd  int                `json:"prefix_end"`
	StopOffset int                `json:"stop_offset"`
	StopReason string             `json:"stop_reason"`
}
type ClockPrefixEvidence struct {
	Source                  string             `json:"source"`
	Groups                  []ClockPrefixGroup `json:"groups"`
	ProductionAuthoritative bool               `json:"production_authoritative"`
	ElapsedSeconds          *float64           `json:"elapsed_seconds"`
}

func InspectClockPrefixGroupsBuffer(b []byte) ClockPrefixEvidence {
	r := ClockPrefixEvidence{Source: ClockPrefixEvidenceSource, Groups: []ClockPrefixGroup{}}
	for _, prefix := range ownedRawPrefixes(b) {
		g := ClockPrefixGroup{Record: prefix.record, Entity: uint32(prefix.entity), Coarse: []ClockScalarField{}, Fine: []ClockScalarField{}, PrefixEnd: prefix.end, StopOffset: prefix.stop, StopReason: prefix.reason}
		for _, p := range prefix.fields {
			if p.tag != 0x6c463718 && p.tag != 0xc9ef071f {
				continue
			}
			x := ClockScalarField{prefix.record, p.offset, p.entity, hex.EncodeToString(b[p.offset : p.offset+4]), p.size, p.bits, hex.EncodeToString(b[p.offset+5 : p.end]), prefix.end, prefix.stop, prefix.reason}
			if p.tag == 0x6c463718 {
				g.Fine = append(g.Fine, x)
			} else {
				g.Coarse = append(g.Coarse, x)
			}
		}
		if len(g.Fine)+len(g.Coarse) > 0 {
			r.Groups = append(r.Groups, g)
		}
	}
	return r
}
