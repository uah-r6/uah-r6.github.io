# Consumed body state 1: numerical bonus-health hypothesis

Research observation only. The production objective actor resolver still rejects state 1. No body enum, operator/action-start rule, objective actor, model input or final quality decision changes.

Complete consumed SAL/APAC audit: `{'rounds': 325, 'bound_body_state_properties': 7946, 'state_counts': {0: 3299, 2: 1717, 4: 2265, 3: 602, 1: 63}, 'state1_properties': 63, 'state1_above_baseline': 63, 'state1_consistent_bonus': 63, 'state1_dead_before': 0, 'state3_or4_with_positive_hp': 694}`.

Typed temporal body routes join the property to a unique declared stable UID. Known health field `252676c9` is compared with observed baseline/ceiling candidate fields `1149a672`/`013fd2da` and float field `80adcf7b`. The numerical hypothesis requires health above baseline, ceiling exactly baseline+20, health at most ceiling, and a positive fraction matching `(health-baseline)/baseline` within 1e-6. Names or external totals never choose a binding.

## Interpretation limits

Ubisoft describes [Finka Adrenal Surge](https://www.ubisoft.com/en-us/game/rainbow-six/siege/game-info/operators/finka) as a temporary team health boost. That primary description supports investigating bonus health; it does not define this internal replay state integer or certify all fields above. An independent current broadcast/HUD review is needed to distinguish bonus health from DBNO, revival or another condition.

Positive HP is insufficient for actor eligibility: known state 3/4 negative controls can retain positive health values. Do not replace the body guard with `HP>0`, infer state from an operator name, or allow unknown states by default. No extra kill, injury or revive event is reconstructed from these fields.

The exact three unresolved timer-owner cases and property offsets are in [the abstention inventory](v3-consumed-unknown-body-inventory.md). Their hypothetical recovery would require an isolated rule, broad cancellation/death/body-sharing/revive controls and separately frozen actor validation; original excluded maps and failed Rating finals remain excluded and failed.

Both source freezes, both failed final hashes and all 86 protected live-file hashes are unchanged. No import, archive mutation, public regeneration, push, publishing or live Rating change.
