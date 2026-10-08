package dissect

// Completing-owner attribution uses typed component ownership, never the
// legacy timer's default player index, scoreboard bonuses or nearest IDs.
import (
	"bytes"
	"encoding/binary"
	"math"
	"sort"
	"strconv"
)

const (
	objectiveUIDTag       uint32 = 0xc845d4ee
	objectiveTimerSlot    uint32 = 0xca8dc027
	objectiveTimerClass   uint32 = 0xf36b21b2
	objectiveVariantClass uint32 = 0xffff59a8 // exactly observed build9734089
	objectiveBodySlot     uint32 = 0xc4dc5441
	objectiveBodyClass    uint32 = 0x3fc6980c
	objectiveBodyState    uint32 = 0xa5f688e7
	objectiveTimerTag     uint32 = 0xd958c8a9
	objectivePhaseTag     uint32 = 0xe9068ce5
	objectiveProgressTag  uint32 = 0xeb7fa3e9
	objectiveNameTag      uint32 = 0x2847e85b
)

type objectiveDeclaration struct {
	offset                        int
	owner, slot, component, class uint32
}
type objectiveProperty struct {
	offset, record, end, size int
	entity, tag               uint32
	bits                      uint64
	text                      string
}
type objectiveRoute struct {
	owner, slot, class  uint32
	declaration, player int
}
type objectiveSample struct {
	offset  int
	seconds float64
}
type objectiveEpisode struct {
	entity                     uint32
	route                      objectiveRoute
	phase, start, end, lastEnd int
	terminal                   string
	samples                    []objectiveSample
}
type objectiveEvidence struct {
	declarations []objectiveDeclaration
	properties   []objectiveProperty
	owners       map[uint32]int
	episodes     []objectiveEpisode
	orphans      []int
}

func objectiveTimerClassForBuild(build int) uint32 {
	if build == 9734089 {
		return objectiveVariantClass
	}
	return objectiveTimerClass
}

func objectiveComponentFields(data []byte) ([]objectiveDeclaration, []objectiveProperty) {
	declarations := []objectiveDeclaration{}
	for at := 0; at+25 <= len(data); at++ {
		if data[at] != 0x1b || binary.LittleEndian.Uint32(data[at+5:at+9]) != 0 || binary.LittleEndian.Uint32(data[at+17:at+21]) != 0 {
			continue
		}
		declarations = append(declarations, objectiveDeclaration{at, binary.LittleEndian.Uint32(data[at+1 : at+5]), binary.LittleEndian.Uint32(data[at+9 : at+13]), binary.LittleEndian.Uint32(data[at+13 : at+17]), binary.LittleEndian.Uint32(data[at+21 : at+25])})
	}
	fields := map[int]objectiveProperty{}
	for cursor := 0; cursor < len(data); {
		rel := bytes.IndexByte(data[cursor:], 0x23)
		if rel < 0 {
			break
		}
		start := cursor + rel
		cursor = start + 1
		if start+14 > len(data) || binary.LittleEndian.Uint32(data[start+5:start+9]) != 0 {
			continue
		}
		entity := binary.LittleEndian.Uint32(data[start+1 : start+5])
		for at := start + 9; at+5 <= len(data); {
			tag := binary.LittleEndian.Uint32(data[at : at+4])
			size := int(data[at+4])
			end := at + 5 + size
			isText := tag == objectiveTimerTag || tag == objectiveNameTag
			if end > len(data) || (size != 1 && size != 2 && size != 4 && size != 8 && !(isText && size <= 64)) {
				break
			}
			p := objectiveProperty{offset: at, record: start, end: end, size: size, entity: entity, tag: tag}
			if isText {
				p.text = string(data[at+5 : end])
			} else {
				for i := 0; i < size; i++ {
					p.bits |= uint64(data[at+5+i]) << uint(8*i)
				}
			}
			if tag == objectiveUIDTag || tag == objectiveBodyState || tag == objectiveTimerTag || tag == objectivePhaseTag || tag == objectiveProgressTag {
				fields[at] = p
			}
			if end >= len(data) || data[end] != 0x22 {
				break
			}
			at = end + 1
		}
	}
	properties := make([]objectiveProperty, 0, len(fields))
	for _, p := range fields {
		properties = append(properties, p)
	}
	sort.Slice(properties, func(i, j int) bool { return properties[i].offset < properties[j].offset })
	return declarations, properties
}

func objectiveOwners(players []Player, fields []objectiveProperty) map[uint32]int {
	names := map[uint64]int{}
	for i, p := range players {
		if p.ID != 0 {
			names[p.ID] = i
		}
	}
	values := map[uint32]map[uint64]bool{}
	for _, p := range fields {
		if p.tag != objectiveUIDTag || p.size != 8 {
			continue
		}
		if values[p.entity] == nil {
			values[p.entity] = map[uint64]bool{}
		}
		values[p.entity][p.bits] = true
	}
	owners := map[uint32]int{}
	counts := map[int]int{}
	for entity, vs := range values {
		if len(vs) != 1 {
			continue
		}
		for uid := range vs {
			if player, ok := names[uid]; ok {
				owners[entity] = player
				counts[player]++
			}
		}
	}
	for entity, player := range owners {
		if counts[player] != 1 {
			delete(owners, entity)
		}
	}
	return owners
}

func (e *objectiveEvidence) binding(entity uint32, offset int) (objectiveRoute, bool) {
	routes := []objectiveRoute{}
	if player, ok := e.owners[entity]; ok {
		routes = append(routes, objectiveRoute{owner: entity, player: player})
	}
	type key struct{ owner, slot uint32 }
	latest := map[key]objectiveDeclaration{}
	for _, d := range e.declarations {
		if d.offset > offset {
			break
		}
		latest[key{d.owner, d.slot}] = d
	}
	for _, d := range latest {
		if d.component == entity && d.component != 0 && d.class != 0 {
			player, ok := e.owners[d.owner]
			if !ok {
				player = -1
			}
			routes = append(routes, objectiveRoute{d.owner, d.slot, d.class, d.offset, player})
		}
	}
	if len(routes) != 1 || routes[0].player < 0 {
		return objectiveRoute{}, false
	}
	return routes[0], true
}

func (e *objectiveEvidence) splitEpisodes(build int) {
	type key struct {
		record int
		entity uint32
	}
	records := map[key][]objectiveProperty{}
	for _, p := range e.properties {
		if p.tag == objectivePhaseTag || p.tag == objectiveProgressTag || p.tag == objectiveTimerTag {
			records[key{p.record, p.entity}] = append(records[key{p.record, p.entity}], p)
		}
	}
	keys := make([]key, 0, len(records))
	for k := range records {
		keys = append(keys, k)
	}
	sort.Slice(keys, func(i, j int) bool {
		if keys[i].record == keys[j].record {
			return keys[i].entity < keys[j].entity
		}
		return keys[i].record < keys[j].record
	})
	active := map[uint32]*objectiveEpisode{}
	// A replay can redeclare the same timer component and repeat its already
	// closed state-2 snapshot. It is not a new interaction. Retain the exact
	// terminal fields only while the unique typed ownership stays continuous.
	type terminalSnapshot struct {
		route  objectiveRoute
		fields []objectiveProperty
	}
	closed := map[uint32]terminalSnapshot{}
	sameOwner := func(a, b objectiveRoute) bool {
		return a.owner == b.owner && a.player == b.player && a.slot == b.slot && a.class == b.class
	}
	sameFields := func(a, b []objectiveProperty) bool {
		if len(a) != len(b) {
			return false
		}
		for i := range a {
			if a[i].tag != b[i].tag || a[i].size != b[i].size || a[i].bits != b[i].bits || a[i].text != b[i].text {
				return false
			}
		}
		return true
	}
	closeEpisode := func(entity uint32, reason string, end int) {
		ep := active[entity]
		if reason != "ownership_declaration_boundary" && reason != "explicit_state_2" {
			end = ep.lastEnd
		}
		ep.terminal = reason
		ep.end = end
		e.episodes = append(e.episodes, *ep)
		delete(active, entity)
	}
	declIndex := 0
	declarationBoundary := func(offset int) {
		for entity, snapshot := range closed {
			route, ok := e.binding(entity, offset)
			if !ok || !sameOwner(route, snapshot.route) {
				delete(closed, entity)
			}
		}
		for entity, ep := range active {
			route, ok := e.binding(entity, offset)
			if !ok || route != ep.route {
				closeEpisode(entity, "ownership_declaration_boundary", offset)
			}
		}
	}
	for _, k := range keys {
		for declIndex < len(e.declarations) && e.declarations[declIndex].offset < k.record {
			declarationBoundary(e.declarations[declIndex].offset)
			declIndex++
		}
		ps := records[k]
		sort.Slice(ps, func(i, j int) bool { return ps[i].offset < ps[j].offset })
		route, ok := e.binding(k.entity, ps[0].offset)
		valid := ok && route.slot == objectiveTimerSlot && route.class == objectiveTimerClassForBuild(build)
		phaseCount, phase, width := 0, -1, 0
		hasTimer := false
		for _, p := range ps {
			link, bound := e.binding(k.entity, p.offset)
			if !bound || link != route {
				valid = false
			}
			if p.tag == objectivePhaseTag {
				phaseCount++
				phase = int(p.bits)
				width = p.size
			}
			if p.tag == objectiveTimerTag && p.text != "" {
				hasTimer = true
			}
		}
		if !valid {
			delete(closed, k.entity)
			if active[k.entity] != nil {
				closeEpisode(k.entity, "ownership_missing_or_changed", ps[len(ps)-1].end)
			}
			if hasTimer {
				e.orphans = append(e.orphans, k.record)
			}
			continue
		}
		if ep := active[k.entity]; ep != nil && ep.route != route {
			closeEpisode(k.entity, "ownership_changed", ps[len(ps)-1].end)
		}
		if phaseCount > 1 || (phaseCount == 1 && width != 4) {
			delete(closed, k.entity)
			if active[k.entity] != nil {
				closeEpisode(k.entity, "unsupported_state", ps[len(ps)-1].end)
			}
			e.orphans = append(e.orphans, k.record)
			continue
		}
		if phase == 0 || phase == 1 {
			delete(closed, k.entity)
			if active[k.entity] != nil {
				closeEpisode(k.entity, "explicit_restart", ps[len(ps)-1].end)
			}
			active[k.entity] = &objectiveEpisode{entity: k.entity, route: route, phase: phase, start: k.record}
		}
		if ep := active[k.entity]; ep != nil {
			ep.lastEnd = ps[len(ps)-1].end
			for _, p := range ps {
				if p.tag == objectiveTimerTag && p.text != "" {
					number, err := strconv.ParseFloat(p.text, 64)
					if err != nil {
						number = math.NaN()
					}
					ep.samples = append(ep.samples, objectiveSample{p.offset, number})
				}
			}
			if phase == 2 {
				closeEpisode(k.entity, "explicit_state_2", ps[len(ps)-1].end)
				closed[k.entity] = terminalSnapshot{route: route, fields: ps}
			} else if phaseCount > 0 && phase != 0 && phase != 1 {
				delete(closed, k.entity)
				closeEpisode(k.entity, "unknown_state", ps[len(ps)-1].end)
			}
		} else {
			if snapshot, exists := closed[k.entity]; exists && phaseCount == 1 && phase == 2 &&
				sameOwner(route, snapshot.route) && sameFields(ps, snapshot.fields) {
				continue
			}
			delete(closed, k.entity)
			if hasTimer {
				e.orphans = append(e.orphans, k.record)
			}
		}
	}
	for declIndex < len(e.declarations) {
		declarationBoundary(e.declarations[declIndex].offset)
		declIndex++
	}
	for entity := range active {
		closeEpisode(entity, "round_ended_without_explicit_terminal", 0)
	}
	sort.Slice(e.episodes, func(i, j int) bool { return e.episodes[i].start < e.episodes[j].start })
}

func (e *objectiveEvidence) complete(ep objectiveEpisode, phase int) bool {
	if ep.phase != phase || len(ep.samples) < 2 {
		return false
	}
	previous := math.Inf(1)
	for _, s := range ep.samples {
		if math.IsNaN(s.seconds) || math.IsInf(s.seconds, 0) || s.seconds > previous {
			return false
		}
		previous = s.seconds
	}
	first, last := ep.samples[0].seconds, ep.samples[len(ep.samples)-1].seconds
	if first < 6.5 || first > 7.1 || last < 0 || last > .1 {
		return false
	}
	if ep.terminal == "explicit_state_2" {
		return true
	}
	if phase != 1 || ep.terminal != "ownership_declaration_boundary" {
		return false
	}
	count := 0
	clear := false
	for _, d := range e.declarations {
		if d.owner == ep.route.owner && d.slot == ep.route.slot && d.offset == ep.end {
			count++
			clear = d.component == 0 && d.class == 0
		}
	}
	return count == 1 && clear
}

func (e *objectiveEvidence) activeBody(ep objectiveEpisode) bool {
	var body objectiveDeclaration
	found := false
	for _, d := range e.declarations {
		if d.offset > ep.start {
			break
		}
		if d.owner == ep.route.owner && d.slot == objectiveBodySlot {
			body = d
			found = true
		}
	}
	if !found || body.component == 0 || body.class != objectiveBodyClass {
		return false
	}
	points := map[int]bool{ep.start: true, ep.end: true}
	var previous *objectiveProperty
	for i := range e.properties {
		p := &e.properties[i]
		if p.entity != body.component || p.tag != objectiveBodyState || p.size != 4 {
			continue
		}
		if p.offset <= ep.start {
			previous = p
		} else if p.offset <= ep.end {
			if p.bits != 0 && p.bits != 2 {
				return false
			}
			points[p.offset] = true
		}
	}
	if previous == nil || (previous.bits != 0 && previous.bits != 2) {
		return false
	}
	points[previous.offset] = true
	for _, d := range e.declarations {
		if d.offset > ep.start && d.offset <= ep.end && (d.component == 0 || d.component == body.component || (d.owner == body.owner && d.slot == body.slot)) {
			points[d.offset] = true
		}
	}
	for point := range points {
		route, ok := e.binding(body.component, point)
		if !ok || route.owner != ep.route.owner || route.player != ep.route.player || route.slot != objectiveBodySlot || route.class != objectiveBodyClass {
			return false
		}
	}
	return true
}

func objectiveRosterValid(h Header) bool {
	if h.GameMode != Bomb || len(h.Players) != 10 || h.Teams[0].Role == h.Teams[1].Role ||
		(h.Teams[0].Role != Attack && h.Teams[0].Role != Defense) || (h.Teams[1].Role != Attack && h.Teams[1].Role != Defense) {
		return false
	}
	names := map[string]bool{}
	uids := map[uint64]bool{}
	counts := [2]int{}
	for _, p := range h.Players {
		if p.ID == 0 || p.Username == "" || names[p.Username] || uids[p.ID] || p.TeamIndex < 0 || p.TeamIndex > 1 {
			return false
		}
		names[p.Username] = true
		uids[p.ID] = true
		counts[p.TeamIndex]++
	}
	return counts == [2]int{5, 5}
}

func (e *objectiveEvidence) selectActor(h Header, feedback []MatchUpdate, occurrence ObjectiveOccurrence) (int, string) {
	if !objectiveRosterValid(h) {
		return -1, "incomplete_unique_roster_or_roles"
	}
	for _, f := range feedback {
		if f.Type == PlayerLeave {
			return -1, "player_leave_timing_unknown"
		}
		if (f.Type == Kill || f.Type == Death) && f.killOffset <= 0 {
			return -1, "unknown_death_offset"
		}
	}
	anchor := int(occurrence.PlantStateOffset)
	if anchor <= 0 {
		return -1, "missing_verified_plant_anchor"
	}
	phase := 0
	role := Attack
	if occurrence.Kind == "disable" {
		phase = 1
		role = Defense
		if len(h.ObjectiveOccurrences) != 2 || h.ObjectiveOccurrences[0].Kind != "plant" ||
			h.ObjectiveOccurrences[0].Source != "defuser_state_v1" || occurrence.Source != "defuser_state_and_defense_win_v1" ||
			h.ObjectiveOccurrences[0].PlantStateOffset != occurrence.PlantStateOffset {
			return -1, "no_verified_plant_and_disable_occurrence"
		}
	} else if occurrence.Kind != "plant" || occurrence.Source != "defuser_state_v1" {
		return -1, "unsupported_objective"
	}
	runs := []objectiveEpisode{}
	completed := []objectiveEpisode{}
	for _, ep := range e.episodes {
		if ep.phase != phase || (phase == 0 && ep.start >= anchor) || (phase == 1 && ep.start <= anchor) {
			continue
		}
		runs = append(runs, ep)
		if e.complete(ep, phase) && (phase == 1 || ep.end < anchor) {
			completed = append(completed, ep)
		}
	}
	if len(completed) != 1 {
		return -1, "missing_or_competing_complete_runs"
	}
	ep := completed[0]
	if ep.end <= ep.start || ep.end < ep.samples[len(ep.samples)-1].offset {
		return -1, "invalid_terminal_order"
	}
	for _, other := range runs {
		if other.start > ep.start {
			return -1, "later_interaction_attempt"
		}
		if phase == 0 && other.start < ep.start && (other.end == 0 || other.end > ep.start) {
			return -1, "overlapping_plant_attempts"
		}
	}
	for _, offset := range e.orphans {
		if (phase == 0 && offset < anchor) || (phase == 1 && offset > anchor) {
			return -1, "unbound_timer_evidence"
		}
	}
	player := ep.route.player
	if player < 0 || player >= len(h.Players) || h.Teams[h.Players[player].TeamIndex].Role != role {
		return -1, "timer_owner_identity_or_role_conflict"
	}
	if ep.route.slot != objectiveTimerSlot || ep.route.class != objectiveTimerClassForBuild(h.CodeVersion) {
		return -1, "unsupported_timer_component_route"
	}
	// Frozen disable rule did not promote the class variant.
	if phase == 1 && ep.route.class != objectiveTimerClass {
		return -1, "unsupported_disable_timer_component_route"
	}
	dead := map[string]bool{}
	for _, f := range feedback {
		if f.killOffset > ep.end {
			continue
		}
		if f.Type == Kill {
			dead[f.Target] = true
		} else if f.Type == Death {
			dead[f.Username] = true
		}
	}
	if dead[h.Players[player].Username] {
		return -1, "timer_owner_dead_by_terminal"
	}
	if phase == 0 {
		allDead := true
		for _, p := range h.Players {
			if p.TeamIndex != h.Players[player].TeamIndex && !dead[p.Username] {
				allDead = false
			}
		}
		if allDead {
			return -1, "all_opponents_dead_by_terminal"
		}
	}
	if !e.activeBody(ep) {
		return -1, "timer_owner_body_unresolved"
	}
	return player, "completing_timer_owner_v1"
}

func (r *Reader) resolveObjectiveActors() {
	if len(r.Header.ObjectiveOccurrences) == 0 {
		return
	}
	declarations, properties := objectiveComponentFields(r.b)
	e := objectiveEvidence{declarations: declarations, properties: properties, owners: objectiveOwners(r.Header.Players, properties)}
	// Match the validated observer's entity scope: declared player components,
	// including their unknown-owner sharing, never arbitrary unrelated fields.
	entities := map[uint32]bool{}
	for entity := range e.owners {
		entities[entity] = true
	}
	for _, d := range declarations {
		if _, known := e.owners[d.owner]; known && d.component != 0 {
			entities[d.component] = true
		}
	}
	filtered := []objectiveProperty{}
	for _, p := range e.properties {
		if p.tag == objectiveUIDTag || p.tag == objectiveBodyState || entities[p.entity] {
			filtered = append(filtered, p)
		}
	}
	e.properties = filtered
	e.splitEpisodes(r.Header.CodeVersion)
	for i := range r.Header.ObjectiveOccurrences {
		o := &r.Header.ObjectiveOccurrences[i]
		player, reason := e.selectActor(r.Header, r.MatchFeedback, *o)
		o.ActorReason = reason
		if player >= 0 {
			name := r.Header.Players[player].Username
			o.Actor = &name
			o.ActorID = r.Header.Players[player].ID
			o.ActorSource = "completing_timer_owner_v1"
		}
	}
}
