package dissect

// A named disconnected slot is not an empty anonymous slot. The separate
// proof below requires an explicit absent body at action start, then a newly
// created zero-vitals/state-4 body, one late UID and a restored scoreboard.
// It never adds a combatant, credits the restoration as kills or changes the
// action-start/operator implementation. Cross-round identity/counter bridges
// are additionally required by the Python whole-map validator.
import (
	"bytes"
	"encoding/binary"
	"encoding/json"
)

const inactiveReconnectSource = "explicit_inactive_reconnect_participant_v1"
const nilParticipantProfile = "00000000-0000-0000-0000-000000000000"

type inactiveReconnect struct {
	Name        string           `json:"username"`
	Team        int              `json:"team"`
	Slot        int              `json:"slot_index"`
	Owner       uint32           `json:"owner"`
	UID         uint64           `json:"uid"`
	UIDOffset   int              `json:"uid_offset"`
	AbsentBody  int              `json:"absent_body_offset"`
	Body        uint32           `json:"body_component"`
	BodyOffset  int              `json:"body_offset"`
	Score       uint32           `json:"score_component"`
	ScoreOffset int              `json:"score_offset"`
	BodyFields  []CreditProperty `json:"body_fields"`
	Counters    []CreditSample   `json:"counters"`
}

// Decode the same initial table as the existing empty-slot proof, retaining
// every named slot and the exact typed nil profile/invalid UID/operator fields.
func reconnectSlots(h Header, data []byte) ([]map[string]any, int) {
	marker := []byte{0x22, 0x07, 0x94, 0x9b, 0xdc}
	positions := []int{}
	for cursor := 0; cursor < int(h.ActionPhaseStartOffset); {
		at := bytes.Index(data[cursor:int(h.ActionPhaseStartOffset)], marker)
		if at < 0 {
			break
		}
		at += cursor
		positions = append(positions, at)
		cursor = at + len(marker)
	}
	if len(positions) != 10 {
		return nil, -1
	}
	slots, missing := []map[string]any{}, -1
	for i, at := range positions {
		end := int(h.ActionPhaseStartOffset)
		if i+1 < len(positions) {
			end = positions[i+1]
		}
		packet := data[at:end]
		if len(packet) < 6 || 6+int(packet[5]) > len(packet) {
			return nil, -1
		}
		name := string(packet[6 : 6+int(packet[5])])
		pa := bytes.Index(packet, []byte{0x8a, 0x50, 0x9b, 0xd0})
		ua := bytes.Index(packet, []byte{0xee, 0xd4, 0x45, 0xc8})
		if pa < 0 || pa+5 > len(packet) || ua < 0 || ua+13 > len(packet) || packet[ua+4] != 8 {
			return nil, -1
		}
		pn := int(packet[pa+4])
		if pa+5+pn > len(packet) {
			return nil, -1
		}
		profile := string(packet[pa+5 : pa+5+pn])
		uid := binary.LittleEndian.Uint64(packet[ua+5 : ua+13])
		row := map[string]any{"name_offset": at, "profile_offset": at + pa, "uid_offset": at + ua, "username": name, "profile_id": profile, "uid": uid}
		if profile == nilParticipantProfile && uid == ^uint64(0) && name != "" {
			if missing >= 0 {
				return nil, -1
			}
			missing = i
			oa := bytes.Index(packet, []byte{0x22, 0xa9, 0x26, 0x0b, 0xe4, 8})
			if oa < 0 || oa+14 > len(packet) || binary.LittleEndian.Uint64(packet[oa+6:oa+14]) != 0 {
				return nil, -1
			}
			row["operator_offset"] = at + oa
			row["operator_id"] = uint64(0)
		} else {
			found := false
			for _, p := range h.Players {
				if p.Username == name && p.ID == uid && p.ProfileID == profile {
					row["team"] = p.TeamIndex
					found = true
					break
				}
			}
			if !found {
				return nil, -1
			}
		}
		slots = append(slots, row)
	}
	return slots, missing
}

func inactiveReconnectInventory(h Header, initial []Player, data []byte, feedback []MatchUpdate) map[string]any {
	if len(h.Players) != 9 || len(initial) != 9 || !h.ActionPhaseDetected || h.ActionPhaseStartOffset <= 0 || h.ActionPhaseStartOffset >= int64(len(data)) {
		return nil
	}
	for _, p := range initial {
		found := false
		for _, q := range h.Players {
			if p.Username == q.Username && p.ID == q.ID && p.TeamIndex == q.TeamIndex {
				found = true
			}
		}
		if !found {
			return nil
		}
	}
	slots, index := reconnectSlots(h, data)
	if index < 1 {
		return nil
	}
	name := slots[index]["username"].(string)
	for _, f := range feedback {
		if f.Type == PlayerLeave || f.Username == name || f.Target == name {
			return nil
		}
	}
	decls, fields := objectiveComponentFields(data)
	known := map[uint64]bool{}
	for _, p := range h.Players {
		known[p.ID] = true
	}
	unknown := []objectiveProperty{}
	for _, f := range fields {
		if f.tag == objectiveUIDTag && !known[f.bits] {
			unknown = append(unknown, f)
		}
	}
	if len(unknown) != 1 || unknown[0].size != 8 {
		return nil
	}
	u := unknown[0]
	p := inactiveReconnect{Name: name, Team: index / 5, Slot: index, Owner: u.entity, UID: u.bits, UIDOffset: u.offset, BodyFields: []CreditProperty{}, Counters: []CreditSample{}}
	for _, d := range decls {
		if d.owner != u.entity {
			continue
		}
		if d.slot == objectiveBodySlot {
			if d.component == 0 && d.class == 0 && p.AbsentBody == 0 {
				p.AbsentBody = d.offset
			} else if d.component != 0 && d.class == objectiveBodyClass && p.Body == 0 {
				p.Body = d.component
				p.BodyOffset = d.offset
			} else {
				return nil
			}
		}
		if d.slot == creditScoreSlot {
			if p.Score != 0 || d.component == 0 || d.class != creditScoreClass {
				return nil
			}
			p.Score = d.component
			p.ScoreOffset = d.offset
		}
	}
	for _, d := range decls {
		if (d.component == p.Body || d.component == p.Score) && d.owner != p.Owner {
			return nil
		}
	}
	for _, f := range fields {
		if f.entity == p.Body && (f.tag == objectiveBodyState || reconnectVital(f.tag)) {
			p.BodyFields = append(p.BodyFields, CreditProperty{f.offset, f.entity, f.tag, f.size, f.bits})
		}
	}
	for _, f := range creditCounterFields(data) {
		if f.entity == p.Score {
			if f.size != 4 || f.bits > 250 {
				return nil
			}
			p.Counters = append(p.Counters, CreditSample{f.offset, uint32(f.bits), p.Score, p.Owner, p.ScoreOffset})
		}
	}
	proof := map[string]any{"source": inactiveReconnectSource, "action_offset": h.ActionPhaseStartOffset, "slots": slots, "inactive_reconnect": p}
	h.ParticipantEvidence = proof
	if !explicitInventoryValid(h) {
		return nil
	}
	return proof
}

func reconnectVital(tag uint32) bool {
	return tag == 0xc9762625 || tag == 0x72a64911 || tag == 0xdad23f01 || tag == 0x7bcfad80
}

func explicitInventoryValid(h Header) bool {
	if explicitEmptyInventoryValid(h) {
		return true
	}
	if h.ParticipantEvidence == nil || h.ParticipantEvidence["source"] != inactiveReconnectSource {
		return false
	}
	var proof struct {
		Action    int64             `json:"action_offset"`
		Slots     []map[string]any  `json:"slots"`
		Reconnect inactiveReconnect `json:"inactive_reconnect"`
	}
	raw, err := json.Marshal(h.ParticipantEvidence)
	if err != nil {
		return false
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.UseNumber()
	if decoder.Decode(&proof) != nil || proof.Action != h.ActionPhaseStartOffset || len(proof.Slots) != 10 {
		return false
	}
	p := proof.Reconnect
	if p.Slot < 1 || p.Slot > 9 || p.Name == "" || p.Team != p.Slot/5 || p.Owner == 0 || p.UID == 0 || p.UID == ^uint64(0) || p.Body == 0 || p.Score == 0 || p.Body == p.Score {
		return false
	}
	for _, player := range h.Players {
		if player.ID == p.UID || player.Username == p.Name {
			return false
		}
	}
	slot := proof.Slots[p.Slot]
	before := proof.Slots[p.Slot-1]
	if slot["username"] != p.Name || slot["profile_id"] != nilParticipantProfile || slot["uid"] != json.Number("18446744073709551615") || slot["operator_id"] != json.Number("0") {
		return false
	}
	if !(participantOffset(before, "uid_offset") > 0 && participantOffset(before, "uid_offset")+13 < p.AbsentBody && p.AbsentBody < participantOffset(slot, "name_offset") && p.AbsentBody < int(proof.Action) && int(proof.Action) < p.BodyOffset && p.BodyOffset < p.ScoreOffset && p.ScoreOffset < p.UIDOffset) {
		return false
	}
	seen := map[uint32]bool{}
	for _, f := range p.BodyFields {
		if f.Entity != p.Body || f.Size != 4 || f.Offset <= p.BodyOffset || f.Offset >= p.UIDOffset || seen[f.Tag] {
			return false
		}
		if f.Tag == objectiveBodyState {
			if f.Bits != 4 {
				return false
			}
		} else if !reconnectVital(f.Tag) || f.Bits != 0 {
			return false
		}
		seen[f.Tag] = true
	}
	if len(seen) != 5 || !seen[objectiveBodyState] || len(p.Counters) != 2 {
		return false
	}
	a, b := p.Counters[0], p.Counters[1]
	if a.Owner != p.Owner || b.Owner != p.Owner || a.Component != p.Score || b.Component != p.Score || a.DeclarationOffset != p.ScoreOffset || b.DeclarationOffset != p.ScoreOffset || !(p.ScoreOffset < a.Offset && a.Offset < p.UIDOffset && p.UIDOffset < b.Offset) || a.Value != 0 || b.Value > 250 {
		return false
	}
	// Reuse the unchanged strict ten-slot validator for the nine active slots.
	// Only the separately proven absent slot is canonicalized for that check.
	slot["username"] = ""
	slot["profile_id"] = ""
	canonical := map[string]any{"source": emptyInventorySource, "action_offset": proof.Action, "slots": proof.Slots}
	copyHeader := h
	copyHeader.ParticipantEvidence = canonical
	return explicitEmptyInventoryValid(copyHeader)
}

func participantOffset(slot map[string]any, key string) int {
	n, ok := slot[key].(json.Number)
	if !ok {
		return -1
	}
	value, err := n.Int64()
	if err != nil || value <= 0 || value > 1<<31-1 {
		return -1
	}
	return int(value)
}
