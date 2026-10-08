package dissect

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"testing"
)

func emptyInventoryFixture() (Header, []Player, []byte) {
	h := Header{ActionPhaseDetected: true, ActionPhaseStartOffset: 10000, GameMode: Bomb}
	h.Teams[0].Role = Attack
	h.Teams[1].Role = Defense
	data := make([]byte, 10)
	for i := 0; i < 10; i++ {
		name, profile := "", ""
		uid := ^uint64(0)
		if i < 9 {
			name = fmt.Sprintf("Player%d", i)
			profile = fmt.Sprintf("00000000-0000-0000-0000-%012d", i+1)
			uid = uint64(i + 1)
			h.Players = append(h.Players, Player{Username: name, ProfileID: profile, ID: uid, TeamIndex: i / 5})
		}
		data = append(data, 0x22, 0x07, 0x94, 0x9b, 0xdc, byte(len(name)))
		data = append(data, []byte(name)...)
		if i == 9 {
			data = append(data, 0x22, 0xa9, 0x26, 0x0b, 0xe4, 8)
			data = append(data, make([]byte, 8)...)
		}
		data = append(data, 0x8a, 0x50, 0x9b, 0xd0, byte(len(profile)))
		data = append(data, []byte(profile)...)
		if i < 9 {
			data = append(data, 0x23)
			data = binary.LittleEndian.AppendUint32(data, uint32(100+i))
			data = append(data, make([]byte, 4)...)
		} else {
			data = append(data, 0x22)
		}
		data = append(data, 0xee, 0xd4, 0x45, 0xc8, 8)
		data = binary.LittleEndian.AppendUint64(data, uid)
	}
	data = append(data, make([]byte, 10001-len(data))...)
	return h, append([]Player(nil), h.Players...), data
}

func TestNineParticipantsRequireExplicitEmptyTenthSlot(t *testing.T) {
	h, initial, data := emptyInventoryFixture()
	h.ParticipantEvidence = explicitEmptyParticipantInventory(h, initial, data, nil)
	if !explicitInventoryValid(h) || !objectiveRosterValid(h) {
		t.Fatal("complete nine-plus-empty inventory rejected")
	}
	if h.ParticipantEvidence == nil {
		t.Fatal("missing empty-slot proof")
	}
}

func TestEmptySlotInventoryRejectsMissingOrConflictingFacts(t *testing.T) {
	for _, mutation := range []string{"no_slot", "no_operator", "active_slot", "nil_profile", "changed_uid", "initial_conflict", "unknown_uid", "leave", "no_action", "source_only", "proof_uid", "proof_offset", "proof_profile", "proof_action"} {
		t.Run(mutation, func(t *testing.T) {
			h, initial, data := emptyInventoryFixture()
			feed := []MatchUpdate{}
			switch mutation {
			case "no_slot":
				data = data[:len(data)-40]
			case "no_operator":
				for i := 0; i < len(data)-6; i++ {
					if data[i] == 0x22 && data[i+1] == 0xa9 {
						data[i+1] = 0
					}
				}
			case "active_slot":
				at := bytes.Index(data, []byte{0x22, 0xee, 0xd4, 0x45, 0xc8, 8, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff})
				data[at+6] = 0
			case "nil_profile":
				h.Players[0].ProfileID = ""
			case "changed_uid":
				h.Players[0].ID = 999
			case "initial_conflict":
				initial[0].TeamIndex = 1
			case "unknown_uid":
				data = append(data, 0x23, 99, 0, 0, 0, 0, 0, 0, 0, 0xee, 0xd4, 0x45, 0xc8, 8)
				data = binary.LittleEndian.AppendUint64(data, 999)
			case "leave":
				feed = append(feed, MatchUpdate{Type: PlayerLeave})
			case "no_action":
				h.ActionPhaseDetected = false
			}
			h.ParticipantEvidence = explicitEmptyParticipantInventory(h, initial, data, feed)
			if mutation == "proof_action" && h.ParticipantEvidence != nil {
				h.ParticipantEvidence["action_offset"] = int64(9999)
			}
			if mutation == "source_only" {
				h.ParticipantEvidence = map[string]any{"source": emptyInventorySource}
			}
			if h.ParticipantEvidence != nil && (mutation == "proof_uid" || mutation == "proof_offset" || mutation == "proof_profile") {
				s := h.ParticipantEvidence["slots"].([]map[string]any)[0]
				if mutation == "proof_uid" {
					s["uid"] = uint64(999)
				}
				if mutation == "proof_offset" {
					s["profile_offset"] = 0
				}
				if mutation == "proof_profile" {
					s["profile_id"] = "wrong"
				}
			}
			if explicitInventoryValid(h) {
				t.Fatalf("unsafe %s inventory accepted", mutation)
			}
		})
	}
}
