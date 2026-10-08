package dissect

// This proof does not promote raw state 1 to an active-body enum. It requires
// a known active body again before the SAME uniquely owned timer completes,
// plus exact, atomic, same-body numerical evidence at every intervening write.
// A completion that still has state 1 remains unsupported.
import (
	"math"
	"sort"
)

const boundedBonusSource = "terminal_active_numeric_bonus_timer_owner_v1"

func bonusBodyField(tag uint32) bool {
	return tag == 0xc9762625 || tag == 0x72a64911 || tag == 0xdad23f01 || tag == 0x7bcfad80
}

func (e *objectiveEvidence) boundedBonusBody(ep objectiveEpisode) (map[string]any, bool) {
	var body objectiveDeclaration
	for _, d := range e.declarations {
		if d.offset > ep.start {
			break
		}
		if d.owner == ep.route.owner && d.slot == objectiveBodySlot {
			body = d
		}
	}
	if body.component == 0 || body.class != objectiveBodyClass || ep.phase != 0 || !e.complete(ep, 0) {
		return nil, false
	}
	// Reuse every existing ownership/lifecycle guard, substituting ONLY the
	// state-1 observations that will separately receive a complete numeric proof.
	checked := *e
	checked.properties = append([]objectiveProperty(nil), e.properties...)
	for i := range checked.properties {
		p := &checked.properties[i]
		if p.entity == body.component && p.tag == objectiveBodyState && p.bits == 1 {
			p.bits = 0
		}
	}
	if !checked.activeBody(ep) {
		return nil, false
	}
	points := map[int]bool{ep.start: true, ep.end: true}
	for _, p := range e.properties {
		if p.entity == body.component && (p.tag == objectiveBodyState || bonusBodyField(p.tag)) && p.end > ep.start && p.end <= ep.end {
			// Complete atomic record, never a partially serialized hp/fraction pair.
			end := p.end
			for _, q := range e.properties {
				if q.entity == p.entity && q.record == p.record && q.end > end {
					end = q.end
				}
			}
			if end <= ep.end {
				points[end] = true
			}
		}
	}
	ordered := []int{}
	for point := range points {
		ordered = append(ordered, point)
	}
	sort.Ints(ordered)
	snapshots := []map[string]any{}
	bonus := false
	lastStateOffset := 0
	for _, point := range ordered {
		latest := map[uint32]objectiveProperty{}
		for _, p := range e.properties {
			if p.offset > point {
				break
			}
			if p.entity == body.component && (p.tag == objectiveBodyState || bonusBodyField(p.tag)) {
				latest[p.tag] = p
			}
		}
		state, found := latest[objectiveBodyState]
		if !found || state.size != 4 || (state.bits != 0 && state.bits != 1 && state.bits != 2) {
			return nil, false
		}
		lastStateOffset = state.offset
		row := map[string]any{"offset": point, "state": state.bits, "state_offset": state.offset}
		if state.bits == 1 {
			hp, h := latest[0xc9762625]
			base, b := latest[0x72a64911]
			ceiling, c := latest[0xdad23f01]
			fraction, f := latest[0x7bcfad80]
			if !h || !b || !c || !f || hp.size != 4 || base.size != 4 || ceiling.size != 4 || fraction.size != 4 ||
				base.bits == 0 || hp.bits <= base.bits || hp.bits > ceiling.bits || ceiling.bits-base.bits != 20 {
				return nil, false
			}
			value := float64(math.Float32frombits(uint32(fraction.bits)))
			if math.IsNaN(value) || math.IsInf(value, 0) || value <= 0 || math.Abs(value-float64(hp.bits-base.bits)/float64(base.bits)) >= 1e-6 {
				return nil, false
			}
			for _, p := range []objectiveProperty{state, hp, base, ceiling, fraction} {
				route, ok := e.binding(body.component, p.offset)
				if !ok || route.owner != ep.route.owner || route.player != ep.route.player || route.slot != objectiveBodySlot || route.class != objectiveBodyClass {
					return nil, false
				}
			}
			row["health"] = hp.bits
			row["baseline"] = base.bits
			row["ceiling"] = ceiling.bits
			row["fraction_bits"] = fraction.bits
			row["field_offsets"] = []int{hp.offset, base.offset, ceiling.offset, fraction.offset}
			bonus = true
		}
		snapshots = append(snapshots, row)
	}
	final := snapshots[len(snapshots)-1]
	if !bonus || final["state"] == uint64(1) || lastStateOffset <= ep.start || lastStateOffset >= ep.end {
		return nil, false
	}
	samples := []map[string]any{}
	for _, s := range ep.samples {
		samples = append(samples, map[string]any{"offset": s.offset, "seconds": s.seconds})
	}
	return map[string]any{"source": boundedBonusSource, "owner": ep.route.owner, "body_component": body.component,
		"body_slot": objectiveBodySlot, "body_class": objectiveBodyClass, "timer_component": ep.entity,
		"timer_slot": ep.route.slot, "timer_class": ep.route.class, "start": ep.start, "end": ep.end,
		"terminal": ep.terminal, "snapshots": snapshots, "samples": samples}, true
}
