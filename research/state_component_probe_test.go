package main

import (
	"encoding/hex"
	"testing"
)

func TestComponentContinuationRetainsStateWithoutCallingItDead(t *testing.T) {
	// Entity 7, health=94, followed by an inherited state=4 and boolean=1.
	b, _ := hex.DecodeString("230700000000000000252676c9045e00000022e788f6a504040000002299fc61d90101")
	rows := componentProperties(b, map[uint32]bool{7: true})
	if len(rows) != 3 {
		t.Fatalf("expected three fields, got %d", len(rows))
	}
	if rows[9]["value"] != uint64(94) || rows[19]["value"] != uint64(4) || rows[29]["value"] != uint64(1) {
		t.Fatal(rows)
	}
	if rows[19]["inherited"] != true || rows[19]["entity"] != uint32(7) {
		t.Fatal(rows[19])
	}
}

func TestTruncatedUnknownWidthIsNotAHealthState(t *testing.T) {
	b, _ := hex.DecodeString("230700000000000000252676c9045e")
	if len(componentProperties(b, map[uint32]bool{7: true})) != 0 {
		t.Fatal("truncated value accepted")
	}
}
