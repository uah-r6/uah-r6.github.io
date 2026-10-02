# Score serialization runs: controls

Read-only consumed-data diagnostic. A group is an exact contiguous run of complete 18-byte 0x23 score records, with no intervening byte. It is not a decoded network packet, frame or causal scoring transaction. Parser clock ticks annotate each record; same displayed clock does not imply the same frame. All feedback matched the cached parser output.

| Match/game/round/type | Build | State offset | Run start distance | Score records (delta; latest clock tick) |
| --- | --- | --- | --- | --- |
| 3579/6707/R02/plant | 9636829 | 68396169 | -72128 | Reeps965G.WBG: 576->586 (10); clock 30@68321684 |
| 3579/6707/R02/plant | 9636829 | 68396169 | -28992 | Reeps965G.WBG: 586->686 (100); clock 17@68363613 |
| 3579/6707/R02/plant | 9636829 | 68396169 | -28839 | Terd5G.WBG: 660->735 (75); clock 17@68363613 |
| 3579/6707/R02/plant | 9636829 | 68396169 | +423 | Ape5G.WBG: 585->685 (100); clock 44@68395902 |
| 3579/6707/R02/plant | 9636829 | 68396169 | +7930 | Binbin.Daystar: 280->295 (15); clock 42@68402749 |
| 3579/6707/R02/plant | 9636829 | 68396169 | +23667 | SouffIe.Daystar: 255->375 (120); clock 37@68417584 |
| 3563/6675/R02/plant | 9658832 | 57656742 | -98877 | njr: 860->870 (10); clock 42@57556178 |
| 3563/6675/R02/plant | 9658832 | 57656742 | -96152 | Surf: 511->521 (10); clock 41@57558562 |
| 3563/6675/R02/plant | 9658832 | 57656742 | -65047 | J9O: 970->980 (10); clock 32@57590813 |
| 3563/6675/R02/plant | 9658832 | 57656742 | +319 | Surf: 521->621 (100); clock 44@57656945 |
| 3563/6675/R02/plant | 9658832 | 57656742 | +4140 | J9O: 980->1080 (100); clock 43@57660835 |
| 3563/6675/R02/plant | 9658832 | 57656742 | +36786 | J9O: 1080->1180 (100); clock 34@57691408; Fultz: 630->730 (100); clock 34@57691408; kyno: 685->785 (100); clock 34@57691408; njr: 945->1145 (200); clock 34@57691408 |
| 3563/6675/R02/disable | 9658832 | 57693663 | -32781 | J9O: 980->1080 (100); clock 43@57660835 |
| 3563/6675/R02/disable | 9658832 | 57693663 | -135 | J9O: 1080->1180 (100); clock 34@57691408; Fultz: 630->730 (100); clock 34@57691408; kyno: 685->785 (100); clock 34@57691408; njr: 945->1145 (200); clock 34@57691408 |
| 3563/6675/R02/disable | 9658832 | 57693663 | -45 | Nuers: 529->629 (100); clock 34@57691408 |
| 3563/6675/R02/disable | 9658832 | 57693663 | +603 | 4027266989: 1->2 (1); clock 0@57693784 |
| 3563/6675/R10/plant | 9658832 | 66011334 | -62785 | Ambi: 1857->1867 (10); clock 61@65947370 |
| 3563/6675/R10/plant | 9658832 | 66011334 | -62271 | J9O: 3684->3689 (5); clock 61@65947370 |
| 3563/6675/R10/plant | 9658832 | 66011334 | -34567 | Rexen: 1950->1960 (10); clock 55@65976115 |
| 3563/6675/R10/plant | 9658832 | 66011334 | +422 | kyno: 2430->2530 (100); clock 44@66011063 |
| 3563/6675/R10/plant | 9658832 | 66011334 | +14938 | J9O: 3689->3694 (5); clock 40@66026238 |
| 3563/6675/R10/plant | 9658832 | 66011334 | +16125 | J9O: 3694->3699 (5); clock 40@66026238 |
| 3563/6675/R10/disable | 9658832 | 66117668 | -41083 | Nuers: 2948->3023 (75); clock 29@66074157; Rexen: 2060->2070 (10); clock 29@66074157; Spoit: 2841->2851 (10); clock 29@66074157; Canadian: 1590->1600 (10); clock 29@66074157; Ambi: 1867->1877 (10); clock 29@66074157 |
| 3563/6675/R10/disable | 9658832 | 66117668 | -40975 | Surf: 2340->2350 (10); clock 29@66074157 |
| 3563/6675/R10/disable | 9658832 | 66117668 | -23052 | Spoit: 2851->2971 (120); clock 24@66091543 |
| 3563/6675/R10/disable | 9658832 | 66117668 | +761 | Rexen: 2070->2170 (100); clock 0@66117789 |
| 3563/6675/R10/disable | 9658832 | 66117668 | +894 | Spoit: 2971->3171 (200); clock 0@66117789 |
| 3563/6675/R10/disable | 9658832 | 66117668 | +1013 | Canadian: 1600->1700 (100); clock 0@66117789 |
| 6157/10430/R12/plant | 9820472 | 65456507 | -62648 | kds: 3055->3065 (10); clock 31@65391388 |
| 6157/10430/R12/plant | 9820472 | 65456507 | -62612 | cyber: 3245->3255 (10); clock 31@65391388; vitaking: 3462->3472 (10); clock 31@65391388; handyy: 3021->3031 (10); clock 31@65391388; soulz1: 3472->3482 (10); clock 31@65391388 |
| 6157/10430/R12/plant | 9820472 | 65456507 | -38143 | Bokzera: 3850->3860 (10); clock 23@65417041 |
| 6157/10430/R12/plant | 9820472 | 65456507 | +423 | Bokzera: 3860->3960 (100); clock 44@65456233 |
| 6157/10430/R12/plant | 9820472 | 65456507 | +9620 | LoiraDEMON: 2985->3060 (75); clock 41@65463902 |
| 6157/10430/R12/plant | 9820472 | 65456507 | +9656 | Bokzera: 3960->4080 (120); clock 41@65463902 |
| 6157/10430/R12/disable | 9820472 | 65503956 | -47026 | Bokzera: 3860->3960 (100); clock 44@65456233 |
| 6157/10430/R12/disable | 9820472 | 65503956 | -37829 | LoiraDEMON: 2985->3060 (75); clock 41@65463902 |
| 6157/10430/R12/disable | 9820472 | 65503956 | -37793 | Bokzera: 3960->4080 (120); clock 41@65463902 |
| 6157/10430/R12/disable | 9820472 | 65503956 | +112 | Dias: 2691->2941 (250); clock 26@65502741; LoiraDEMON: 3060->3310 (250); clock 26@65502741; VolpsZ: 3090->3340 (250); clock 26@65502741; HerdsZ: 2687->2937 (250); clock 26@65502741; Bokzera: 4080->4330 (250); clock 26@65502741; kds: 3165->5615 (2450); clock 26@65502741; cyber: 3330->5680 (2350); clock 26@65502741; vitaking: 3472->5822 (2350); clock 26@65502741; handyy: 3031->5381 (2350); clock 26@65502741; soulz1: 3557->5907 (2350); clock 26@65502741 |
| 6157/10430/R12/disable | 9820472 | 65503956 | +1230 | 4030825820: 6->7 (1); clock 0@65504303 |
| 4139/None/R07/plant | 9769907 | 61871641 | -77010 | Raid.SSG: 2149->2244 (95); clock 57@61794187 |
| 4139/None/R07/plant | 9769907 | 61871641 | -71568 | Aiden.SSG: 2465->2475 (10); clock 55@61800054 |
| 4139/None/R07/plant | 9769907 | 61871641 | -39261 | SpiriTz.100T: 1610->1620 (10); clock 47@61831969 |
| 4139/None/R07/plant | 9769907 | 61871641 | +843 | Aiden.SSG: 2475->2575 (100); clock 44@61872278 |
| 4139/None/R07/plant | 9769907 | 61871641 | +2416 | Raid.SSG: 2244->2254 (10); clock 44@61872278 |
| 4139/None/R07/plant | 9769907 | 61871641 | +3783 | SpiriTz.100T: 1620->1730 (110); clock 44@61872278 |

Only direct validated 0x23-prefixed score records are included by this observer. Inherited continuation fields are not treated as new records; increments come from the complete cached ledger, not differences between incomplete direct snapshots. No actor is selected; serialization adjacency must not be promoted to causal score grouping without further evidence.
