package dissect

import (
	"encoding/binary"
	"reflect"
	"testing"
)

func ownedTestProperty(entity, tag uint32, width int, value uint64) []byte {
	b := make([]byte, 14+width)
	b[0] = 0x23
	binary.LittleEndian.PutUint32(b[1:], entity)
	binary.LittleEndian.PutUint32(b[9:], tag)
	b[13] = byte(width)
	for i := 0; i < width; i++ {
		b[14+i] = byte(value >> uint(8*i))
	}
	return b
}
func ownedTestDeclaration(owner, slot, component, class uint32) []byte {
	b := make([]byte, 25)
	b[0] = 0x1b
	binary.LittleEndian.PutUint32(b[1:], owner)
	binary.LittleEndian.PutUint32(b[9:], slot)
	binary.LittleEndian.PutUint32(b[13:], component)
	binary.LittleEndian.PutUint32(b[21:], class)
	return b
}
func ownedTestBase() ([]byte, Header) {
	h := historyTestHeader()
	b := []byte{}
	for i, p := range h.Players {
		b = append(b, ownedTestProperty(uint32(100+i), objectiveUIDTag, 8, p.ID)...)
	}
	b = append(b, ownedTestDeclaration(100, objectiveBodySlot, 200, objectiveBodyClass)...)
	return b, h
}
func ownedTestFields(r OwnedPropertyEvidence) []OwnedPropertyField {
	f := []OwnedPropertyField{}
	for _, p := range r.Prefixes {
		f = append(f, p.Fields...)
	}
	return f
}
func TestOwnedRouteIndexMatchesStrictBinding(t *testing.T) {
	e := objectiveEvidence{owners: map[uint32]int{10: 0, 11: 1}, declarations: []objectiveDeclaration{
		{1, 10, 30, 100, 40}, {2, 99, 30, 100, 40}, {3, 99, 30, 0, 0},
		{4, 10, 30, 101, 40}, {5, 11, 31, 101, 40}, {6, 11, 31, 102, 40},
		{7, 10, 32, 101, 40}, {8, 10, 32, 0, 0}, {9, 11, 33, 10, 40},
	}}
	index := newOwnedRouteIndex(e)
	for at := 0; at <= 10; at++ {
		for _, entity := range []uint32{10, 11, 100, 101, 102} {
			want, wok := e.binding(entity, at)
			got, gok := index.binding(entity, at)
			if want != got || wok != gok {
				t.Fatalf("at%d entity%d: %v/%v != %v/%v", at, entity, got, gok, want, wok)
			}
		}
	}
}
func TestOwnedPropertyUnsignedBitsAndExactNumericReferences(t *testing.T) {
	b, h := ownedTestBase()
	start := len(b)
	b = append(b, ownedTestProperty(200, 1234, 8, ^uint64(0))...)
	b = append(b, ownedTestProperty(200, 1235, 8, h.Players[6].ID)...)
	b = append(b, ownedTestProperty(200, 1236, 4, 106)...)
	r := InspectOwnedPropertyFramesBuffer(b, h, OwnedPropertyQuery{start, len(b), h.Players[0].ID, start, len(b)})
	f := ownedTestFields(r)
	if len(f) != 3 || *f[0].Bits != ^uint64(0) || f[0].RawHex != "ffffffffffffffff" {
		t.Fatalf("raw unsigned value lost: %+v", r)
	}
	if len(f[1].References) != 1 || f[1].References[0].Identity.UID != h.Players[6].ID || f[1].References[0].Representation != "exact_header_uid64" {
		t.Fatal("exact UID equality missing")
	}
	if len(f[2].References) != 1 || f[2].References[0].Representation != "exact_uid_owner_entity_u32" {
		t.Fatal("exact owner reference missing")
	}
	if r.ProductionAuthoritative || r.ElapsedSeconds != nil {
		t.Fatal("numeric match was promoted")
	}
}
func TestOwnedPropertyInheritedUnknownWidthStopsWithoutSkipping(t *testing.T) {
	b, h := ownedTestBase()
	start := len(b)
	b = append(b, ownedTestProperty(200, objectiveBodyState, 4, 3)...)
	b = append(b, 0x22, 1, 2, 3, 4, 3, 0xaa, 0xbb, 0xcc, 0x22, 4, 3, 2, 1, 4, 9, 0, 0, 0)
	r := InspectOwnedPropertyFramesBuffer(b, h, OwnedPropertyQuery{start, len(b), h.Players[0].ID, start, len(b)})
	if len(r.Prefixes) != 1 || len(r.Prefixes[0].Fields) != 1 || r.Prefixes[0].StopReason != "unsupported_field_width" || r.Prefixes[0].Stop != start+19 {
		t.Fatalf("unknown middle bytes skipped: %+v", r)
	}
}
func TestOwnedPropertyInheritedTruncationRetained(t *testing.T) {
	b, h := ownedTestBase()
	start := len(b)
	b = append(b, ownedTestProperty(200, objectiveBodyState, 4, 3)...)
	b = append(b, 0x22, 1, 2, 3, 4, 8, 1, 2)
	r := InspectOwnedPropertyFramesBuffer(b, h, OwnedPropertyQuery{start, len(b), h.Players[0].ID, start, len(b)})
	if len(r.Prefixes) != 1 || r.Prefixes[0].StopReason != "truncated_field_value" || len(r.Prefixes[0].Fields) != 1 {
		t.Fatalf("truncation lost: %+v", r)
	}
}
func TestOwnedPropertyReplacementAndUnknownSharedOwnerRefuse(t *testing.T) {
	b, h := ownedTestBase()
	start := len(b)
	b = append(b, ownedTestProperty(200, 1234, 4, 1)...)
	b = append(b, ownedTestDeclaration(100, objectiveBodySlot, 201, objectiveBodyClass)...)
	b = append(b, ownedTestProperty(200, 1234, 4, 2)...)
	b = append(b, ownedTestProperty(201, 1234, 4, 3)...)
	b = append(b, ownedTestDeclaration(999, 77, 201, objectiveBodyClass)...)
	b = append(b, ownedTestProperty(201, 1234, 4, 4)...)
	r := InspectOwnedPropertyFramesBuffer(b, h, OwnedPropertyQuery{start, len(b), h.Players[0].ID, start, len(b)})
	f := ownedTestFields(r)
	values := []uint64{}
	for _, p := range f {
		values = append(values, *p.Bits)
	}
	if !reflect.DeepEqual(values, []uint64{1, 3}) {
		t.Fatalf("replacement/shared route leaked: %v", values)
	}
}
func TestOwnedPropertyAmbiguousUIDOwnersRefuseWholeEvidence(t *testing.T) {
	b, h := ownedTestBase()
	b = append(b, ownedTestProperty(999, objectiveUIDTag, 8, h.Players[0].ID)...)
	r := InspectOwnedPropertyFramesBuffer(b, h, OwnedPropertyQuery{0, len(b), h.Players[0].ID, 0, len(b)})
	if r.Reason != "incomplete_or_ambiguous_uid_owners" || len(r.Prefixes) != 0 {
		t.Fatalf("duplicate UID owner accepted: %+v", r)
	}
}
func TestOwnedPropertyTextWidthsAndQueryRefusal(t *testing.T) {
	b, h := ownedTestBase()
	start := len(b)
	b = append(b, ownedTestProperty(200, objectiveTimerTag, 3, uint64('1')|uint64('.')<<8|uint64('2')<<16)...)
	r := InspectOwnedPropertyFramesBuffer(b, h, OwnedPropertyQuery{start, len(b), h.Players[0].ID, start, len(b)})
	f := ownedTestFields(r)
	if len(f) != 1 || f[0].Text == nil || *f[0].Text != "1.2" || f[0].Bits != nil || len(f[0].References) != 0 {
		t.Fatal("text interpreted as numeric")
	}
	r = InspectOwnedPropertyFramesBuffer(b, h, OwnedPropertyQuery{start, len(b) + 1, h.Players[0].ID, start, len(b)})
	if r.Reason != "invalid_query_bounds" {
		t.Fatal("out-of-buffer query accepted")
	}
}
