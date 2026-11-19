package dissect

// Credited kills are a separate scoreboard observation, not a replacement for
// MatchFeedback finishers. This additive reader leaves the frozen Reader.Read
// and operator/action-start implementation untouched.
import (
	"bytes"
	"encoding/binary"
	"io"
	"sort"
)

const (
	CreditedKillSource        = "stable_uid_scoreboard_delta_v1"
	creditKillTag      uint32 = 0x9db1d21c
	creditScoreSlot    uint32 = 0x389b21eb
	creditScoreClass   uint32 = 0xa191a518
)

type CreditSample struct {
	Offset            int    `json:"offset"`
	Value             uint32 `json:"value"`
	Component         uint32 `json:"component"`
	Owner             uint32 `json:"owner"`
	DeclarationOffset int    `json:"declarationOffset"`
}

type PlayerKillCredit struct {
	UID        uint64            `json:"uid"`
	ProfileID  string            `json:"profileID,omitempty"`
	Username   string            `json:"username"`
	Team       int               `json:"team"`
	Initial    *uint32           `json:"initial"`
	Terminal   *uint32           `json:"terminal"`
	Kills      *uint32           `json:"kills"`
	Samples    []CreditSample    `json:"samples"`
	Reason     string            `json:"reason"`
	CounterGap *CreditCounterGap `json:"counterGap,omitempty"`
}

// This records the physical source of a missing counter during an in-round
// UID replacement. A later round must independently anchor the value; this
// observation alone never supplies a kill count.
type CreditCounterGap struct {
	Source            string `json:"source"`
	Owner             uint32 `json:"owner"`
	OldUID            uint64 `json:"oldUID"`
	NewUID            uint64 `json:"newUID"`
	OldUIDOffset      int    `json:"oldUIDOffset"`
	NewUIDOffset      int    `json:"newUIDOffset"`
	OldScoreComponent uint32 `json:"oldScoreComponent"`
	NewScoreComponent uint32 `json:"newScoreComponent"`
	OldScoreOffset    int    `json:"oldScoreOffset"`
	NewScoreOffset    int    `json:"newScoreOffset"`
	OldSampleOffset   int    `json:"oldSampleOffset"`
	NewSampleOffset   int    `json:"newSampleOffset"`
}

type CreditFinish struct {
	Offset         int                     `json:"offset"`
	Feedback       MatchUpdate             `json:"feedback"`
	OffsetEvidence *NativeFeedbackEnvelope `json:"offsetEvidence,omitempty"`
}

type RoundKillCredit struct {
	Source              string             `json:"source"`
	Complete            bool               `json:"complete"`
	Reason              string             `json:"reason"`
	ActionStartOffset   int64              `json:"actionStartOffset"`
	Players             []PlayerKillCredit `json:"players"`
	Finishes            []CreditFinish     `json:"finishes"`
	ParticipantEvidence map[string]any     `json:"participantEvidence,omitempty"`
}

// Structural evidence is also accepted for cached, independently decoded
// regression controls. These are observations, never official target totals.
type CreditDeclaration struct {
	Offset    int    `json:"offset"`
	Owner     uint32 `json:"owner"`
	Slot      uint32 `json:"slot"`
	Component uint32 `json:"component"`
	Class     uint32 `json:"class"`
}

type CreditProperty struct {
	Offset int    `json:"offset"`
	Entity uint32 `json:"entity"`
	Tag    uint32 `json:"tag"`
	Size   int    `json:"size"`
	Bits   uint64 `json:"bits"`
}

type CreditStructuralEvidence struct {
	Header       Header              `json:"header"`
	Declarations []CreditDeclaration `json:"declarations"`
	Properties   []CreditProperty    `json:"properties"`
	Finishes     []CreditFinish      `json:"finishes"`
}

func ValidateKillCreditEvidence(in CreditStructuralEvidence) RoundKillCredit {
	declarations := []objectiveDeclaration{}
	uidFields, counters := []objectiveProperty{}, []objectiveProperty{}
	for _, d := range in.Declarations {
		declarations = append(declarations, objectiveDeclaration{d.Offset, d.Owner, d.Slot, d.Component, d.Class})
	}
	for _, f := range in.Properties {
		p := objectiveProperty{offset: f.Offset, entity: f.Entity, tag: f.Tag, size: f.Size, bits: f.Bits}
		if f.Tag == objectiveUIDTag {
			uidFields = append(uidFields, p)
		}
		if f.Tag == creditKillTag {
			counters = append(counters, p)
		}
	}
	sort.Slice(declarations, func(i, j int) bool { return declarations[i].offset < declarations[j].offset })
	sort.Slice(counters, func(i, j int) bool { return counters[i].offset < counters[j].offset })
	return deriveKillCreditObservations(in.Header, declarations, uidFields, counters, in.Finishes)
}

// ReadKillCredit uses the same decompression, header, operator and feedback
// parser. Exact callback provenance can supply a standalone Death's missing
// physical offset; raw feedback retains its original owner/time. Counter increments
// have packet offsets only: no victim, downer or elimination time is guessed.
func ReadKillCredit(in io.Reader) (Header, RoundKillCredit, error) {
	header, credit, _, _, err := readKillCreditEnvelopes(in)
	return header, credit, err
}

// Decode only explicitly framed properties, including inherited fields in a
// record. A byte pattern without a record/entity/width is never a counter.
func creditCounterFields(data []byte) []objectiveProperty {
	fields := []objectiveProperty{}
	seen := map[int]bool{}
	for cursor := 0; cursor < len(data); {
		rel := bytes.IndexByte(data[cursor:], 0x23)
		if rel < 0 {
			break
		}
		start := cursor + rel
		cursor = start + 1
		if start+14 > len(data) || binary.LittleEndian.Uint32(data[start+5:start+9]) != 0 {
			continue
		}
		entity := binary.LittleEndian.Uint32(data[start+1 : start+5])
		for at := start + 9; at+5 <= len(data); {
			tag := binary.LittleEndian.Uint32(data[at : at+4])
			size := int(data[at+4])
			end := at + 5 + size
			text := tag == objectiveTimerTag || tag == objectiveNameTag
			if end > len(data) || (size != 1 && size != 2 && size != 4 && size != 8 && !(text && size <= 64)) {
				break
			}
			if tag == creditKillTag && !seen[at] {
				seen[at] = true
				var bits uint64
				for i := 0; i < size; i++ {
					bits |= uint64(data[at+5+i]) << uint(8*i)
				}
				fields = append(fields, objectiveProperty{offset: at, record: start, end: end, size: size, entity: entity, tag: tag, bits: bits})
			}
			if end >= len(data) || data[end] != 0x22 {
				break
			}
			at = end + 1
		}
	}
	sort.Slice(fields, func(i, j int) bool { return fields[i].offset < fields[j].offset })
	return fields
}

func deriveKillCredit(header Header, data []byte, finishes []CreditFinish) RoundKillCredit {
	declarations, uidFields := objectiveComponentFields(data)
	return deriveKillCreditObservations(header, declarations, uidFields, creditCounterFields(data), finishes)
}

func deriveKillCreditObservations(header Header, declarations []objectiveDeclaration, uidFields, counters []objectiveProperty, finishes []CreditFinish) RoundKillCredit {
	result := RoundKillCredit{Source: CreditedKillSource, Complete: true, Reason: CreditedKillSource,
		ActionStartOffset: header.ActionPhaseStartOffset, Players: []PlayerKillCredit{}, Finishes: finishes, ParticipantEvidence: header.ParticipantEvidence}
	ids := map[uint64]bool{}
	names := map[string]bool{}
	teams := [2]int{}
	valid := len(header.Players) == 10 || explicitInventoryValid(header)
	for _, p := range header.Players {
		if p.ID == 0 || ids[p.ID] || p.Username == "" || names[p.Username] || p.TeamIndex < 0 || p.TeamIndex > 1 {
			valid = false
		}
		ids[p.ID] = true
		names[p.Username] = true
		if p.TeamIndex >= 0 && p.TeamIndex < 2 {
			teams[p.TeamIndex]++
		}
		result.Players = append(result.Players, PlayerKillCredit{UID: p.ID, ProfileID: p.ProfileID, Username: p.Username, Team: p.TeamIndex, Samples: []CreditSample{}})
	}
	if !valid || (teams != [2]int{5, 5} && !(explicitInventoryValid(header) && (teams == [2]int{5, 4} || teams == [2]int{4, 5}))) {
		result.Complete = false
		result.Reason = "incomplete_or_ambiguous_uid_roster"
		for i := range result.Players {
			result.Players[i].Reason = result.Reason
		}
		return result
	}
	if header.Teams[0].Won == header.Teams[1].Won {
		result.Complete = false
		result.Reason = "round_not_completed_with_unique_winner"
		for i := range result.Players {
			result.Players[i].Reason = result.Reason
		}
		return result
	}
	evidence := objectiveEvidence{declarations: declarations, owners: objectiveOwners(header.Players, uidFields)}
	invalid := map[int]string{}
	previousBindings := map[uint32]int{}
	for _, f := range counters {
		route, ok := evidence.binding(f.entity, f.offset)
		if !ok || route.slot != creditScoreSlot || route.class != creditScoreClass {
			if player, seen := previousBindings[f.entity]; seen {
				invalid[player] = "scoreboard_route_became_ambiguous_or_unsupported"
			}
			continue
		}
		previousBindings[f.entity] = route.player
		if f.size != 4 || f.bits > 250 {
			invalid[route.player] = "invalid_counter_width_or_range"
			continue
		}
		p := &result.Players[route.player]
		p.Samples = append(p.Samples, CreditSample{f.offset, uint32(f.bits), f.entity, route.owner, route.declaration})
	}
	firstFinish := int(^uint(0) >> 1)
	for _, f := range finishes {
		if f.Offset <= 0 {
			firstFinish = 0
		}
		if f.Offset < firstFinish {
			firstFinish = f.Offset
		}
	}
	for i := range result.Players {
		p := &result.Players[i]
		reason := invalid[i]
		if len(p.Samples) == 0 {
			reason = "missing_direct_uid_counter"
			p.CounterGap = inRoundUIDCounterGap(*p, header.ActionPhaseStartOffset, declarations, uidFields, counters)
		} else {
			first, last := p.Samples[0], p.Samples[len(p.Samples)-1]
			if first.Offset >= firstFinish {
				reason = "baseline_not_before_first_elimination"
			}
			if header.ActionPhaseStartOffset > 0 && int64(first.Offset) >= header.ActionPhaseStartOffset {
				reason = "baseline_not_before_action_start"
			}
			for j, s := range p.Samples {
				if s.Component != first.Component || s.Owner != first.Owner {
					reason = "changed_scoreboard_component_or_owner"
				}
				if j > 0 && s.Value < p.Samples[j-1].Value {
					reason = "counter_decreased_within_round"
				}
				if header.ActionPhaseStartOffset > 0 && int64(s.Offset) < header.ActionPhaseStartOffset && s.Value != first.Value {
					reason = "counter_changed_before_action_start"
				}
			}
			if last.Value >= first.Value && last.Value-first.Value > 5 {
				reason = "round_delta_exceeds_opponents"
			}
			if reason == "" {
				initial, terminal, delta := first.Value, last.Value, last.Value-first.Value
				p.Initial = &initial
				p.Terminal = &terminal
				p.Kills = &delta
			}
		}
		if reason != "" {
			p.Reason = reason
			result.Complete = false
			result.Reason = "unresolved_player_counters"
		} else {
			p.Reason = CreditedKillSource
		}
	}
	return result
}

func inRoundUIDCounterGap(p PlayerKillCredit, action int64, declarations []objectiveDeclaration, uidFields, counters []objectiveProperty) *CreditCounterGap {
	if action <= 0 {
		return nil
	}
	var owner uint32
	var old, next objectiveProperty
	for _, f := range uidFields {
		if f.tag == objectiveUIDTag && f.size == 8 && f.bits == p.UID && f.offset < int(action) {
			if owner != 0 {
				return nil
			}
			owner, old = f.entity, f
		}
	}
	if owner == 0 {
		return nil
	}
	count := 0
	for _, f := range uidFields {
		if f.tag != objectiveUIDTag || f.size != 8 || f.entity != owner {
			continue
		}
		count++
		if f.bits != p.UID && f.bits != 0 && f.offset > int(action) {
			next = f
		}
	}
	if count != 2 || next.offset == 0 {
		return nil
	}
	var before, after objectiveDeclaration
	for _, d := range declarations {
		if d.owner != owner || d.slot != creditScoreSlot || d.class != creditScoreClass || d.component == 0 {
			continue
		}
		if d.offset < int(action) {
			if before.offset != 0 {
				return nil
			}
			before = d
		} else {
			if after.offset != 0 {
				return nil
			}
			after = d
		}
	}
	if before.offset == 0 || after.offset == 0 || before.component == after.component || after.offset > next.offset {
		return nil
	}
	oldSample, newSample := 0, 0
	for _, c := range counters {
		if c.entity != before.component && c.entity != after.component {
			continue
		}
		if c.size != 4 || c.bits != 0 {
			return nil
		}
		if c.entity == before.component {
			if c.offset < before.offset || c.offset >= int(action) || oldSample != 0 {
				return nil
			}
			oldSample = c.offset
		} else {
			if c.offset < after.offset || c.offset >= next.offset || newSample != 0 {
				return nil
			}
			newSample = c.offset
		}
	}
	if oldSample == 0 || newSample == 0 {
		return nil
	}
	return &CreditCounterGap{Source: "in_round_uid_replacement_zero_counters_v1", Owner: owner,
		OldUID: p.UID, NewUID: next.bits, OldUIDOffset: old.offset, NewUIDOffset: next.offset,
		OldScoreComponent: before.component, NewScoreComponent: after.component,
		OldScoreOffset: before.offset, NewScoreOffset: after.offset, OldSampleOffset: oldSample, NewSampleOffset: newSample}
}
