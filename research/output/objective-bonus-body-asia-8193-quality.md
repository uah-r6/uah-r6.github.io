# ASIA 8193 consumed roster quality diagnostic

Historical whole-map refusal remains immutable; no omitted/reconstructed player or admitted map.

| Physical folder | Round | Header count | Exact refusal |
| --- | ---: | ---: | --- |
| Match-2026-09-10_23-43-06-25740 | 1 | 10 | none |
| Match-2026-09-10_23-43-06-25740 | 2 | 10 | none |
| Match-2026-09-10_23-43-06-25740 | 3 | 10 | none |
| Match-2026-09-10_23-43-06-25740 | 4 | 10 | none |
| Match-2026-09-10_23-43-06-25740 | 5 | 10 | duplicate_uid |
| Match-2026-09-11_00-04-54-25740 | 1 | 10 | none |
| Match-2026-09-11_00-04-54-25740 | 2 | 10 | none |
| Match-2026-09-11_00-04-54-25740 | 3 | 10 | none |
| Match-2026-09-11_00-04-54-25740 | 4 | 10 | none |
| Match-2026-09-11_00-04-54-25740 | 5 | 10 | none |

The exact issue is numeric UID collision, not missing profile UUIDs: SpeakEasy.WBG, Hoven5G.WBG, Terd5G.WBG and Gotti5G.WBG all carry UID6366317606386794496 in first-folder physical R05. All ten profile UUIDs are distinct. R05 starts and ends 2–2, an unfinished physical attempt. The frozen chronology guard validates identities before recognizing zero-score attempts, so this still refused the entire map. Neither guard ordering nor the sealed quality outcome is changed after labels.

The header/normalized inventory is inspected only. Later valid headers do not prove an earlier missing numeric UID. No raw packet reconstruction, actor label or score-based player association was attempted. The original full-roster safeguard remains unchanged.
