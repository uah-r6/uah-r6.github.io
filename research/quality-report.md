# Professional replay quality audit

260 player-map rows from 26 maps; 182 pass all gates. 16 clean September rows were reserved and evaluated once as the final event.

| Cause | Rows | Treatment |
| --- | ---: | --- |
| Replay/public per-player K/D mismatch | 77 | Exclude |
| Unverified replay ↔ SiegeGG alias | 2 | Exclude |
| Map/team/score/round mismatch | 0 | Would reject entire map |

76 rows have a kill discrepancy; 4 have a death discrepancy. 25 of 26 map-wide kill and death totals agree with public targets. The exception is Europe MENA Stage 1 Chalet: the replay has 100 non-teamkill kills and 101 deaths; the public target has 101 kills and 101 deaths. The replay has one teamkill, but the evidence does not establish whether SiegeGG counted it as a kill. Most discrepancies are per-player attribution, not lost rounds. A pilot probe found cumulative scoreboard kill packets, but the entity-to-player offset changes across builds and even maps; it is not yet safe to use those counters to rewrite replay kill events. A separate read-only public round-log probe aligned 280 round winners (0 unaligned) and compared 464 multikill notes by unique operator; 38 disagree with replay-derived round kills. The notes provide independent evidence of attribution differences, but are incomplete and cannot by themselves safely correct every kill. The two remaining aliases are `MARKELELE.SH` and `fenglixiaqiu`; their target identities lack independent profile confirmation. Other investigated aliases are backed by replay profile UUIDs and public username histories in `sources.json`.

## Excluded rows

| Event | Map | Replay player | Replay K-D | Public K-D | Cause |
| --- | --- | --- | ---: | ---: | --- |
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
