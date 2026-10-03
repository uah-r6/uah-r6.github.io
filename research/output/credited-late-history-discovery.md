# Late event-history discovery — consumed controls, 2026-10-03

This is additive research after local `fa220a8`. The [count-only production preview](credited-kill-production-preview.md), published objective correction, original studies and immutable v2 Rating inputs are unchanged. No credited-kill or event-stat migration has occurred.

## UID discovery scope

An explicit observed prefix/width table recognizes 1,696 complete ten-player UID lists in the two original sealed buffers, covering 16,960 literal references. The lists occur at offsets 82,967–186,665 and 38,164–203,116, far before action start. Their opaque payloads contain no additional literal full player UID. They do not establish damage relationships. The earlier narrower 526-list result remains preserved separately.

There are 370 other literal references, including 151 after action start. Of these, 113 match the exact header tuple `UID64 + RoleImage64 + Alliance32`. Fifty-two adjacent tuple pairs occur after the last live feed elimination. They include repeated earlier payloads: physical late copies cannot be treated as live occurrence timestamps or independent events.

## Bounded candidate event layouts

The research prototype preserves explicit bounds and raw values. It does not change the production Go reader or implement a Python tracker replay decoder.

| Candidate kind | Observed local fields | Current interpretation |
| --- | --- | --- |
| 1 | Byte kind; opaque uint32 scalar; weapon uint64; entity reference uint64; two header-matching identity tuples; boolean headshot | Finisher elimination fields corroborated on the fixed controls below |
| 5 / 7 | Byte kind; opaque uint32 scalar; entity reference uint64; two header-matching identity tuples | Target-state association supported; first identity's causal role remains pending |

Six fixed consumed rounds cover four builds. Every one of their **41 unique kind-1 events** matches the unchanged same-round finisher/victim, weapon, headshot and physical feed order. This includes both independently reviewed plant-clock reset cases and two current UAH credit-split rounds. Repeated identical late payload copies are retained separately; they are not counted again.

| Source | Build | Unique eliminations | Evidence |
| --- | ---: | ---: | --- |
| SAL 8580 Lair R06 | 9879602 | 8 | Kheyze/Stk versus Maia finish, ordinary same-round controls |
| SAL 8583 Clubhouse R02 | 9879602 | 4 | Neskin/resetz versus pino finish, mandatory opening control |
| SAL 8583 Clubhouse R03 | 9879602 | 8 | Independent preplant/postplant death-order control |
| SAL 8594 Bank R07 | 9883691 | 9 | Independent clock reset and planting-overtime control |
| UAH Fortress R04 | 9901603 | 6 | Dino/hidebuff candidate versus Lgon finish |
| UAH Michigan Border R03 | 9918362 | 6 | Lgon/getSpoopd candidate versus Jay finish |

Only four new content-addressed sample dumps were generated for this hypothesis. Original cached buffers, downloads, old parsing pipelines, targets and model evaluations were not rerun or replaced. All private bytes/results remain ignored by Git.

## Split identity and target body controls

| Case | Candidate kind 5 identities / scalar | Kind 1 finisher / scalar |
| --- | --- | --- |
| Stk | Kheyze → Stk / 4706 | Maia → Stk / 4834 |
| resetz | Neskin → resetz / 5608 | pino → resetz / 5633 |
| hidebuff | Dino → hidebuff / 39912 | Lgon → hidebuff / 40935 |
| getSpoopd | Lgon → getSpoopd / 36791 | Jay → getSpoopd / 36833 |

The first two targets have previously reviewed independent official HUD DBNO evidence. The latter two agree with the independently derived UAH counter-credit differences. This is a candidate event relationship, not permission to replace finisher names or manufacture a generic credited-killer join.

Independent same-round kind-1/feed matches bound candidate event order. Within those bounds, each of the **18 candidate kind-5 targets** has exactly one raw-3 observation on its unique temporal UID/body route with the known body class. Both kind-7 targets have exactly one active-state observation. No scalar-to-time interpolation, nearest counter or byte-distance association is used. Kind-7 includes Maia/Jv92 and Handyy/soulz; recovery lifecycle and first-reference reviver semantics still need independent controls.

These findings support the DBNO/recovery hypotheses for the second identity. They do not independently establish the first identity's damaging shot, a universal enum, or Ubisoft's final credit policy after recovery/another down/teamkill/self-down. Do not silently call a candidate first identity a proven downer.

## Clock limits

The opaque scalar orders all 41 finisher events consistently, including the known countdown resets. Its numeric magnitude differs between professional and local recordings. Many professional differences are near 30 units per displayed countdown second; local examples are near 210. Coarse ticks, zero clocks and phase resets produce other ratios.

**No rate is assumed.** Neither 30 nor 210 is converted to elapsed seconds. The field may be tied to recording/playback cadence or another clock; explicit semantics, variable-rate behavior, resets and overtime remain unverified. Trades still require a trustworthy elapsed clock. First-final-elimination order is promising; competing-DBNO opening policy and generic credited ownership remain pending.

## Outer framing and incomplete controls

An enclosing structure has a 4-byte opaque header value, an 8-byte declared payload length, a 4-byte item count, then a 9-byte reference descriptor and items. Bounds are checked against the buffer. Twenty-one containers are fully consumed under the recognized layouts; eighteen remain partial because unknown items or trailing data occur.

| Source | Complete containers | Partial containers | Recognized candidate physical copies framed before unknown items |
| --- | ---: | ---: | ---: |
| Lair R06 | 3 | 5 | 19 / 41 |
| Clubhouse R02 | 3 | 0 | 11 / 11 |
| Clubhouse R03 | 1 | 5 | 0 / 31 |
| Bank R07 | 2 | 6 | 7 / 66 |
| Fortress R04 | 6 | 0 | 21 / 21 |
| Michigan Border R03 | 6 | 2 | 34 / 35 |

The first framing probe stopped on Clubhouse R03: an unknown item precedes the first recognized event. The follow-up selects a unique declared size/count container enclosing that event. No preceding-byte repair or event drop is accepted. Unknown kinds remain partial, so the prototype is **not a complete or production-ready event-history parser**. The standalone 41-event field parity is distinct from whole-container completeness.

## Verification and next action

450 Python tests passed, one optional real-replay smoke skipped, six subtests passed. Go tests including Y11 fixtures and go vet passed earlier in this session; Go/shared stat/export/web code did not change afterward. Previous production web builds remain applicable. Protected SQLite, archives, public JSON, objective actors, action/operator logic, v2 inputs and original studies remain identical.

Next: characterize unknown history items with explicit bounded identity layouts, preserve terminal/partial refusal cases, and independently validate kind-5/7 actor roles and recovery/reset behavior before a separate opt-in Go reader. Determine scalar clock semantics across professional/local recording rates and planting overtime. Never tune old Rating finals, assume one fixed tick rate, count repeated history copies, guess a credited victim from totals, or migrate a partial Chalet map. Stage B is not ready; the count-only preview and incomplete-map policy remain unchanged.
