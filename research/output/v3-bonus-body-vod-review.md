# Current Y11 HUD review: bonus-health planter false abstention

[Official SAL Stage2 Day1 broadcast, 8458 seconds](https://www.youtube.com/watch?v=Ao6SRRhCmbg&t=8458s), Rainbow Six Esports, uploaded2026-09-05. Consumed match8581/FaZe-Imperial, Villa physicalR06.

| VOD seconds | Independently visible HUD evidence |
| ---: | --- |
| 8457 | Villa R06, score2-3, clock1:34. KDS alive before plant. NearZ independently displays DBNO cross. |
| 8458 | Clock1:33. KDS card becomes yellow and explicitly says Planting the Defuser. |
| 8460 | Clock1:31. KDS still Planting the Defuser; blue circular boost indicators appear above all five Attack cards. NearZ still has DBNO cross. |
| 8463 | Clock1:28. KDS still Planting the Defuser, blue boost indicator present; no KDS DBNO/death indicator. |
| 8464 | Clock1:27. KDS still Planting the Defuser with blue boost indicator. |
| 8465 | Global DEFUSER IS PLANTED banner and44.77postplanttimer appear. KDS card leaves planting state and remains alive/boosted. Camera remains xSexyCake, not KDS. |

## Replay evidence and conclusion

Unique timer owner KDS numericUID`1040242176954841429`, body component`4027704524`. Verified plant offset`51470330`, interaction`51432785`–`51469727` with explicit state2 terminal. No body route replacement/sharing, prior actor death, all-opponents-dead interruption or competing completer.

Body state0→1 at offset`51437603`. Same declared component has120HP, observed100baseline/120ceiling and positive fraction`0.20000000298023224`. The production guard rejects state1 and remains unchanged.

The HUD identifies KDS actively planting while boosted and global completion follows. This independently supports a false abstention in this case. It is an explicit HUD association, not camera-subject attribution. The camera follows xSexyCake; the replay supplies numeric HP, which is not visually readable on KDS’s card. Do not call it direct close-up visual verification or universal state1 semantics.

Next: isolated consumed-data candidate accepting state1 only with structurally validated positive bonus health, full temporal UID/body identity and all existing occurrence/episode/cancellation/liveness guards. Run broad negative controls and separately freeze unused actor validation before any production change. Keep original SAL/APAC exclusions, predictions and permanent failed Rating results unchanged.

No production body enum, operator/action logic, Rating formula/default, SQLite, archive or public JSON change. Both frozen source checks, both failed final hashes and all86protected live hashes remain unchanged. No push/publish.
