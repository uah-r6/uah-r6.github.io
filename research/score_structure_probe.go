// Research observer: score serialization records and actual replay clock ticks.
package main

import (
	"encoding/binary"
	"encoding/json"
	"os"
	"reflect"
	"sort"

	"github.com/lumina-r6/siege-dissect/dissect"
	"github.com/rs/zerolog"
)

func main() {
	zerolog.SetGlobalLevel(zerolog.Disabled)
	results := make([]map[string]interface{}, 0)
	for _, path := range os.Args[1:] {
		f, err := os.Open(path)
		if err != nil {
			panic(err)
		}
		r, err := dissect.NewReader(f)
		f.Close()
		if err != nil {
			panic(err)
		}
		rows := make(map[int]map[string]interface{})
		for _, spec := range []struct {
			tag  []byte
			name string
		}{
			{[]byte{0x1F, 0x07, 0xEF, 0xC9}, "clock"},
			{[]byte{0xEC, 0xDA, 0x4F, 0x80}, "score"},
			{[]byte{0x1C, 0xD2, 0xB1, 0x9D}, "kills"},
			{[]byte{0x4D, 0x73, 0x7F, 0x9E}, "assists"},
		} {
			spec := spec
			r.Listen(spec.tag, func(reader *dissect.Reader) error {
				v := reflect.ValueOf(reader).Elem()
				at := int(v.FieldByName("offset").Int())
				data := v.FieldByName("b").Bytes()
				if spec.name == "clock" {
					if at+5 <= len(data) && data[at] == 4 {
						rows[at-4] = map[string]interface{}{"offset": at - 4, "kind": "clock", "value": binary.LittleEndian.Uint32(data[at+1 : at+5])}
					}
					return nil
				}
				if at < 13 || at+5 > len(data) || data[at-13] != 0x23 || data[at] != 4 {
					return nil
				}
				for i := at - 8; i < at-4; i++ {
					if data[i] != 0 {
						return nil
					}
				}
				rows[at-4] = map[string]interface{}{"offset": at - 4, "kind": spec.name,
					"entity":       binary.LittleEndian.Uint32(data[at-12 : at-8]),
					"record_start": at - 13, "record_end": at + 5,
					"value": binary.LittleEndian.Uint32(data[at+1 : at+5])}
				return nil
			})
		}
		if err = r.Read(); !dissect.Ok(err) {
			panic(err)
		}
		offsets := make([]int, 0, len(rows))
		for offset := range rows {
			offsets = append(offsets, offset)
		}
		sort.Ints(offsets)
		ordered := make([]map[string]interface{}, 0, len(rows))
		for _, offset := range offsets {
			ordered = append(ordered, rows[offset])
		}
		results = append(results, map[string]interface{}{"file": path, "header": r.Header,
			"fields": ordered, "feedback": r.MatchFeedback})
	}
	if err := json.NewEncoder(os.Stdout).Encode(results); err != nil {
		panic(err)
	}
}
