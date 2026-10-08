package dissect

// A nine-player header alone is incomplete evidence. Accept it ONLY when the
// full ten-slot initial packet table independently proves nine active profiles
// and one explicit empty slot. No identity/counter is synthesized for that slot.
import (
	"bytes"
	"encoding/binary"
	"encoding/json"
)

const emptyInventorySource = "explicit_ten_slot_empty_participant_v1"

func explicitEmptyParticipantInventory(h Header, initial []Player, data []byte, feedback []MatchUpdate) map[string]any {
	if len(h.Players) != 9 || len(initial) != 9 || !h.ActionPhaseDetected || h.ActionPhaseStartOffset <= 0 || h.ActionPhaseStartOffset >= int64(len(data)) {
		return nil
	}
	for _, f := range feedback {
		if f.Type == PlayerLeave {
			return nil
		}
	}
	players := map[string]Player{}
	for _, p := range h.Players {
		if p.ID == 0 || p.ID == ^uint64(0) || p.Username == "" || p.ProfileID == "" || p.TeamIndex < 0 || p.TeamIndex > 1 {
			return nil
		}
		if _, found := players[p.Username]; found {
			return nil
		}
		players[p.Username] = p
	}
	for _, p := range initial {
		q, ok := players[p.Username]
		if !ok || p.ID != q.ID || p.TeamIndex != q.TeamIndex {
			return nil
		}
	}
	marker := []byte{0x22, 0x07, 0x94, 0x9b, 0xdc}
	positions := []int{}
	for cursor := 0; cursor < len(data); {
		at := bytes.Index(data[cursor:], marker)
		if at < 0 {
			break
		}
		at += cursor
		cursor = at + len(marker)
		if int64(at) < h.ActionPhaseStartOffset {
			positions = append(positions, at)
		}
	}
	if len(positions) != 10 {
		return nil
	}
	slots := []map[string]any{}
	seen := map[string]bool{}
	empty := 0
	for i, at := range positions {
		end := int(h.ActionPhaseStartOffset)
		if i+1 < len(positions) {
			end = positions[i+1]
		}
		if at+6 > end {
			return nil
		}
		n := int(data[at+5])
		if at+6+n > end {
			return nil
		}
		name := string(data[at+6 : at+6+n])
		packet := data[at:end]
		profileTag := []byte{0x8a, 0x50, 0x9b, 0xd0}
		pa := bytes.Index(packet, profileTag)
		uidTag := []byte{0xee, 0xd4, 0x45, 0xc8}
		ua := bytes.Index(packet, uidTag)
		if pa < 0 || pa+5 > len(packet) || ua < 0 || ua+13 > len(packet) || packet[ua+4] != 8 {
			return nil
		}
		pn := int(packet[pa+4])
		if pa+5+pn > len(packet) {
			return nil
		}
		profile := string(packet[pa+5 : pa+5+pn])
		uid := binary.LittleEndian.Uint64(packet[ua+5 : ua+13])
		row := map[string]any{"name_offset": at, "profile_offset": at + pa, "uid_offset": at + ua, "username": name, "profile_id": profile, "uid": uid}
		if name == "" {
			opTag := []byte{0x22, 0xa9, 0x26, 0x0b, 0xe4, 8}
			oa := bytes.Index(packet, opTag)
			if profile != "" || uid != ^uint64(0) || oa < 0 || oa+14 > len(packet) || binary.LittleEndian.Uint64(packet[oa+6:oa+14]) != 0 {
				return nil
			}
			row["operator_offset"] = at + oa
			row["operator_id"] = uint64(0)
			empty++
		} else {
			p, ok := players[name]
			if !ok || seen[name] || p.ID != uid || p.ProfileID != profile {
				return nil
			}
			seen[name] = true
			row["team"] = p.TeamIndex
		}
		slots = append(slots, row)
	}
	if empty != 1 || len(seen) != 9 {
		return nil
	}
	// Every typed runtime UID must belong to this exact nine-player inventory.
	_, fields := objectiveComponentFields(data)
	owners := objectiveOwners(h.Players, fields)
	if len(owners) != 9 {
		return nil
	}
	for _, f := range fields {
		if f.tag != objectiveUIDTag {
			continue
		}
		known := false
		for _, p := range h.Players {
			if p.ID == f.bits {
				known = true
				break
			}
		}
		if f.size != 8 || !known {
			return nil
		}
	}
	return map[string]any{"source": emptyInventorySource, "action_offset": h.ActionPhaseStartOffset, "slots": slots}
}

func explicitInventoryValid(h Header) bool {
	if len(h.Players) != 9 || h.ParticipantEvidence == nil || !h.ActionPhaseDetected {
		return false
	}
	var proof struct {
		Source string `json:"source"`
		Action int64  `json:"action_offset"`
		Slots  []struct {
			NameOffset     int     `json:"name_offset"`
			ProfileOffset  int     `json:"profile_offset"`
			UIDOffset      int     `json:"uid_offset"`
			OperatorOffset int     `json:"operator_offset"`
			OperatorID     *uint64 `json:"operator_id"`
			Name           string  `json:"username"`
			Profile        string  `json:"profile_id"`
			UID            uint64  `json:"uid"`
			Team           int     `json:"team"`
		} `json:"slots"`
	}
	data, err := json.Marshal(h.ParticipantEvidence)
	if err != nil || json.Unmarshal(data, &proof) != nil || proof.Source != emptyInventorySource || proof.Action <= 0 || proof.Action != h.ActionPhaseStartOffset || len(proof.Slots) != 10 {
		return false
	}
	players := map[string]Player{}
	profiles := map[string]bool{}
	uids := map[uint64]bool{}
	for _, p := range h.Players {
		if p.Username == "" || p.ProfileID == "" || p.ID == 0 || p.ID == ^uint64(0) || profiles[p.ProfileID] || uids[p.ID] {
			return false
		}
		players[p.Username] = p
		profiles[p.ProfileID] = true
		uids[p.ID] = true
	}
	if len(players) != 9 {
		return false
	}
	empty := 0
	seen := map[string]bool{}
	for i, s := range proof.Slots {
		end := int(proof.Action)
		if i+1 < len(proof.Slots) {
			end = proof.Slots[i+1].NameOffset
		}
		if s.NameOffset <= 0 || s.NameOffset >= s.ProfileOffset || s.ProfileOffset >= s.UIDOffset || s.UIDOffset >= end {
			return false
		}
		if s.Name == "" {
			if s.Profile != "" || s.UID != ^uint64(0) || s.OperatorID == nil || *s.OperatorID != 0 || s.OperatorOffset <= s.NameOffset || s.OperatorOffset >= s.ProfileOffset {
				return false
			}
			empty++
		} else {
			p, ok := players[s.Name]
			if !ok || seen[s.Name] || p.ProfileID != s.Profile || p.ID != s.UID || p.TeamIndex != s.Team {
				return false
			}
			seen[s.Name] = true
		}
	}
	return empty == 1 && len(seen) == 9
}
