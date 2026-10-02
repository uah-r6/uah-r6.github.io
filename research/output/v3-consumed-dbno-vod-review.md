# Independent current Y11 DBNO credit / finisher review

Consumed SAL official8580/TLAW-INTZ Lair physicalR06. The official broadcast confirms that displayed finisher and credited-kill owner differ. The replay feedback correctly records the displayed finisher in this case. The current tracker counts these feed finishes as kills; those counts can differ from official credited kills. No normalized event, statistic, Rating feature, model or historical data is changed.

## Independent visual evidence

[Official Rainbow Six Esports SAL Stage2 Day1 broadcast](https://www.youtube.com/watch?v=Ao6SRRhCmbg&t=3484s), uploaded20260905. Exact cached frames and SHA256 provenance remain ignored.

| Broadcast seconds | Observed UI |
| ---: | --- |
| 3484 | R06, score4-1, clock1:03. Stk INTZ has the DBNO cross on his observer card. Kheyze has5kills/3deaths/5assists; Maia6/3/0. |
| 3485 | Clock1:02. Stk cross remains visible; observer main perspective is Ar7hr. Kheyze5/3/5, Maia6/3/0. |
| 3486 | Clock1:01. Feed displays AngelzZ INTZ eliminates Kheyze TLAW. Kheyze card becomes5/4/5; Stk still DBNO. Maia6/3/0. |
| 3487 | Clock1:00. Stk card transitions to dead. Kheyze card now6/4/5 while already dead; Maia remains6/3/0 at this sampled instant. |
| 3488 | Clock0:59. Feed displays Maia TLAW eliminates Stk INTZ. Maia card6/3/1: killsunchanged, assistincreases. Kheyze card6/4/5. |
| 3500 | Clock0:47. Maia6/3/1, Kheyze6/4/5, Stk1/6/0 confirm persistent scoreboard values. |

Stk is visibly DBNO before elimination. Maia appears as his finisher in the feed, but Maia gains an assist and no kill; Kheyze gains the kill while already dead. This demonstrates the credit/finisher split in current Y11. The particular downing shot is not visible in the sampled frames; the stronger claim that the camera directly shows Kheyze downing Stk is not made. One independently reviewed case does not visually adjudicate all43 map-count differences.

## Replay evidence retained separately

Physical replay SHA256 `82f47f7ef95348fd2619c6f1a26bf0f853dc45cf925c39cf6110f2475cc58125`. Existing parser feed event at 74276292, clock1:00: Maia.TLAW -> Stk.INTZ. Direct declared scoreboard UID routes give Kheyze numericUID394888978586195443 kill delta1, feed finishes0; Maia numericUID5569963436246234840 kill delta0, feed finishes1. Counter ownership is established without public labels or matching a desired kill total. The separate full-map counter audit records exact raw offsets, owner/component references, initial/terminal counters and between-round continuity.

## Methodology consequence

Map-level exact K/D matching does not establish every round-level credited kill: Kheyze has one positive and one negative credit/finisher difference in R06/R13, canceling at map level. This limits the current research quality gate and can affect round-level multikill/KOST/opening inputs. The magnitude of those effects is not measured here; no per-victim credited event is guessed or reassigned.

Historical [Ubisoft DBNO notes, August18,2021](https://www.ubisoft.com/en-us/game/rainbow-six/siege/news-updates/1YPQ5yw9TaRhQwghjStqn2) document a downing player receiving the kill credit while a teammate finisher is shown in the feed. The current broadcast independently corroborates the distinction rather than relying solely on historical notes.

A future credited-kill study needs explicit stable UID counter ownership plus victim/event association and DBNO/revive/rehost evidence. Preserve finisher identity and death timing. Do not rewrite killer names from the last scoreboard update or use aggregate totals to choose identities. This is a data-definition limitation and a research next step, not an approved runtime correction.

Permanent failed SAL result SHA256 `73b17d45f73cc7f07da5fc996bd9e1379017120d451e67c5e145ad1c1b9cbaa2` and all86 protected live hashes unchanged. No final refit, gate relaxation, import, public regeneration, push or publishing.
