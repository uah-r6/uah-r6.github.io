package dissect

// Manual additions that the pinned operator generator has not picked up yet.
// The numeric ID, header RoleName and Attack side were checked in official
// Y11S1/Y11S2 replay rounds. Keep this alongside generated operator maps so
// a future generator run does not erase it before Ubisoft data is updated.
func init() {
	_operatorRoles[SolidSnake] = Attack
	_Operator_map[SolidSnake] = "Solid Snake"
}
