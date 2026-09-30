package dissect

import (
	"bytes"
	"strconv"
	"testing"
)

func TestY11HeaderRetainsLastPlayerBeforeTeamScore(t *testing.T) {
	var data bytes.Buffer
	write := func(key, value string) {
		data.WriteByte(byte(len(key)))
		data.Write(make([]byte, 7))
		data.WriteString(key)
		data.WriteByte(byte(len(value)))
		data.Write(make([]byte, 7))
		data.WriteString(value)
	}
	for _, row := range [][2]string{
		{"version", "Y11S3_Alpha04"}, {"code", strconv.Itoa(Y11S3_Alpha04)},
		{"datetime", "2026-09-23-18-15-06"}, {"matchtype", "4"},
		{"worldid", "413845419788"}, {"recordingplayerid", "1"},
		{"gamemodeid", "327933806"}, {"roundspermatch", "12"},
		{"roundspermatchovertime", "3"}, {"roundnumber", "0"},
		{"overtimeroundnumber", "0"}, {"startingteamscore0", "0"},
		{"startingteamscore1", "0"}, {"teamname0", "A"}, {"teamname1", "B"},
		{"playerid", "1"}, {"playername", "First"}, {"team", "0"},
		{"rolename", "ZOFIA"},
		{"playerid", "2"}, {"playername", "Last"}, {"team", "0"},
		{"roleimage", "409899350111"}, {"rolename", "STRIKER"},
		{"roleportrait", "409899350418"},
		{"teamscore0", "1"}, {"teamscore1", "0"},
	} {
		write(row[0], row[1])
	}
	data.WriteByte(0) // Reader.Bytes requires a byte after the final value.
	r := &Reader{b: data.Bytes()}
	h, err := r.readHeader()
	if err != nil {
		t.Fatal(err)
	}
	if len(h.Players) != 2 || h.Players[1].Username != "Last" ||
		h.Players[1].RoleName != "STRIKER" ||
		h.Players[1].RoleImage != 409899350111 {
		t.Fatalf("last player metadata was dropped: %+v", h.Players)
	}
}
