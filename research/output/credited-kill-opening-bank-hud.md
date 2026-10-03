# Independent Bank preplant/postplant order control

[Official SAL Stage2 Day3 broadcast](https://www.youtube.com/watch?v=4Qxi72CtGNA&t=18624s). This separate consumed review preserves the earlier credited-count and opening-order seals.

| Video second | Independently inspected HUD |
| ---: | --- |
| 18624 | R07, score2-4, action6.99,5v5; Bassetto planting; cyber visibly downed; no final-death feed. |
| 18626 | R07, action4.99,4v5; sole feed vitaking.FaZe -> Bassetto.L5; Bassetto dead0/5/0, vitaking4/2/2; no plant completion. |
| 18630 | R07, action0.97,2v3 on transition; feed ordered oldest-first vitaking->Bassetto, vitaking->PSYCHO, pino->kds, soulz1->pino, Neskin->vitaking, Neskin->cyber; WIZARD planting. |
| 18635 | R07, action0.00 with planting overtime,2v2; WIZARD still planting; Handyy7/2/1, Neskin alive4/5/3. |
| 18640 | R07, postplant41.92, DEFUSER IS PLANTED,1v2; feed Handyy.FaZe -> Neskin.L5; Handyy8/2/1, Neskin dead4/6/3. |
| 18643 | R07, postplant38.92,1v2; same Handyy->Neskin feed and completed plant banner. |

Raw packet order records vitaking ->Bassetto first at91880758/action0:06, while Handyy ->Neskin is later at91938582/postplant0:42. The official broadcast independently corroborates that order and clock reset. A round-wide decreasing-seconds sort wrongly puts Handyy first. Both changed SAL rounds now have independent preplant/postplant HUD controls.

Action0.00 persists during planting overtime; an elapsed-time/trade model must represent that interval as well as the postplant reset. Sparse screenshots are not subsecond synchronization. Packet ordering suffices for final-death order in these two cases, but cannot by itself identify the credited owner or DBNO-causing player of every final death.

No live opening/trade/pivot/clutch/KOST/Rating change, database write, corrected public export or regrading of any historical final. A universal opening-credit policy still needs explicit identity-linked DBNO/death evidence, particularly when competing downs precede deaths.
