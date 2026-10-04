package dissect

// Research-only cumulative event-list evidence. This does not replace
// MatchFeedback, assign credited killers, or interpret scalar units.
import (
	"bytes"
	"encoding/binary"
	"encoding/hex"
	"fmt"
)

const EventHistoryEvidenceSource = "bounded_cumulative_event_history_evidence_v1"

type HistoryIdentity struct {
	UID       uint64 `json:"uid"`
	ProfileID string `json:"profile_id"`
	Username  string `json:"username"`
	Team      int    `json:"team"`
	RoleImage uint64 `json:"role_image"`
	Alliance  uint32 `json:"alliance"`
}

type HistoryItem struct {
	Ordinal         int              `json:"ordinal"`
	Start           int              `json:"start"`
	End             int              `json:"end"`
	Kind            uint8            `json:"kind_byte"`
	Scalar          uint32           `json:"opaque_scalar"`
	Weapon          uint64           `json:"weapon_id,omitempty"`
	EntityReference uint64           `json:"entity_reference,omitempty"`
	First           *HistoryIdentity `json:"first,omitempty"`
	Second          *HistoryIdentity `json:"second,omitempty"`
	Single          *HistoryIdentity `json:"reference,omitempty"`
	Headshot        *bool            `json:"headshot,omitempty"`
	OpaqueTail      *uint8           `json:"opaque_tail_u8,omitempty"`
	RawHex          string           `json:"raw_hex"`
	ElapsedSeconds  *float64         `json:"elapsed_seconds"`
}

type HistoryContainer struct {
	Start        int           `json:"start"`
	End          int           `json:"end"`
	ItemCount    int           `json:"item_count"`
	PayloadBytes int           `json:"payload_length"`
	Complete     bool          `json:"complete"`
	Reason       string        `json:"reason"`
	Items        []HistoryItem `json:"items"`
	UnknownHex   string        `json:"unknown_hex,omitempty"`
}

type EventHistoryEvidence struct {
	Source                  string             `json:"source"`
	Complete                bool               `json:"complete"`
	Reason                  string             `json:"reason"`
	Descriptor              string             `json:"descriptor,omitempty"`
	Containers              []HistoryContainer `json:"containers"`
	Items                   []HistoryItem      `json:"items"`
	ScalarsNondecreasing    bool               `json:"scalars_nondecreasing"`
	ScalarTies              map[string]int     `json:"scalar_ties"`
	ProductionAuthoritative bool               `json:"production_authoritative"`
}

func historyIdentities(h Header) (map[uint64]HistoryIdentity, error) {
	if len(h.Players) != 10 {
		return nil, fmt.Errorf("history evidence requires ten distinct header players")
	}
	ids := make(map[uint64]HistoryIdentity)
	names := make(map[string]bool)
	teams := [2]int{}
	for _, p := range h.Players {
		if p.ID == 0 || p.Username == "" || names[p.Username] || p.TeamIndex < 0 || p.TeamIndex > 1 || p.RoleImage <= 0 || p.Alliance <= 0 || uint64(p.Alliance) > uint64(^uint32(0)) {
			return nil, fmt.Errorf("history header identity is unresolved")
		}
		if _, exists := ids[p.ID]; exists {
			return nil, fmt.Errorf("history header UID is duplicated")
		}
		ids[p.ID] = HistoryIdentity{p.ID, p.ProfileID, p.Username, p.TeamIndex, uint64(p.RoleImage), uint32(p.Alliance)}
		names[p.Username] = true
		teams[p.TeamIndex]++
	}
	if teams != [2]int{5, 5} {
		return nil, fmt.Errorf("history header team inventory is unresolved")
	}
	return ids, nil
}

func historyReference(b []byte, at, end int, ids map[uint64]HistoryIdentity) *HistoryIdentity {
	if at < 0 || at+20 > end || end > len(b) {
		return nil
	}
	p, ok := ids[binary.LittleEndian.Uint64(b[at:at+8])]
	if !ok || binary.LittleEndian.Uint64(b[at+8:at+16]) != p.RoleImage || binary.LittleEndian.Uint32(b[at+16:at+20]) != p.Alliance {
		return nil
	}
	return &p
}

func historyItemAt(b []byte, at, end int, ids map[uint64]HistoryIdentity) (HistoryItem, bool) {
	x := HistoryItem{}
	if at < 0 || at >= end || end > len(b) {
		return x, false
	}
	kind, width := b[at], 0
	switch kind {
	case 1, 2:
		width = 62
	case 3:
		width = 41
	case 5, 7:
		width = 53
	case 10:
		width = 26
	default:
		return x, false
	}
	if at+width > end {
		return x, false
	}
	x = HistoryItem{Start: at, End: at + width, Kind: kind, Scalar: binary.LittleEndian.Uint32(b[at+1 : at+5]), RawHex: hex.EncodeToString(b[at : at+width])}
	if x.Scalar == 0 {
		return x, false
	}
	refAt := at + 5
	if kind == 1 || kind == 2 || kind == 3 {
		x.Weapon = binary.LittleEndian.Uint64(b[at+5 : at+13])
		x.EntityReference = binary.LittleEndian.Uint64(b[at+13 : at+21])
		refAt = at + 21
	} else if kind == 5 || kind == 7 {
		x.EntityReference = binary.LittleEndian.Uint64(b[at+5 : at+13])
		refAt = at + 13
	}
	if kind != 10 && x.EntityReference == 0 {
		return x, false
	}
	first := historyReference(b, refAt, x.End, ids)
	if first == nil {
		return x, false
	}
	if kind == 1 || kind == 2 || kind == 5 || kind == 7 {
		x.First, x.Second = first, historyReference(b, refAt+20, x.End, ids)
		if x.Second == nil {
			return x, false
		}
	} else {
		x.Single = first
	}
	if kind == 1 || kind == 2 {
		if b[at+61] > 1 {
			return x, false
		}
		v := b[at+61] == 1
		x.Headshot = &v
	} else if kind == 10 {
		if b[at+25] != 1 && b[at+25] != 2 {
			return x, false
		}
		v := b[at+25]
		x.OpaqueTail = &v
	}
	return x, true
}

func historyBoxAt(b []byte, descriptorAt int, descriptor []byte) (HistoryContainer, bool) {
	x := HistoryContainer{Start: descriptorAt - 16, Items: []HistoryItem{}}
	if x.Start < 0 || descriptorAt+9 > len(b) || !bytes.Equal(b[descriptorAt:descriptorAt+9], descriptor) {
		return x, false
	}
	length := binary.LittleEndian.Uint64(b[x.Start+4 : x.Start+12])
	count := binary.LittleEndian.Uint32(b[x.Start+12 : x.Start+16])
	if length < 13 || length > 65536 || count < 1 || count > 64 {
		return x, false
	}
	x.End, x.PayloadBytes, x.ItemCount = x.Start+12+int(length), int(length), int(count)
	return x, x.End <= len(b) && x.End >= descriptorAt+9
}

func decodeHistoryBox(b []byte, box HistoryContainer, ids map[uint64]HistoryIdentity) HistoryContainer {
	at := box.Start + 25
	for ordinal := 0; ordinal < box.ItemCount-1; ordinal++ {
		item, ok := historyItemAt(b, at, box.End, ids)
		if !ok {
			box.Reason = "unknown_or_invalid_item_not_skipped"
			box.UnknownHex = hex.EncodeToString(b[at:box.End])
			return box
		}
		item.Ordinal = ordinal
		box.Items = append(box.Items, item)
		at = item.End
	}
	box.Complete = at == box.End
	box.Reason = "exact_count_and_bytes"
	if !box.Complete {
		box.Reason = "trailing_bytes_not_skipped"
		box.UnknownHex = hex.EncodeToString(b[at:box.End])
	}
	return box
}

// InspectEventHistoryBuffer examines the already decompressed reader buffer.
// Completeness is structural, not an authoritative credited-victim join.
// It requires a two-reference event anchor; kill-free unsupported layouts
// refuse rather than invent a descriptor or infer from scoreboard totals.
func InspectEventHistoryBuffer(b []byte, h Header) EventHistoryEvidence {
	result := EventHistoryEvidence{Source: EventHistoryEvidenceSource, Containers: []HistoryContainer{}, Items: []HistoryItem{}, ScalarTies: map[string]int{}}
	ids, err := historyIdentities(h)
	if err != nil {
		result.Reason = err.Error()
		return result
	}
	first := len(b)
	for uid := range ids {
		pattern := make([]byte, 8)
		binary.LittleEndian.PutUint64(pattern, uid)
		cursor := 0
		for cursor < len(b) {
			found := bytes.Index(b[cursor:], pattern)
			if found < 0 {
				break
			}
			at := cursor + found
			cursor = at + 1
			if historyReference(b, at, len(b), ids) == nil || historyReference(b, at+20, len(b), ids) == nil {
				continue
			}
			valid := []int{}
			for _, shift := range []int{21, 13} {
				item, ok := historyItemAt(b, at-shift, len(b), ids)
				if ok && item.First != nil && ((shift == 21 && (item.Kind == 1 || item.Kind == 2)) || (shift == 13 && (item.Kind == 5 || item.Kind == 7))) {
					valid = append(valid, item.Start)
				}
			}
			if len(valid) == 1 && valid[0] < first {
				first = valid[0]
			}
		}
	}
	if first == len(b) {
		result.Reason = "no_bounded_two_reference_anchor"
		return result
	}
	descriptors := map[string]bool{}
	start := first - 512
	if start < 0 {
		start = 0
	}
	for at := start; at < first && at+9 <= len(b); at++ {
		if b[at] != 9 || !bytes.Equal(b[at+5:at+9], []byte{3, 0, 0, 0}) {
			continue
		}
		d := b[at : at+9]
		box, ok := historyBoxAt(b, at, d)
		if ok && box.Start < first && first < box.End {
			descriptors[string(d)] = true
		}
	}
	if len(descriptors) != 1 {
		result.Reason = "unique_enclosing_descriptor_not_established"
		return result
	}
	var descriptor []byte
	for d := range descriptors {
		descriptor = []byte(d)
	}
	result.Descriptor = hex.EncodeToString(descriptor)
	for cursor := 0; cursor < len(b); {
		found := bytes.Index(b[cursor:], descriptor)
		if found < 0 {
			break
		}
		at := cursor + found
		cursor = at + 1
		box, ok := historyBoxAt(b, at, descriptor)
		if ok {
			result.Containers = append(result.Containers, decodeHistoryBox(b, box, ids))
		}
	}
	longest := -1
	for i, box := range result.Containers {
		if box.Complete && (longest < 0 || box.ItemCount > result.Containers[longest].ItemCount) {
			longest = i
		}
	}
	if longest < 0 {
		result.Reason = "no_complete_history_container"
		return result
	}
	result.Items = result.Containers[longest].Items
	for _, box := range result.Containers {
		if !box.Complete {
			result.Reason = "partial_container_retained"
			return result
		}
		for i, item := range box.Items {
			if i >= len(result.Items) || item.RawHex != result.Items[i].RawHex {
				result.Items = []HistoryItem{}
				result.Reason = "cumulative_items_changed_or_reordered"
				return result
			}
		}
	}
	result.Complete, result.ScalarsNondecreasing, result.Reason = true, true, "exact_cumulative_count_bounds_and_prefixes"
	scalars := map[uint32]int{}
	for i, item := range result.Items {
		scalars[item.Scalar]++
		if i > 0 && result.Items[i-1].Scalar > item.Scalar {
			result.ScalarsNondecreasing = false
		}
	}
	for scalar, count := range scalars {
		if count > 1 {
			result.ScalarTies[fmt.Sprint(scalar)] = count
		}
	}
	return result
}

// InspectEventHistory is opt-in and leaves Reader/default callbacks unchanged.
// Call after Read if final action-start header identities are required.
func (r *Reader) InspectEventHistory() EventHistoryEvidence {
	return InspectEventHistoryBuffer(r.b, r.Header)
}
