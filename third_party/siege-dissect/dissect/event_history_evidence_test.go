package dissect

import (
	"encoding/binary"
	"fmt"
	"testing"
)

func historyTestHeader() Header {
	h := Header{}
	for i := 0; i < 10; i++ {
		h.Players = append(h.Players, Player{ID: uint64(1000 + i), Username: fmt.Sprintf("P%d", i), TeamIndex: i / 5, RoleImage: 900 + i, Alliance: 3 + i/5})
	}
	return h
}

func historyTestRef(p Player) []byte {
	b := make([]byte, 20)
	binary.LittleEndian.PutUint64(b, p.ID)
	binary.LittleEndian.PutUint64(b[8:], uint64(p.RoleImage))
	binary.LittleEndian.PutUint32(b[16:], uint32(p.Alliance))
	return b
}

func historyTestItem(kind byte, scalar uint32, a, b Player) []byte {
	width := map[byte]int{1: 62, 2: 62, 3: 41, 5: 53, 7: 53, 10: 26}[kind]
	x := make([]byte, width)
	x[0] = kind
	binary.LittleEndian.PutUint32(x[1:], scalar)
	at := 5
	if kind == 1 || kind == 2 || kind == 3 {
		binary.LittleEndian.PutUint64(x[5:], 123)
		binary.LittleEndian.PutUint64(x[13:], 456)
		at = 21
	} else if kind == 5 || kind == 7 {
		binary.LittleEndian.PutUint64(x[5:], 456)
		at = 13
	}
	copy(x[at:], historyTestRef(a))
	if kind == 1 || kind == 2 || kind == 5 || kind == 7 {
		copy(x[at+20:], historyTestRef(b))
	}
	if kind == 10 {
		x[25] = 2
	}
	return x
}

func historyTestBox(items ...[]byte) []byte {
	var payload []byte
	for _, i := range items {
		payload = append(payload, i...)
	}
	b := make([]byte, 25)
	binary.LittleEndian.PutUint32(b, 77)
	binary.LittleEndian.PutUint64(b[4:], uint64(13+len(payload)))
	binary.LittleEndian.PutUint32(b[12:], uint32(1+len(items)))
	copy(b[16:], []byte{9, 34, 1, 0, 0, 3, 0, 0, 0})
	return append(b, payload...)
}

func TestEventHistoryCumulativePrefixesRetainTiedListOrderAndRawActors(t *testing.T) {
	h := historyTestHeader()
	down := historyTestItem(5, 100, h.Players[0], h.Players[6])
	finish := historyTestItem(1, 100, h.Players[1], h.Players[6])
	b := append(historyTestBox(), historyTestBox(down)...)
	b = append(b, historyTestBox(down, finish)...)
	r := InspectEventHistoryBuffer(b, h)
	if !r.Complete || len(r.Containers) != 3 || len(r.Items) != 2 || r.ScalarTies["100"] != 2 {
		t.Fatalf("unexpected cumulative/tie evidence: %+v", r)
	}
	if r.Items[0].Kind != 5 || r.Items[1].Kind != 1 || r.Items[0].First.UID != h.Players[0].ID || r.Items[1].First.UID != h.Players[1].ID {
		t.Fatal("list order or separate first identities changed")
	}
	if r.ProductionAuthoritative || r.Items[0].ElapsedSeconds != nil || !r.ScalarsNondecreasing {
		t.Fatal("structural evidence promoted to production/time")
	}
}

func TestEventHistoryChangedCumulativeCopyRefuses(t *testing.T) {
	h := historyTestHeader()
	a := historyTestItem(1, 100, h.Players[0], h.Players[6])
	b := historyTestItem(1, 101, h.Players[1], h.Players[6])
	raw := append(historyTestBox(a), historyTestBox(b)...)
	r := InspectEventHistoryBuffer(raw, h)
	if r.Complete || r.Reason != "cumulative_items_changed_or_reordered" || len(r.Items) != 0 {
		t.Fatalf("replacement accepted: %+v", r)
	}
}

func TestEventHistoryUnknownMiddleAndTruncatedBoundsStayUnresolved(t *testing.T) {
	h := historyTestHeader()
	a := historyTestItem(1, 100, h.Players[0], h.Players[6])
	b := historyTestItem(1, 200, h.Players[1], h.Players[7])
	unknown := append([]byte{4}, make([]byte, 30)...)
	raw := append(historyTestBox(), historyTestBox(a, unknown, b)...)
	r := InspectEventHistoryBuffer(raw, h)
	if r.Complete || r.Reason != "partial_container_retained" || r.Containers[1].UnknownHex == "" || len(r.Containers[1].Items) != 1 {
		t.Fatalf("unknown item skipped: %+v", r)
	}
	raw = historyTestBox(a)
	descriptor := raw[16:25]
	if _, ok := historyBoxAt(raw[:len(raw)-1], 16, descriptor); ok {
		t.Fatal("truncated declared bounds accepted")
	}
	if InspectEventHistoryBuffer(raw[:len(raw)-1], h).Complete {
		t.Fatal("truncated evidence promoted")
	}
}

func TestEventHistoryHeaderAndReferenceIdentitySafeguards(t *testing.T) {
	h := historyTestHeader()
	item := historyTestItem(1, 100, h.Players[0], h.Players[6])
	ids, err := historyIdentities(h)
	if err != nil {
		t.Fatal(err)
	}
	item[29] ^= 1
	if _, ok := historyItemAt(item, 0, len(item), ids); ok {
		t.Fatal("wrong header icon accepted")
	}
	h.Players[1].ID = h.Players[0].ID
	if _, err := historyIdentities(h); err == nil {
		t.Fatal("duplicate UID accepted")
	}
	h = historyTestHeader()
	h.Players = h.Players[:9]
	if InspectEventHistoryBuffer(historyTestBox(), h).Complete {
		t.Fatal("nine-player header accepted")
	}
	h = historyTestHeader()
	h.Players[5].TeamIndex = 0
	if _, err := historyIdentities(h); err == nil {
		t.Fatal("six/four team inventory accepted")
	}
	h = historyTestHeader()
	h.Players[0].Alliance = int(uint64(1)<<32) + 3
	if _, err := historyIdentities(h); err == nil {
		t.Fatal("alliance value truncated to uint32")
	}
}

func TestEventHistoryFriendlySingleReferenceAndOpaqueKindsRemainDistinct(t *testing.T) {
	h := historyTestHeader()
	ids, err := historyIdentities(h)
	if err != nil {
		t.Fatal(err)
	}
	for _, kind := range []byte{2, 3, 10} {
		item := historyTestItem(kind, 100, h.Players[0], h.Players[1])
		x, ok := historyItemAt(item, 0, len(item), ids)
		if !ok || x.Kind != kind || x.ElapsedSeconds != nil {
			t.Fatalf("raw kind %d changed: %+v", kind, x)
		}
		if kind == 3 && (x.Single == nil || x.First != nil || x.Second != nil || x.Headshot != nil) {
			t.Fatal("unnamed death given actor pair or headshot")
		}
		if kind == 10 && (x.Single == nil || x.OpaqueTail == nil || *x.OpaqueTail != 2) {
			t.Fatal("opaque tail lost")
		}
	}
}

func TestEventHistoryKillFreeUnsupportedAnchorDoesNotInventHistory(t *testing.T) {
	h := historyTestHeader()
	raw := historyTestBox(historyTestItem(3, 100, h.Players[0], h.Players[1]))
	r := InspectEventHistoryBuffer(raw, h)
	if r.Complete || r.Reason != "no_bounded_two_reference_anchor" {
		t.Fatalf("unsupported anchor invented: %+v", r)
	}
}
