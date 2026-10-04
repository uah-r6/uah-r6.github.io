package dissect

import "testing"

func clockTestInherited(tag uint32, width int, value uint64) []byte {
	p := ownedTestProperty(123, tag, width, value)
	return append([]byte{0x22}, p[9:]...)
}
func TestClockPrefixGroupsSameRecordWithoutUnitPromotion(t *testing.T) {
	b := ownedTestProperty(123, 0xc9ef071f, 4, 43)
	b = append(b, clockTestInherited(0x6c463718, 4, 43983)...)
	r := InspectClockPrefixGroupsBuffer(b)
	if len(r.Groups) != 1 || len(r.Groups[0].Coarse) != 1 || len(r.Groups[0].Fine) != 1 || r.Groups[0].Entity != 123 {
		t.Fatal("joint fields lost")
	}
	if r.Groups[0].Coarse[0].Record != r.Groups[0].Fine[0].Record || r.ProductionAuthoritative || r.ElapsedSeconds != nil {
		t.Fatal("group invented units or lost record")
	}
}
func TestClockPrefixGroupsDoNotJoinSeparateRecords(t *testing.T) {
	b := ownedTestProperty(123, 0xc9ef071f, 4, 43)
	b = append(b, ownedTestProperty(123, 0x6c463718, 4, 43983)...)
	r := InspectClockPrefixGroupsBuffer(b)
	if len(r.Groups) != 2 || len(r.Groups[0].Fine) != 0 || len(r.Groups[1].Coarse) != 0 {
		t.Fatal("separate records were paired by proximity")
	}
}
func TestClockPrefixGroupsRetainDuplicatesAndUnsupportedStops(t *testing.T) {
	b := ownedTestProperty(123, 0xc9ef071f, 4, 43)
	b = append(b, clockTestInherited(0xc9ef071f, 4, 44)...)
	b = append(b, 0x22, 1, 2, 3, 4, 3, 1, 2, 3)
	b = append(b, clockTestInherited(0x6c463718, 4, 43983)...)
	r := InspectClockPrefixGroupsBuffer(b)
	if len(r.Groups) != 1 || len(r.Groups[0].Coarse) != 2 || len(r.Groups[0].Fine) != 0 || r.Groups[0].StopReason != "unsupported_field_width" {
		t.Fatal("duplicates/unknowns repaired")
	}
}
