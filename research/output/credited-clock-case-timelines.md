# Clock-annotated split and missing-history cases — 2026-10-03

Base `016e51e`. Ten fixed consumed cases reuse the owned-prefix selection: reviewed Stk/resetz credit splits and all eight body targets missing kind5 history. The initial harness failed before producing a result because counter identity uses `uid` rather than header `id`; its reservation, exact source and failure are preserved privately. Separately reserved v2 checks exact UID/profile/name/team equality. No causal hypothesis was changed to repair this interface error.

## Reviewed split-credit serialization

These are clock brackets around independently typed live samples, not shot/credit occurrence timestamps. Late history copies remain separate; no copy is treated as a live timestamp.

| Stk/Kheyze/Maia sample | Offset | Raw finer countdown bracket |
| --- | ---: | --- |
| Stk body raw3 |74255864 |64738–64772 |
| Kheyze body raw4 |74268967 |61979–62012 |
| AngelzZ→Kheyze original final feed |74269360 |61911–61979 |
| Kheyze counter +1 |74275879 |60375–60408 |
| Stk body raw4 |74275897 |60375–60408 |
| Maia→Stk original final feed |74276292 |60341–60375 |

The counter observation is serialized after the reviewed target raw3 and after Kheyze's own final death, then18bytes before Stk's raw4. This preserves the known split-credit case without moving Kheyze's kill to the damaging shot or inventing a counter-victim field. A counter increment itself carries no victim. See the earlier independently reviewed credited-kill case studies; first history reference's universal downer role remains unproven.

| resetz/Neskin/pino sample | Offset | Raw finer countdown bracket |
| --- | ---: | --- |
| resetz body raw3 |86443440 |33563–33597 |
| Neskin counter +1 |86448083 |32708–32742 |
| resetz body raw4 |86448101 |32708–32742 |
| pino→resetz first final feed |86448473 |32674–32708 |

The [prior independent official HUD review](credited-kill-opening-owner.md) showed Neskin kills0→1, pino kill unchanged/assist+1, and resetz first final death. That supports this particular credited owner independently of proximity. The live counter appears18bytes before body raw4 and390bytes before the original finish field. The damaging shot/downer was not independently observed. The finer replay field is not synchronized to broadcast subsecond time; do not call these brackets an exact official opening timestamp.

## Body raw3→raw4 spans

Bounds below are mathematical differences of positive same-region raw countdown brackets. The observed scale is1000raw units per integer countdown second. `elapsed_seconds` remains null; no interpolation, exact shot duration or generic DBNO meaning is claimed.

| Source/target | Raw countdown difference bounds | Limitation |
| --- | --- | --- |
| SAL8580R06 Stk |4330–4397 |Reviewed target state, first causal actor role unpromoted |
| SAL8583R02 resetz |821–889 |Reviewed target state, damaging shot not observed |
| APAC8156R10 Jin |Unresolved |Raw3 zero/terminal bracket; later raw4 missing side |
| APAC8161R14 Aokayu |1522–1589 |No kind5 target; no damage-source ID |
| SAL8593R01 Mr6otlaw |Unresolved |Later raw4 zero/terminal bracket |
| SAL8594R01 soulz1 |Unresolved |Zero/terminal and missing side |
| SAL8595R08 stemp |0–67 |Overlapping serialized clock brackets; no kind5 target |
| SAL8596segment2R01 VolpsZ |Unresolved |Zero/terminal and missing side |
| SAL8596segment2R05 xSexyCake |298–397 |No kind5 target, causal semantics unknown |
| SAL8598R01 vitaking |Unresolved |Zero/terminal and missing side |

The earlier short byte-span observations cannot be converted to time. These explicit clock brackets expose which cases can be compared numerically and which cannot. Raw3 is not promoted to a universal down event.

## Aokayu/Nina/OSAdinho gap

The preserved APAC8161R14 live order is:

- Kawa raw4 at63935515, raw clock37023–37057.
- OSAdinho counter+1 at63935611, same raw bracket; OSAdinho→Kawa finish63935980.
- Aokayu raw3 at63940904,35597–35631.
- Aokayu raw4 at63946483,34042–34075.
- Nina counter+1 at63946588,34042–34075.
- OSAdinho→Aokayu finish63947087,34008–34042.

This is an exact serialized timeline with independently bound UIDs. It is **not** a credited-victim join. Neither adjacency nor a compensating Nina/OSAdinho count assigns a causal source to Aokayu. Full history still lacks a kind5 target Aokayu; owned prefixes still lack an incoming attacker identifier. Header Denari is context, not proof of a gadget cause. The frozen broad reconstruction mismatch remains unchanged.

## Next action

Three focused Python tests cover interval uncertainty, reset/zero/missing/reversed order refusals, and counter/header identity mismatch. Runtime/Go/shared statistics/export/web paths remain unchanged after the previous full Go/vet verification. The next step is a same-region finisher-refrag raw-window audit, followed by direct source/recovery evidence. No historical kill migration, Rating study or publication.
