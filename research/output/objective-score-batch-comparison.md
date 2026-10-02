# Score packet comparison after actor validation

The 12-map actor set is consumed. Public actors below are used only to diagnose the frozen rule's failures. No actor is credited in production.

## Validation counts

Frozen narrow-score diagnostic: plants 8 correct / 0 incorrect / 24 unresolved; disables 0 correct / 0 incorrect / 12 unresolved. All 12 disables had five stable defender scoreboard bindings. The narrow rule saw multiple team score updates rather than a lone +100 candidate.

| Match / game / round | Build | Public disabler | Score packets relative to state transition (all defenders) |
| --- | ---: | --- | --- |
| 3579 / 6706 / R04 | 9636829 | Souffle | AZuKi86.Daystar: +100@+475; Binbin.Daystar: +100@+608; Pikanzu.Daystar: +100@+758; SealOrz.Daystar: +100@+248; SouffIe.Daystar: +100@+93, +100@+1560 |
| 3563 / 6675 / R02 | 9658832 | J9O | Fultz: +100@-108; J9O: +100@-126; Nuers: +100@-36; kyno: +100@-90; njr: +200@-72 |
| 3563 / 6675 / R10 | 9658832 | Spoit | Ambi: +100@+1155; Canadian: +100@+1022; Rexen: +100@+770; Spoit: +200@+903; Surf: +100@+1288 |
| 4283 / 8686 / R01 | 9769907 | dan | Nayqo.VP: +100@+1009; RORICK.VP: +100@+808; SkyZs.VP: +100@+1094; dan-_-.VP: +100@+111, +100@+1316; p4sh4.VP: +100@+941 |
| 4283 / 8686 / R09 | 9769907 | Yoggah | AsK.Geekay: +100@+275; Eupor.Geekay: +100@+221; GRUBY.Geekay: +100@+203; Sarks.Geekay: +100@+257; Yoggah.Geekay: +100@+239, +100@+1486 |
| 4283 / 8687 / R08 | 9769907 | AsK | AsK.Geekay: +100@+93, +100@+1406; Eupor.Geekay: +100@+239; GRUBY.Geekay: +100@+221; Sarks.Geekay: +130@-3733, +100@+275; Yoggah.Geekay: +100@+257 |
| 6157 / 10430 / R07 | 9820472 | VITAKING | cyber: +100@-108; handyy: +100@-36; kds: +100@-144; soulz1: +100@-18; vitaking: +200@-72 |
| 6157 / 10430 / R12 | 9820472 | KDS | cyber: +2350@+229; handyy: +2350@+265; kds: +2450@+211; soulz1: +2350@+283; vitaking: +2350@+247 |
| 6158 / 10563 / R05 | 9879602 | p4sh4 | Nayqo.VP: +100@+365; RORICK.VP: +100@+311; SkyZs.VP: +100@+1698; dan-_-.VP: +100@+329; p4sh4.VP: +100@+147, +100@+1479 |
| 6158 / 10563 / R06 | 9879602 | SkyZs | Nayqo.VP: +100@+1103; RORICK.VP: +100@+752; SkyZs.VP: +100@+1236, +100@+1368; dan-_-.VP: +100@+970; p4sh4.VP: +100@+837 |
| 6277 / 10576 / R01 | 9879602 | Hungry | Creedz.SECRET: +100@+1541; Croqson.SECRET: +100@+1303; Hungry.SECRET: +100@+151, +100@+1422; noaDOOM.SECRET: +100@+1677; vDrillz.SECRET: +100@+1260 |
| 6277 / 10576 / R06 | 9879602 | Hungry | Creedz.SECRET: +100@+1092; Croqson.SECRET: +100@+1074; Hungry.SECRET: +100@+786, +100@+1238; noaDOOM.SECRET: +100@+1110; vDrillz.SECRET: +100@+1038 |

## Why the 12 disables were unresolved

Most disable completions have a compact score wave for all five defenders, with one or more players receiving two +100 packets or a single +200 packet. The frozen plant-like rule requires one player to receive a unique nearby +100, so it abstains. Some complete team score waves precede the state transition by about 36-198 decompressed bytes. This is packet ordering, not an absent score update. A match-ending wave can combine the team reward with the extra amount in a single +2450 packet.

In 11 of 12 rounds, the public disabler also has the extra +100 relative to the four teammates. **Exception: 3563 / 6675 / R02.** The public disabler J9O receives +100, while njr receives +200; a relative-score-only rule would falsely credit njr. J9O's kill counter rose 34,214 bytes before the state and was followed by +100; njr's assist counter rose 34,178 bytes before state and was followed by +75. Neither known counter explains njr's extra +100 in the team wave. Do not promote a team residual alone.

Exact 3563/6675 R02 wave, ordered before the disable-state offset 57,693,663: J9O 1080→1180 at -126 bytes; Fultz 630→730 at -108; kyno 685→785 at -90; njr 945→1145 at -72; Nuers 529→629 at -36. Each score remains at that new value at the state packet. This wave is the last nearby scoreboard batch; no later defender score update occurs within +20,000 bytes. The state packet has no typed reference path to the partial player-entity candidates. The structural actor remains unresolved.

The original discovery disable 3073 R08 (older February layout) has five +250 losers, four +2350 winners, and one +2450 winner near the terminal timer. Its scoreboard components have no verified player binding, so the apparent +100 residual cannot name a disabler. Discovery 6156 R07/R10 score waves are just before the state transition and were missed by an after-only window. The original 3880 R10 round-end batch has several different teammate deltas, confounded by other scoring events.

At the 3073 R08 diagnostic timer terminal offset 59,532,324, the five +250 loser packets occur at +111/+205/+316/+410/+504 bytes. Four winners receive +2350 at +640/+765/+866/+967, and the fifth receives +2450 at +1051 (score 2330→4780). The raw entity/player join is unavailable in this February build, so neither that fifth player nor the public disabler can be independently identified from this scoreboard table. There is no trusted standalone actor packet or typed state0 completion in this round.

A same-build negative control reinforces the ambiguity. In 3563/6675 R04 (build 9658832), the replay has **no objective occurrence** but the winning defenders' late score packets include J9O +200 while Fultz, njr, kyno, and Nuers receive +100. J9O had a kill-counter increment 3,060 bytes before that +200, with no standalone score packet for that increment. Thus a +200 versus +100 team wave can be a delayed kill batch even without a disable. Reproduce this control with `research/objective_score_nonobjective_control.py`.

## Plants: resolved versus unresolved

All 32 extension plants had complete eligible-player scoreboard bindings. The table records replay-side evidence before attaching the public actor label. `Counter increments` counts kill/assist counter updates in the frozen -5000..+20000-byte collision interval; `near +100 players` counts eligible players with a +100 score packet in the 0..+1500-byte candidate interval.

| Match / game / round | Build | Public planter | Near +100 players | Counter increments | Frozen result |
| --- | ---: | --- | ---: | ---: | --- |
| 3579 / 6706 / R01 | 9636829 | SpeakEasy | 1 | 6 | unresolved (counter_collision) |
| 3579 / 6706 / R02 | 9636829 | Ape | 1 | 2 | unresolved (counter_collision) |
| 3579 / 6706 / R04 | 9636829 | Ape | 1 | 1 | unresolved (counter_collision) |
| 3579 / 6707 / R02 | 9636829 | Ape | 1 | 0 | correct (single_close_score) |
| 3579 / 6707 / R04 | 9636829 | Ape | 1 | 1 | unresolved (counter_collision) |
| 3563 / 6673 / R01 | 9658832 | Canadian | 1 | 1 | unresolved (counter_collision) |
| 3563 / 6673 / R03 | 9658832 | Canadian | 0 | 0 | unresolved (absent_or_ambiguous_score) |
| 3563 / 6675 / R02 | 9658832 | Surf | 1 | 2 | unresolved (counter_collision) |
| 3563 / 6675 / R10 | 9658832 | Kyno | 1 | 0 | correct (single_close_score) |
| 3563 / 6676 / R09 | 9658832 | Kyno | 0 | 4 | unresolved (counter_collision) |
| 4283 / 8685 / R01 | 9769907 | RORICK | 1 | 1 | unresolved (counter_collision) |
| 4283 / 8685 / R04 | 9769907 | p4sh4 | 1 | 1 | unresolved (counter_collision) |
| 4283 / 8686 / R01 | 9769907 | Yoggah | 1 | 2 | unresolved (counter_collision) |
| 4283 / 8686 / R09 | 9769907 | Nayqo | 1 | 3 | unresolved (counter_collision) |
| 4283 / 8686 / R14 | 9769907 | AsK | 1 | 0 | correct (single_close_score) |
| 4283 / 8687 / R05 | 9769907 | AsK | 1 | 1 | unresolved (counter_collision) |
| 4283 / 8687 / R08 | 9769907 | SkyZs | 1 | 2 | unresolved (counter_collision) |
| 6157 / 10428 / R03 | 9820472 | KDS | 1 | 1 | unresolved (counter_collision) |
| 6157 / 10428 / R09 | 9820472 | Loira | 1 | 1 | unresolved (counter_collision) |
| 6157 / 10428 / R10 | 9820472 | volpz | 1 | 0 | correct (single_close_score) |
| 6157 / 10430 / R01 | 9820472 | VITAKING | 2 | 3 | unresolved (counter_collision) |
| 6157 / 10430 / R07 | 9820472 | volpz | 0 | 4 | unresolved (counter_collision) |
| 6157 / 10430 / R10 | 9820472 | DiasLucas | 1 | 1 | unresolved (counter_collision) |
| 6157 / 10430 / R12 | 9820472 | Bokzera | 1 | 2 | unresolved (counter_collision) |
| 6158 / 10563 / R04 | 9879602 | Skeptic | 1 | 3 | unresolved (counter_collision) |
| 6158 / 10563 / R05 | 9879602 | Skeptic | 1 | 0 | correct (single_close_score) |
| 6158 / 10563 / R06 | 9879602 | Zaaramy | 1 | 3 | unresolved (counter_collision) |
| 6158 / 10563 / R07 | 9879602 | Nayqo | 1 | 1 | unresolved (counter_collision) |
| 6277 / 10576 / R01 | 9879602 | Skeptic | 1 | 0 | correct (single_close_score) |
| 6277 / 10576 / R06 | 9879602 | Skeptic | 1 | 1 | unresolved (counter_collision) |
| 6277 / 10576 / R11 | 9879602 | Creedz | 1 | 0 | correct (single_close_score) |
| 6277 / 10576 / R12 | 9879602 | Hungry | 1 | 0 | correct (single_close_score) |

Plant abstentions: 23 counter collisions and 1 absent/ambiguous close score; no incomplete identity bindings. Counter collisions can be true teammate kills, actor kills, assists, or unrelated events. They are not evidence that the named public actor is wrong, and this diagnostic does not distinguish their scoring components.

## Kill collisions near plants

Teammate-kill example: 4150 R07 public planter Hotancold receives +100 at +716 bytes after the plant state. Teammate GMZ's kill counter rises at +14,853 and GMZ receives +100 at +17,387. The kill belongs to GMZ, not to the planter; the frozen diagnostic abstains because its broad collision interval sees the kill. This shows why 23 abstentions do not mean 23 ambiguous immediate score packets.

Actor-kill example: 4139 R04 public planter Hotancold receives +100 at +304 bytes, then Hotancold's kill counter rises at +5,832 and score rises +200 at +7,251. Teammates' later score packets include +100, and SpiriTz has an assist counter increment followed by +175. A larger actor score is compatible with a plant plus later kill/team scoring, but this packet stream does not establish a claymore or the exact +200 decomposition. The frozen rule abstains.

## Known false-credit control: 4139 R07

Five SSG attackers have stable score bindings. Relative to the plant-state packet, Aiden's score changes 2475→2575 (+100) at +852 bytes and 2575→2675 (+100) at +15,205. Raid changes 2244→2254 (+10) at +2,425, has a kill-counter increment 4→5 at +13,955, then score 2254→2454 (+200) at +16,180. Rival, Dream, and Gity each receive +100 in the +15,200-byte team wave. The public planter is Raid. A simple close +100 or team-relative residual selects Aiden, incorrectly. The frozen diagnostic abstains because of the kill-counter collision. An assumed +100 kill subtraction does not prove the remaining +10 is objective credit or explain Aiden's first +100. No independent structural actor candidate is established; the drone identity table is invalid for pawn ownership.

## Next action

Study why 3563 R02 credits njr an unexplained +100 and whether a typed interaction/ownership packet independently identifies J9O. Describe team score waves by packet structure instead of adjusting a byte window to fit public labels. The 12-map set is consumed; reserve fresh professional objective rounds before any revised actor rule is evaluated independently. Keep all live actors unresolved and the deployed siege_style_v2 unchanged.
