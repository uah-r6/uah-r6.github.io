# Official HUD control: preplant and postplant opening order

[Official SAL Stage2 Day1 broadcast](https://www.youtube.com/watch?v=Ao6SRRhCmbg&t=15122s), upload20260905, RainbowSixEsports channel. This is a separate consumed observation after the credited-count checkpoint `eeca495`; it does not revise that checkpoint or any frozen final.

| Video seconds | Independently inspected HUD |
| ---: | --- |
| 15122 | Round3, score1-1, action clock0:43; 5v5, all ten observer cards alive; no death feed. |
| 15130 | Round3, action clock0:35; 5v5; live LOUD observer card shows Planting Defuser. |
| 15133 | Round3, action clock0:32; sampled instant still5v5; live LOUD Planting Defuser. |
| 15135 | Round3, action clock0:30;4v5; feed Gabu7z.LOUD -> pino.L5; pino dead card1/2/2, Gabu2/2/0. |
| 15140 | Round3, postplant clock41.19; DEFUSER IS PLANTED;3v4; feed Neskin.L5 -> Flastryy.LOUD above stemp.LOUD -> WIZARD.L5. pino/WIZARD/Flastryy dead, Neskin3/1/1. |

The first observed final elimination is Gabu ->pino before planting, while Neskin ->Flastryy appears after defuser completion/reset. The raw packet order agrees. Original feedback records action0:32 for the first event and postplant0:43 for Neskin ->Flastryy. Sorting all round events by remaining seconds reverses those two phases. This case supports a clock-epoch/order explanation, not a DBNO time claim.

Preserve raw finisher/victim/packet order and countdown provenance. A future elapsed-time/trade path must recognize a independently verified plant reset rather than subtract two remaining values across phases. No live opening/trade/pivot/clutch/KOST/Rating source changes; no historical correction or export.

Still unresolved: the separate map-level opening kill ownership difference pino vsNeskin. These frames verify round3 order but do not explain that residual across other rounds. No credited victim is assigned by nearest counter, aggregate total or camera-subject identity.
