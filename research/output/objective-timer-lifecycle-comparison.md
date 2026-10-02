# Consumed timer lifecycle and round teardown comparison

Explicit numeric UID ownership, complete state-record runs and literal terminal declarations. All actor fields remain null. No missing property is synthesized and no unknown state becomes dead. The cached parser win-condition string is deliberately not used as ground truth. A literal slot clear is teardown, not completion by itself.

| Match / game / round | Winner role | Global defuser state writes | Timer owner / state / last / terminal |
| --- | --- | --- | --- |
| 3173/5931/R03 | ['Defense'] | 1@87557234 | Savage / 0 / 0.001 / explicit_state_2; kds / 1 / 0.002 / ownership_declaration_boundary |
| 3173/5932/R17 | ['Defense'] | 1@75897030 | Mowwwgli / 0 / 0.001 / explicit_state_2; handyy / 1 / 0.012 / ownership_declaration_boundary |
| 3073/None/R08 | ['Defense'] | 1@59501899 | pino / 0 / 0.044 / explicit_state_2; Ape5G / 1 / 0.0 / explicit_state_2 |
| 4141/None/R06 | ['Attack'] | none | JJBlaztful.5F / 0 / 5.191 / explicit_state_2; JJBlaztful.5F / 0 / 0.018 / ownership_declaration_boundary |
| 4141/None/R14 | ['Attack'] | none | Beeno.4FUN / 0 / 3.384 / explicit_state_2; Beeno.4FUN / 0 / 6.427 / explicit_state_2; Beeno.4FUN / 0 / 6.189 / explicit_state_2; Beeno.4FUN / 0 / 0.007 / explicit_state_2 |
| 4138/None/R09 | ['Attack'] | none | Fultz.DZ / 0 / 2.965 / explicit_state_2; Nuers.DZ / 0 / 0.005 / explicit_state_2 |
| 3563/6675/R02 | ['Defense'] | 1@57656742, 0@57693663 | Rexen / 0 / 4.89 / explicit_state_2; Surf / 0 / 4.379 / explicit_state_2; Surf / 0 / 5.744 / explicit_state_2; Surf / 0 / 0.025 / explicit_state_2; njr / 1 / 0.0 / explicit_state_2 |
| 3563/6675/R10 | ['Defense'] | 1@66011334, 0@66117668 | kyno / 0 / 0.034 / explicit_state_2; Spoit / 1 / 0.004 / explicit_state_2 |

SI BankR03 kds and FortressR17 handyy have unique directly bound state1 timers reaching0.002 and0.012 respectively, followed by an explicit owner-slot clear(component0,class00000000). Neither has a terminal state2 or global defuser state0. Each has a preceding verified global plant state1 and a Defense winner. Their absence is a real serialization/lifecycle difference, not a lost scoreboard identity join. The strict observer still gives no actor proposal for either.

Older consumed3073/R08 has no global state0 but does have an explicit state2 on the disable component. Thus missing global and player-component terminal writes are separate limitations. The three negative controls have Attack winners and no global plant flag; a similar timer/clear pattern cannot establish a plant. State2 can also terminate canceled attempts.

A potential disable-by-phase hypothesis requires independently validated plant occurrence, a Defense winner, unique state1 interaction owner with correct role, coherent identity/liveness and no competing run. This is not yet a frozen actor rule: the disputed J9O/njr control and target contradictions need resolution before standalone owner credit. Existing A and all immutable results remain unchanged.

86 protected database/archive/public SHA256 values unchanged. Detailed complete ordered ledgers remain in ignored research JSON; no raw replay or dump is committed.
