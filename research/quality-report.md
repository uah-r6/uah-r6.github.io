# Professional replay quality audit

510 player-map rows from 51 maps; 374 pass all gates. Reserved rows by event: North America League Stage 2 2026: 60 clean rows; Europe MENA League Stage 2 2026: 16 clean rows. Europe MENA Stage 2 was evaluated once and is historical; North America Stage 2 remains untouched for a new final test.

| Cause | Rows | Treatment |
| --- | ---: | --- |
| Replay/public per-player K/D mismatch | 135 | Exclude |
| Unverified replay ↔ SiegeGG alias | 2 | Exclude |
| Map/team/score/round mismatch | 0 | Would reject entire map |

134 rows have a kill discrepancy; 4 have a death discrepancy. 49 of 51 map-wide kill and death totals agree with public targets. The map-wide exceptions are listed below. The Europe MENA Chalet replay has one teamkill, but the evidence does not establish whether SiegeGG counted it as a kill. Most discrepancies are per-player attribution; map-wide differences remain excluded. A pilot probe found cumulative scoreboard kill packets, but the entity-to-player offset changes across builds and even maps; it is not yet safe to use those counters to rewrite replay kill events. A separate read-only public round-log probe aligned 545 round winners (0 unaligned) and compared 910 multikill notes by unique operator; 64 disagree with replay-derived round kills. The notes provide independent evidence of attribution differences, but are incomplete and cannot by themselves safely correct every kill. The two remaining aliases are `MARKELELE.SH` and `fenglixiaqiu`; their target identities lack independent profile confirmation. Other investigated aliases are backed by replay profile UUIDs and public username histories in `sources.json`.

## Map-wide total differences

| Event | Map | Replay K-D | Public K-D |
| --- | --- | ---: | ---: |
| North America League Stage 1 2026 | Lair | 62-63 | 63-63 |
| Europe MENA League Stage 1 2026 | Chalet | 100-101 | 101-101 |

## Excluded rows

| Event | Map | Replay player | Replay K-D | Public K-D | Cause |
| --- | --- | --- | ---: | ---: | --- |
| North America League Stage 2 2026 | Villa | Gaveni.M80 | 8-7 | 7-7 | kills/deaths mismatch |
| North America League Stage 2 2026 | Villa | Gunnar.M80 | 4-7 | 5-7 | kills/deaths mismatch |
| North America League Stage 2 2026 | Nighthaven Labs | Snake.5F | 11-8 | 12-8 | kills/deaths mismatch |
| North America League Stage 2 2026 | Nighthaven Labs | Rival.5F | 6-10 | 5-10 | kills/deaths mismatch |
| North America League Stage 2 2026 | Chalet | Hotancold.100T | 12-6 | 13-6 | kills/deaths mismatch |
| North America League Stage 2 2026 | Chalet | Kason.100T | 9-8 | 8-8 | kills/deaths mismatch |
| North America League Stage 2 2026 | Chalet | Adrian.WC | 8-9 | 7-9 | kills/deaths mismatch |
| North America League Stage 2 2026 | Chalet | Bae94.WC | 1-10 | 2-10 | kills/deaths mismatch |
| North America League Stage 2 2026 | Border | Rexen.SR | 6-6 | 5-6 | kills/deaths mismatch |
| North America League Stage 2 2026 | Border | Surf.SR | 8-5 | 9-5 | kills/deaths mismatch |
| North America League Stage 1 2026 | Bank | Packer.4FUN | 11-9 | 12-9 | kills/deaths mismatch |
| North America League Stage 1 2026 | Bank | MikeW.4FUN | 14-9 | 13-9 | kills/deaths mismatch |
| North America League Stage 1 2026 | Bank | Beeno.4FUN | 9-10 | 10-10 | kills/deaths mismatch |
| North America League Stage 1 2026 | Bank | Sylo.4FUN | 8-8 | 7-8 | kills/deaths mismatch |
| North America League Stage 1 2026 | Bank | kanzen.WC | 8-10 | 7-10 | kills/deaths mismatch |
| North America League Stage 1 2026 | Bank | Bae94.WC | 15-11 | 16-11 | kills/deaths mismatch |
| North America League Stage 1 2026 | Bank | Rival.5F | 7-12 | 6-12 | kills/deaths mismatch |
| North America League Stage 1 2026 | Bank | Fenz.5F | 18-8 | 19-8 | kills/deaths mismatch |
| North America League Stage 1 2026 | Fortress | Canadian.SR | 8-8 | 9-8 | kills/deaths mismatch |
| North America League Stage 1 2026 | Fortress | Rexen.SR | 11-10 | 9-10 | kills/deaths mismatch |
| North America League Stage 1 2026 | Fortress | Surf.SR | 10-8 | 11-8 | kills/deaths mismatch |
| North America League Stage 1 2026 | Lair | Logan.oL | 9-8 | 8-8 | kills/deaths mismatch |
| North America League Stage 1 2026 | Lair | Nesta.oL | 2-8 | 3-8 | kills/deaths mismatch |
| North America League Stage 1 2026 | Fortress | Eddy.C9 | 10-8 | 8-8 | kills/deaths mismatch |
| North America League Stage 1 2026 | Fortress | Panbazou.C9 | 8-5 | 9-5 | kills/deaths mismatch |
| North America League Stage 1 2026 | Fortress | Monk.c9 | 10-7 | 12-7 | kills/deaths mismatch |
| North America League Stage 1 2026 | Fortress | Ewzy.C9 | 7-6 | 6-6 | kills/deaths mismatch |
| North America League Stage 1 2026 | Fortress | Trevmak.oL | 4-9 | 5-9 | kills/deaths mismatch |
| North America League Stage 1 2026 | Fortress | Vrionx.oL | 14-8 | 13-8 | kills/deaths mismatch |
| North America League Stage 1 2026 | Lair | Kason.100T | 6-6 | 8-6 | kills/deaths mismatch |
| North America League Stage 1 2026 | Lair | SpiriTz.100T | 13-7 | 11-7 | kills/deaths mismatch |
| North America League Stage 1 2026 | Fortress | kanzen.WC | 7-4 | 8-4 | kills/deaths mismatch |
| North America League Stage 1 2026 | Fortress | Adrian.WC | 12-3 | 11-3 | kills/deaths mismatch |
| North America League Stage 1 2026 | Fortress | MikeW.4FUN | 3-8 | 4-8 | kills/deaths mismatch |
| North America League Stage 1 2026 | Fortress | Sylo.4FUN | 4-8 | 3-8 | kills/deaths mismatch |
| North America League Stage 1 2026 | Fortress | Dream.SSG | 6-8 | 7-8 | kills/deaths mismatch |
| North America League Stage 1 2026 | Fortress | Gity.SSG | 9-10 | 8-10 | kills/deaths mismatch |
| North America League Stage 1 2026 | Fortress | Hotancold.100T | 12-8 | 14-8 | kills/deaths mismatch |
| North America League Stage 1 2026 | Fortress | GMZ.100T | 15-5 | 14-5 | kills/deaths mismatch |
| North America League Stage 1 2026 | Fortress | SpiriTz.100T | 9-9 | 8-9 | kills/deaths mismatch |
| Europe MENA League Stage 1 2026 | Lair | Dora.HERETICS | 4-5 | 5-5 | kills/deaths mismatch |
| Europe MENA League Stage 1 2026 | Lair | Lollo.HERETICS | 10-5 | 9-5 | kills/deaths mismatch |
| North America League Stage 1 2026 | Lair | JJBlaztful.5F | 3-7 | 4-7 | kills/deaths mismatch |
| North America League Stage 1 2026 | Clubhouse | J9O.DZ | 14-4 | 13-4 | kills/deaths mismatch |
| North America League Stage 1 2026 | Clubhouse | Fultz.DZ | 4-5 | 5-5 | kills/deaths mismatch |
| North America League Stage 1 2026 | Clubhouse | Canadian.SR | 2-7 | 4-7 | kills/deaths mismatch |
| North America League Stage 1 2026 | Clubhouse | Spoit.SR | 8-8 | 7-8 | kills/deaths mismatch |
| North America League Stage 1 2026 | Clubhouse | Surf.SR | 6-9 | 5-9 | kills/deaths mismatch |
| North America League Stage 1 2026 | Clubhouse | kanzen.WC | 13-10 | 12-10 | kills/deaths mismatch |
| North America League Stage 1 2026 | Clubhouse | bbySharKK.WC | 8-12 | 9-12 | kills/deaths mismatch |
| North America League Stage 1 2026 | Nighthaven Labs | Eddy.C9 | 0-9 | 1-9 | kills/deaths mismatch |
| North America League Stage 1 2026 | Nighthaven Labs | Ewzy.C9 | 7-8 | 6-8 | kills/deaths mismatch |
| South America League Stage 1 2026 | Nighthaven Labs | RESETZ.LOUD | 6-7 | 7-7 | kills/deaths mismatch |
| South America League Stage 1 2026 | Nighthaven Labs | Gabu7z.LOUD | 14-4 | 15-4 | kills/deaths mismatch |
| South America League Stage 1 2026 | Nighthaven Labs | FLASTRY.LOUD | 7-6 | 6-6 | kills/deaths mismatch |
| South America League Stage 1 2026 | Nighthaven Labs | stemp.LOUD | 3-10 | 2-10 | kills/deaths mismatch |
| South America League Stage 1 2026 | Kafe Dostoyevsky | HerdsZ.FURIA | 6-10 | 7-10 | kills/deaths mismatch |
| South America League Stage 1 2026 | Kafe Dostoyevsky | volpz7.FURIA | 3-9 | 2-9 | kills/deaths mismatch |
| South America League Stage 1 2026 | Lair | R4re.BD | 6-9 | 7-9 | kills/deaths mismatch |
| South America League Stage 1 2026 | Lair | guto.BD | 12-10 | 11-10 | kills/deaths mismatch |
| North America League Stage 1 2026 | Kafe Dostoyevsky | dfuzr.M80 | 6-3 | 5-3 | kills/deaths mismatch |
| North America League Stage 1 2026 | Kafe Dostoyevsky | Gunnar.M80 | 7-2 | 8-2 | kills/deaths mismatch |
| Europe MENA League Stage 2 2026 | Bank | vDrillz.SECRET | 14-7 | 13-7 | kills/deaths mismatch |
| Europe MENA League Stage 2 2026 | Bank | noaDOOM.SECRET | 8-9 | 9-9 | kills/deaths mismatch |
| Europe MENA League Stage 2 2026 | Bank | matzz-.- | 11-8 | 10-8 | kills/deaths mismatch |
| Europe MENA League Stage 2 2026 | Bank | Zaara.TH | 6-11 | 7-11 | kills/deaths mismatch |
| Europe MENA League Stage 1 2026 | Lair | GRUBY.Geekay | 6-8 | 5-8 | kills/deaths mismatch |
| Europe MENA League Stage 1 2026 | Lair | Sarks.Geekay | 6-7 | 7-7 | kills/deaths mismatch |
| Europe MENA League Stage 1 2026 | Chalet | RORICK.VP | 11-9 | 12-9 | kills/deaths mismatch |
| Europe MENA League Stage 1 2026 | Chalet | SkyZs.VP | 14-11 | 13-11 | kills/deaths mismatch |
| Europe MENA League Stage 1 2026 | Chalet | GRUBY.Geekay | 9-13 | 10-13 | kills/deaths mismatch |
| Europe MENA League Stage 1 2026 | Chalet | Eupor.Geekay | 4-11 | 3-11 | kills/deaths mismatch |
| Europe MENA League Stage 1 2026 | Chalet | Yoggah.Geekay | 13-9 | 14-9 | kills/deaths mismatch |
| Europe MENA League Stage 1 2026 | Chalet | Sarks.Geekay | 13-11 | 12-11 | kills/deaths mismatch |
| Europe MENA League Stage 1 2026 | Chalet | AsK.Geekay | 7-10 | 8-10 | kills/deaths mismatch |
| Europe MENA League Stage 1 2026 | Fortress | RORICK.VP | 6-4 | 7-4 | kills/deaths mismatch |
| Europe MENA League Stage 1 2026 | Fortress | SkyZs.VP | 7-5 | 6-5 | kills/deaths mismatch |
| Europe MENA League Stage 1 2026 | Fortress | GRUBY.Geekay | 6-8 | 5-8 | kills/deaths mismatch |
| Europe MENA League Stage 1 2026 | Fortress | AsK.Geekay | 7-7 | 8-7 | kills/deaths mismatch |
| Salt Lake City Major 2026 | Nighthaven Labs | Ambi | 10-4 | 11-4 | kills/deaths mismatch |
| Salt Lake City Major 2026 | Nighthaven Labs | Spoit | 7-4 | 6-4 | kills/deaths mismatch |
| Salt Lake City Major 2026 | Bank | Fultz | 8-8 | 9-8 | kills/deaths mismatch |
| Salt Lake City Major 2026 | Bank | J9O | 18-5 | 16-5 | kills/deaths mismatch |
| Salt Lake City Major 2026 | Bank | njr | 6-6 | 7-6 | kills/deaths mismatch |
| Esports World Cup 2026 | Kafe Dostoyevsky | Gruby | 10-10 | 11-10 | kills/deaths mismatch |
| Esports World Cup 2026 | Kafe Dostoyevsky | Yoggah | 14-9 | 13-9 | kills/deaths mismatch |
| Esports World Cup 2026 | Border | Bokzera | 10-10 | 11-10 | kills/deaths mismatch |
| Esports World Cup 2026 | Border | Dias | 7-8 | 6-8 | kills/deaths mismatch |
| Esports World Cup 2026 | Border | vitaking | 3-7 | 4-7 | kills/deaths mismatch |
| Esports World Cup 2026 | Border | soulz1 | 8-8 | 7-8 | kills/deaths mismatch |
| Esports World Cup 2026 | Lair | Dias | 7-7 | 6-7 | kills/deaths mismatch |
| Esports World Cup 2026 | Lair | Bokzera | 14-10 | 15-10 | kills/deaths mismatch |
| Salt Lake City Major 2026 | Clubhouse | kds | 13-10 | 12-10 | kills/deaths mismatch |
| Salt Lake City Major 2026 | Clubhouse | cyberzera | 12-12 | 13-12 | kills/deaths mismatch |
| Salt Lake City Major 2026 | Clubhouse | vitaking | 5-10 | 3-10 | kills/deaths mismatch |
| Salt Lake City Major 2026 | Clubhouse | handyy | 11-11 | 12-11 | kills/deaths mismatch |
| Salt Lake City Major 2026 | Clubhouse | soulz1 | 12-9 | 13-9 | kills/deaths mismatch |
| Salt Lake City Major 2026 | Clubhouse | kyno | 7-10 | 8-10 | kills/deaths mismatch |
| Salt Lake City Major 2026 | Clubhouse | Nuers | 20-10 | 19-10 | kills/deaths mismatch |
| Salt Lake City Major 2026 | Bank | Fultz | 11-5 | 10-5 | kills/deaths mismatch |
| Salt Lake City Major 2026 | Bank | kyno | 9-5 | 10-5 | kills/deaths mismatch |
| Salt Lake City Major 2026 | Bank | kds | 3-10 | 4-10 | kills/deaths mismatch |
| Salt Lake City Major 2026 | Bank | soulz1 | 4-8 | 3-8 | kills/deaths mismatch |
| Salt Lake City Major 2026 | Chalet | J9O | 3-6 | 2-6 | kills/deaths mismatch |
| Salt Lake City Major 2026 | Chalet | njr | 15-2 | 16-2 | kills/deaths mismatch |
| Asia Pacific League Stage 1 2026 | Clubhouse | MARKELELE.SH | 13-8 | 12-8 | kills/deaths mismatch; player alias lacks independent identity confirmation |
| Asia Pacific League Stage 1 2026 | Clubhouse | MrPuuuuuuncH.SH | 8-7 | 9-7 | kills/deaths mismatch |
| Asia Pacific League Stage 1 2026 | Clubhouse | fenglixiaqiu | 9-9 | 9-9 | player alias lacks independent identity confirmation |
| Asia Pacific Kickoff 2026 | Lair | Peeps.ORC | 14-9 | 13-9 | kills/deaths mismatch |
| Asia Pacific Kickoff 2026 | Lair | Kritj.ORC | 6-9 | 7-9 | kills/deaths mismatch |
| Asia Pacific Kickoff 2026 | Chalet | SealOrz.Daystar | 11-6 | 10-6 | kills/deaths mismatch |
| Asia Pacific Kickoff 2026 | Chalet | Binbin.Daystar | 4-10 | 3-10 | kills/deaths mismatch |
| Asia Pacific Kickoff 2026 | Chalet | Pikanzu.Daystar | 8-7 | 10-7 | kills/deaths mismatch |
| Asia Pacific Kickoff 2026 | Consulate | SouffIe.Daystar | 5-7 | 6-7 | kills/deaths mismatch |
| Asia Pacific Kickoff 2026 | Consulate | Binbin.Daystar | 5-7 | 4-7 | kills/deaths mismatch |
| Asia Pacific Kickoff 2026 | Consulate | Pikanzu.Daystar | 14-7 | 13-7 | kills/deaths mismatch |
| Asia Pacific Kickoff 2026 | Consulate | AZuKi86.Daystar | 2-8 | 3-8 | kills/deaths mismatch |
| Six Invitational 2026 | Clubhouse | Wizard | 2-8 | 1-7 | kills/deaths mismatch |
| Six Invitational 2026 | Clubhouse | Fntzy | 3-8 | 4-8 | kills/deaths mismatch |
| Six Invitational 2026 | Clubhouse | Htz | 2-7 | 2-8 | kills/deaths mismatch |
| Six Invitational 2026 | Border | Hoven5G | 8-8 | 9-8 | kills/deaths mismatch |
| Six Invitational 2026 | Border | Reeps965G | 13-8 | 11-8 | kills/deaths mismatch |
| Six Invitational 2026 | Border | SpeakEasy5G | 8-10 | 9-10 | kills/deaths mismatch |
| Six Invitational 2026 | Border | Wizard | 9-9 | 8-10 | kills/deaths mismatch |
| Six Invitational 2026 | Border | kondz | 10-10 | 6-10 | kills/deaths mismatch |
| Six Invitational 2026 | Border | pino | 10-8 | 11-8 | kills/deaths mismatch |
| Six Invitational 2026 | Border | Htz | 6-10 | 10-9 | kills/deaths mismatch |
| Asia Pacific Kickoff 2026 | Clubhouse | Ape5G.WBG | 2-4 | 4-4 | kills/deaths mismatch |
| Asia Pacific Kickoff 2026 | Clubhouse | Hoven5G.WBG | 5-6 | 4-6 | kills/deaths mismatch |
| Asia Pacific Kickoff 2026 | Clubhouse | SpeakEasy.WBG | 8-4 | 7-4 | kills/deaths mismatch |
| Asia Pacific Kickoff 2026 | Nighthaven Labs | SouffIe.Daystar | 7-7 | 6-7 | kills/deaths mismatch |
| Asia Pacific Kickoff 2026 | Nighthaven Labs | Binbin.Daystar | 0-7 | 1-7 | kills/deaths mismatch |
| Asia Pacific Kickoff 2026 | Nighthaven Labs | Ape5G.WBG | 6-5 | 5-5 | kills/deaths mismatch |
| Asia Pacific Kickoff 2026 | Nighthaven Labs | Hoven5G.WBG | 5-4 | 4-4 | kills/deaths mismatch |
| Asia Pacific Kickoff 2026 | Nighthaven Labs | Reeps965G.WBG | 11-5 | 12-5 | kills/deaths mismatch |
| Asia Pacific Kickoff 2026 | Nighthaven Labs | SpeakEasy.WBG | 5-3 | 6-3 | kills/deaths mismatch |

Quality gates were not relaxed to increase the fitting sample. Public K/D may itself contain an attribution error in a given case; the current evidence does not identify which side is correct for every row.
