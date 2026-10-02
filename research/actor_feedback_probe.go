// Research only: expose existing parser feedback offsets without changing the parser.
package main

import (
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
		file, err := os.Open(path)
		if err != nil {
			panic(err)
		}
		reader, err := dissect.NewReader(file)
		file.Close()
		if err != nil {
			panic(err)
		}
		timers := make(map[int]string)
		reader.Listen([]byte{0x22, 0xA9, 0xC8, 0x58, 0xD9}, func(r *dissect.Reader) error {
			offset := int(reflect.ValueOf(r).Elem().FieldByName("offset").Int()) - 5
			value, err := r.String()
			if err == nil {
				timers[offset] = value
			}
			return err
		})
		if err = reader.Read(); !dissect.Ok(err) {
			panic(err)
		}
		events := make([]map[string]interface{}, 0)
		for _, event := range reader.MatchFeedback {
			if event.Type != dissect.Kill && event.Type != dissect.Death {
				continue
			}
			// This existing internal field is read as an integer; no unsafe mutation.
			offset := reflect.ValueOf(event).FieldByName("killOffset").Int()
			events = append(events, map[string]interface{}{"feedback": event, "offset": offset})
		}
		timerOffsets := make([]int, 0, len(timers))
		for offset := range timers {
			timerOffsets = append(timerOffsets, offset)
		}
		sort.Ints(timerOffsets)
		timerRows := make([]map[string]interface{}, 0, len(timerOffsets))
		for _, offset := range timerOffsets {
			timerRows = append(timerRows, map[string]interface{}{"offset": offset, "value": timers[offset]})
		}
		results = append(results, map[string]interface{}{"file": path, "header": reader.Header, "events": events, "timers": timerRows})
	}
	if err := json.NewEncoder(os.Stdout).Encode(results); err != nil {
		panic(err)
	}
}
