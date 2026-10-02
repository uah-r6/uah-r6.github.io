// Research only: explicit component declarations and health/UID properties.
package main

import (
	"bytes"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"os"
	"sort"

	"github.com/lumina-r6/siege-dissect/dissect"
	"github.com/rs/zerolog"
)

func componentProperties(data []byte, healthEntities map[uint32]bool) map[int]map[string]interface{} {
	properties := make(map[int]map[string]interface{})
	for start := 0; start+14 <= len(data); start++ {
		if data[start] != 0x23 || !bytes.Equal(data[start+5:start+9], []byte{0, 0, 0, 0}) {
			continue
		}
		entity := binary.LittleEndian.Uint32(data[start+1 : start+5])
		for at := start + 9; at+5 <= len(data); {
			size := int(data[at+4])
			if size != 1 && size != 2 && size != 4 && size != 8 {
				break
			}
			end := at + 5 + size
			if end > len(data) {
				break
			}
			tag := hex.EncodeToString(data[at : at+4])
			kind := "component_state"
			if tag == "252676c9" && size == 4 {
				kind = "health"
			}
			if tag == "eed445c8" && size == 8 {
				kind = "numeric_uid"
			}
			if kind != "component_state" || healthEntities[entity] {
				var value uint64
				for i := 0; i < size; i++ {
					value |= uint64(data[at+5+i]) << (8 * i)
				}
				properties[at] = map[string]interface{}{"offset": at, "kind": kind, "entity": entity,
					"value": value, "hash": tag, "size": size, "record_start": start, "inherited": at != start+9}
			}
			if end >= len(data) || data[end] != 0x22 {
				break
			}
			at = end + 1
		}
	}
	return properties
}

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
		var raw bytes.Buffer
		if _, err := r.Write(&raw); err != nil {
			panic(err)
		}
		data := raw.Bytes()
		declarations := make([]map[string]interface{}, 0)
		healthEntities := make(map[uint32]bool)
		for i := 0; i+25 <= len(data); i++ {
			if data[i] != 0x1b || !bytes.Equal(data[i+5:i+9], []byte{0, 0, 0, 0}) || !bytes.Equal(data[i+17:i+21], []byte{0, 0, 0, 0}) {
				continue
			}
			declarations = append(declarations, map[string]interface{}{"offset": i,
				"owner":      binary.LittleEndian.Uint32(data[i+1 : i+5]),
				"slot_hash":  hex.EncodeToString(data[i+9 : i+13]),
				"component":  binary.LittleEndian.Uint32(data[i+13 : i+17]),
				"class_hash": hex.EncodeToString(data[i+21 : i+25])})
			if hex.EncodeToString(data[i+9:i+13]) == "4154dcc4" && hex.EncodeToString(data[i+21:i+25]) == "0c98c63f" {
				healthEntities[binary.LittleEndian.Uint32(data[i+13:i+17])] = true
			}
		}
		properties := componentProperties(data, healthEntities)
		if err = r.Read(); !dissect.Ok(err) {
			panic(err)
		}
		offsets := make([]int, 0, len(properties))
		for offset := range properties {
			offsets = append(offsets, offset)
		}
		sort.Ints(offsets)
		ordered := make([]map[string]interface{}, 0, len(properties))
		for _, offset := range offsets {
			ordered = append(ordered, properties[offset])
		}
		results = append(results, map[string]interface{}{"file": path, "header": r.Header,
			"declarations": declarations, "properties": ordered, "feedback": r.MatchFeedback})
	}
	if err := json.NewEncoder(os.Stdout).Encode(results); err != nil {
		panic(err)
	}
}
