# Current Y11 credited-kill increment timing — consumed Stk case

The [official SAL broadcast review](v3-consumed-dbno-vod-review.md) independently shows Stk downed, Kheyze dead before gaining the kill, and Maia finishing Stk while gaining an assist. This packet chronology uses that previously reviewed case; it does not infer a credited victim from the nearest counter.

| Packet offset | Latest serialized clock (seconds) | Observation | Value |
| ---: | ---: | --- | --- |
| 37150 | 0 | Maia.TLAW assists | 0 |
| 51679 | 0 | Kheyze.TLAW kills | 5 |
| 71968 | 0 | Stk body | 2 |
| 73724750 | 1 | Stk body | 0 |
| 74254694 | 65 | Stk body | 2 |
| 74255864 | 64 | Stk body | 3 |
| 74269360 | 61 | Raw elimination | AngelzZ.INTZ -> Kheyze.TLAW |
| 74275879 | 60 | Kheyze.TLAW kills | 6 |
| 74275897 | 60 | Stk body | 4 |
| 74276004 | 60 | Maia.TLAW assists | 1 |
| 74276292 | 60 | Raw elimination | Maia.TLAW -> Stk.INTZ |
| 74454243 | 35 | Maia.TLAW assists | 2 |

Kheyze counter5->6 at74275879; Stk independently observed DBNO raw3 at74255864; eliminated raw4 at74275897; Maia finish74276292. Increment is serialized with final elimination, not at the earlier DBNO transition in this case. Packet serialization order is not server causality or subsecond clock precision. No generic credited victim/downer event mapping.

The counter retains5 until the observed update to6. That update is18bytes before the eliminated body state and413bytes before the feed finish; it is20,015bytes after the independently supported downed transition. Byte distance is not elapsed time. Coarse clock ticks annotate observations only. No direct downer ID was found in the earlier narrow owned-field probe; downer/DBNO time remains unavailable for generic runtime events.

A credited counter observation is a player/round count plus packet offset. It is not an opening, trade window start, victim mapping or simulated alive-state kill event. Production event features remain unchanged.
