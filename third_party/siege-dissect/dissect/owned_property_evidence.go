package dissect

// Opt-in research evidence. Numeric equality is NOT damage, instigator or kill
// attribution. Only explicit scalar/text prefixes and temporal owner routes are
// inspected; unsupported widths stop the prefix without skipping bytes.
import (
	"bytes"
	"encoding/binary"
	"encoding/hex"
	"fmt"
	"sort"
)

const OwnedPropertyEvidenceSource = "uid_owned_property_prefix_evidence_v1"

type OwnedPropertyQuery struct {
	Start       int    `json:"start"`
	End         int    `json:"end"`
	TargetUID   uint64 `json:"target_uid"`
	TargetStart int    `json:"target_start"`
	TargetEnd   int    `json:"target_end"`
}
type OwnedPropertyRoute struct {
	Owner       uint32          `json:"owner"`
	Slot        uint32          `json:"slot"`
	Class       uint32          `json:"class"`
	Declaration int             `json:"declaration"`
	Identity    HistoryIdentity `json:"identity"`
}
type OwnedPropertyReference struct {
	Representation string          `json:"representation"`
	Identity       HistoryIdentity `json:"identity"`
}
type OwnedPropertyField struct {
	Offset     int                      `json:"offset"`
	End        int                      `json:"end"`
	TagHex     string                   `json:"tag_hex"`
	Width      int                      `json:"width"`
	RawHex     string                   `json:"raw_hex"`
	Bits       *uint64                  `json:"unsigned_bits"`
	Text       *string                  `json:"text"`
	Route      OwnedPropertyRoute       `json:"route"`
	References []OwnedPropertyReference `json:"candidate_numeric_references"`
}
type OwnedPropertyPrefix struct {
	Record     int                  `json:"record"`
	Entity     uint32               `json:"entity"`
	PrefixEnd  int                  `json:"prefix_end"`
	Stop       int                  `json:"stop_offset"`
	StopReason string               `json:"stop_reason"`
	StopHex    string               `json:"stop_hex"`
	Fields     []OwnedPropertyField `json:"fields"`
}
type OwnedPropertyEvidence struct {
	Source                  string                     `json:"source"`
	Reason                  string                     `json:"reason"`
	Query                   OwnedPropertyQuery         `json:"query"`
	Owners                  map[uint32]HistoryIdentity `json:"owners"`
	Prefixes                []OwnedPropertyPrefix      `json:"prefixes"`
	ProductionAuthoritative bool                       `json:"production_authoritative"`
	ElapsedSeconds          *float64                   `json:"elapsed_seconds"`
}

// Incremental equivalent of objectiveEvidence.binding: every latest (owner,
// slot), including unknown owners, contributes to ambiguity. Replacement removes
// the old component route. No future declaration is visible at an earlier field.
type ownedRouteKey struct{ owner, slot uint32 }
type ownedRouteIndex struct {
	declarations []objectiveDeclaration
	owners       map[uint32]int
	latest       map[ownedRouteKey]objectiveDeclaration
	components   map[uint32]map[ownedRouteKey]objectiveDeclaration
	next         int
}

func newOwnedRouteIndex(e objectiveEvidence) *ownedRouteIndex {
	return &ownedRouteIndex{declarations: e.declarations, owners: e.owners,
		latest: map[ownedRouteKey]objectiveDeclaration{}, components: map[uint32]map[ownedRouteKey]objectiveDeclaration{}}
}
func (r *ownedRouteIndex) binding(entity uint32, offset int) (objectiveRoute, bool) {
	for r.next < len(r.declarations) && r.declarations[r.next].offset <= offset {
		d := r.declarations[r.next]
		r.next++
		k := ownedRouteKey{d.owner, d.slot}
		if previous, ok := r.latest[k]; ok {
			delete(r.components[previous.component], k)
		}
		r.latest[k] = d
		if d.component != 0 && d.class != 0 {
			if r.components[d.component] == nil {
				r.components[d.component] = map[ownedRouteKey]objectiveDeclaration{}
			}
			r.components[d.component][k] = d
		}
	}
	routes := []objectiveRoute{}
	if player, ok := r.owners[entity]; ok {
		routes = append(routes, objectiveRoute{owner: entity, player: player})
	}
	for _, d := range r.components[entity] {
		player, ok := r.owners[d.owner]
		if !ok {
			player = -1
		}
		routes = append(routes, objectiveRoute{d.owner, d.slot, d.class, d.offset, player})
	}
	if len(routes) != 1 || routes[0].player < 0 {
		return objectiveRoute{}, false
	}
	return routes[0], true
}

type ownedRawPrefix struct {
	record, entity, end, stop int
	reason                    string
	fields                    []objectiveProperty
}

func ownedRawPrefixes(b []byte) []ownedRawPrefix {
	out := []ownedRawPrefix{}
	for cursor := 0; cursor < len(b); {
		rel := bytes.IndexByte(b[cursor:], 0x23)
		if rel < 0 {
			break
		}
		start := cursor + rel
		cursor = start + 1
		if start+14 > len(b) || binary.LittleEndian.Uint32(b[start+5:start+9]) != 0 {
			continue
		}
		x := ownedRawPrefix{record: start, entity: int(binary.LittleEndian.Uint32(b[start+1 : start+5])), end: start + 9}
		for at := start + 9; ; {
			x.stop = at
			if at+5 > len(b) {
				x.reason = "truncated_field_header"
				break
			}
			tag := binary.LittleEndian.Uint32(b[at : at+4])
			size := int(b[at+4])
			end := at + 5 + size
			isText := tag == objectiveNameTag || tag == objectiveTimerTag
			if size != 1 && size != 2 && size != 4 && size != 8 && !(isText && size <= 64) {
				x.reason = "unsupported_field_width"
				break
			}
			if end > len(b) {
				x.reason = "truncated_field_value"
				break
			}
			p := objectiveProperty{offset: at, record: start, end: end, size: size, entity: uint32(x.entity), tag: tag}
			if isText {
				p.text = string(b[at+5 : end])
			} else {
				for i := 0; i < size; i++ {
					p.bits |= uint64(b[at+5+i]) << uint(8*i)
				}
			}
			x.fields = append(x.fields, p)
			x.end = end
			x.stop = end
			if end == len(b) {
				x.reason = "buffer_end"
				break
			}
			if b[end] != 0x22 {
				x.reason = "no_inherited_continuation"
				break
			}
			at = end + 1
		}
		out = append(out, x)
	}
	return out
}

func InspectOwnedPropertyFramesBuffer(b []byte, h Header, q OwnedPropertyQuery) OwnedPropertyEvidence {
	r := OwnedPropertyEvidence{Source: OwnedPropertyEvidenceSource, Query: q, Owners: map[uint32]HistoryIdentity{}, Prefixes: []OwnedPropertyPrefix{}}
	ids, err := historyIdentities(h)
	if err != nil {
		r.Reason = err.Error()
		return r
	}
	if q.Start < 0 || q.End > len(b) || q.End <= q.Start || q.TargetStart < q.Start || q.TargetEnd > q.End || q.TargetEnd <= q.TargetStart {
		r.Reason = "invalid_query_bounds"
		return r
	}
	if _, ok := ids[q.TargetUID]; !ok {
		r.Reason = "unknown_target_uid"
		return r
	}
	decls, fields := objectiveComponentFields(b)
	e := objectiveEvidence{declarations: decls, properties: fields, owners: objectiveOwners(h.Players, fields)}
	for entity, player := range e.owners {
		r.Owners[entity] = ids[h.Players[player].ID]
	}
	if len(e.owners) != len(ids) {
		r.Reason = "incomplete_or_ambiguous_uid_owners"
		return r
	}
	prefixes := ownedRawPrefixes(b)
	type location struct {
		prefix, field int
		property      objectiveProperty
	}
	locations := []location{}
	for i, x := range prefixes {
		for j, p := range x.fields {
			if p.offset >= q.Start && p.offset < q.End {
				locations = append(locations, location{i, j, p})
			}
		}
	}
	sort.Slice(locations, func(i, j int) bool { return locations[i].property.offset < locations[j].property.offset })
	index := newOwnedRouteIndex(e)
	selected := map[int][]OwnedPropertyField{}
	for _, l := range locations {
		p := l.property
		route, ok := index.binding(p.entity, p.offset)
		if !ok {
			continue
		}
		identity := ids[h.Players[route.player].ID]
		ref := []OwnedPropertyReference{}
		isText := p.tag == objectiveNameTag || p.tag == objectiveTimerTag
		if !isText {
			if p.size == 8 {
				if target, found := ids[p.bits]; found {
					ref = append(ref, OwnedPropertyReference{"exact_header_uid64", target})
				}
			}
			if (p.size == 4 || p.size == 8) && p.bits <= uint64(^uint32(0)) {
				if target, found := r.Owners[uint32(p.bits)]; found {
					ref = append(ref, OwnedPropertyReference{fmt.Sprintf("exact_uid_owner_entity_u%d", p.size*8), target})
				}
			}
		}
		inTarget := identity.UID == q.TargetUID && p.offset >= q.TargetStart && p.offset < q.TargetEnd
		if !inTarget && len(ref) == 0 {
			continue
		}
		x := OwnedPropertyField{Offset: p.offset, End: p.end, TagHex: hex.EncodeToString(b[p.offset : p.offset+4]), Width: p.size, RawHex: hex.EncodeToString(b[p.offset+5 : p.end]), Route: OwnedPropertyRoute{route.owner, route.slot, route.class, route.declaration, identity}, References: ref}
		if isText {
			value := p.text
			x.Text = &value
		} else {
			value := p.bits
			x.Bits = &value
		}
		selected[l.prefix] = append(selected[l.prefix], x)
	}
	for i, x := range prefixes {
		ps := selected[i]
		if len(ps) == 0 {
			continue
		}
		stopEnd := x.stop + 32
		if stopEnd > len(b) {
			stopEnd = len(b)
		}
		r.Prefixes = append(r.Prefixes, OwnedPropertyPrefix{x.record, uint32(x.entity), x.end, x.stop, x.reason, hex.EncodeToString(b[x.stop:stopEnd]), ps})
	}
	r.Reason = "bounded_scalar_text_prefixes_only_not_complete_component_or_causal_evidence"
	return r
}
