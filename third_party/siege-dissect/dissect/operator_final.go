package dissect

import (
	"strings"
	"unicode"

	"github.com/rs/zerolog/log"
)

// headerOperatorName folds accents found in current replay RoleName values.
// Current header text can contain a single-byte rendering of an accent.
func headerOperatorName(name string) string {
	return strings.Map(func(c rune) rune {
		switch c {
		case 'À', 'Á', 'Â', 'Ã', 'Ä', 'Å', 'à', 'á', 'â', 'ã', 'ä', 'å':
			return 'A'
		case 'Ç', 'ç':
			return 'C'
		case 'È', 'É', 'Ê', 'Ë', 'è', 'é', 'ê', 'ë':
			return 'E'
		case 'Ì', 'Í', 'Î', 'Ï', 'ì', 'í', 'î', 'ï':
			return 'I'
		case 'Ñ', 'ñ':
			return 'N'
		case 'Ò', 'Ó', 'Ô', 'Õ', 'Ö', 'Ø', 'ò', 'ó', 'ô', 'õ', 'ö', 'ø':
			return 'O'
		case 'Ù', 'Ú', 'Û', 'Ü', 'ù', 'ú', 'û', 'ü':
			return 'U'
		}
		return unicode.ToUpper(c)
	}, strings.TrimSpace(name))
}

func (r *Reader) markUnresolvedAttackOperators() {
	for i := range r.Header.Players {
		p := &r.Header.Players[i]
		if p.TeamIndex < 0 || p.TeamIndex >= len(r.Header.Teams) ||
			r.Header.Teams[p.TeamIndex].Role != Attack {
			continue
		}
		if p.OperatorSource != "" {
			continue
		}
		p.InitialOperator = p.Operator
		p.Operator = 0
		p.OperatorSource = "unresolved"
	}
}

// The replay header's RoleName and portrait represent the final selected
// operator. readPlayer reports the initial pick; its Y11 swap identity is
// ambiguous. Only trust the header snapshot once the prep timer has reset
// to the action timer. Missing or unknown role names stay unresolved.
func (r *Reader) resolveActionStartOperators() {
	known := make(map[string]Operator, len(_Operator_map))
	for op, name := range _Operator_map {
		known[headerOperatorName(name)] = op
	}
	for i := range r.Header.Players {
		p := &r.Header.Players[i]
		if p.TeamIndex < 0 || p.TeamIndex >= len(r.Header.Teams) ||
			r.Header.Teams[p.TeamIndex].Role != Attack {
			continue
		}
		p.InitialOperator = p.Operator
		op, ok := known[headerOperatorName(p.RoleName)]
		if !ok || op.Role() != Attack || !r.prepOperatorIDs[op] {
			log.Warn().Str("player", p.Username).Str("roleName", p.RoleName).
				Msg("unresolved action-start attacker operator")
			p.Operator = 0
			p.OperatorSource = "unresolved"
			continue
		}
		p.Operator = op
		p.OperatorSource = "action_start_header"
		p.OperatorSeenBeforeAction = true
	}
}
