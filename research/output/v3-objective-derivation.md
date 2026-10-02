# Separate v3 trusted-objective development data

Player-map rows470, clean306, original clean development331; maps47. Objective totals`{'plant': 110, 'plant_unresolved': 5, 'plant_resolved': 105, 'disable': 18, 'disable_resolved': 18}`. Parser/alignment failures`[]`.

Original v2 train events and EWC development only; both September events excluded. No new Rating targets, no final errors, no source downloads. Existing physical/logical manifests and parser caches reused; normalized maps and observations written to separate ignored v3 paths. Full maps with unresolved objective actors are excluded from fit, never treated as zero. Actor labels/totals from third-party sites do not enter features or eligibility.

New normalized counts/KOST are rederived from verified actors. For the requested one-feature comparison both arms retain the original eight v2 round inputs (including KOST) identically, and only the verified plants+disables feature is added. Corrected KOST changes are listed below and are not silently introduced as a second feature change.

| Match/game | Map | Objectives | Complete | KOST changes |
| --- | --- | --- | --- | --- |
| 3905/7016 | Clubhouse | {'plant': 3, 'plant_unresolved': 3} | False | [] |
| 4115/8555 | Clubhouse | {} | True | [] |
| 4147/7411 | Lair | {'plant': 3, 'plant_resolved': 3} | True | [] |
| 4149/7418 | Nighthaven Labs | {'plant': 1, 'plant_resolved': 1, 'disable': 1, 'disable_resolved': 1} | True | [{'player': 'Kyno.DZ', 'old': 8, 'new': 9}] |
| 4136/8056 | Bank | {'plant': 1, 'plant_resolved': 1, 'disable': 1, 'disable_resolved': 1} | True | [] |
| 4140/8330 | Fortress | {'plant': 1, 'plant_resolved': 1} | True | [] |
| 4141/8331 | Bank | {'plant': 1, 'plant_resolved': 1} | True | [] |
| 4132/7858 | Bank | {'plant': 4, 'plant_resolved': 4, 'disable': 1, 'disable_resolved': 1} | True | [] |
| 4134/7861 | Fortress | {'plant': 2, 'plant_resolved': 2} | True | [] |
| 4135/7862 | Lair | {} | True | [] |
| 3745/7405 | Fortress | {} | True | [] |
| 4150/7419 | Lair | {'plant': 4, 'plant_resolved': 4} | True | [] |
| 4148/7413 | Fortress | {'plant': 1, 'plant_resolved': 1} | True | [] |
| 4139/8307 | Fortress | {'plant': 2, 'plant_resolved': 2} | True | [] |
| 3637/6842 | Fortress | {'plant': 2, 'plant_resolved': 2} | True | [] |
| 3639/6844 | Lair | {'plant': 4, 'plant_resolved': 4, 'disable': 1, 'disable_resolved': 1} | True | [] |
| 4127/7422 | Lair | {'plant': 3, 'plant_resolved': 3} | True | [] |
| 4129/7433 | Clubhouse | {} | True | [] |
| 4137/8073 | Clubhouse | {'plant': 2, 'plant_resolved': 2} | True | [] |
| 4138/8130 | Nighthaven Labs | {'plant': 1, 'plant_resolved': 1} | True | [] |
| 4118/8666 | Nighthaven Labs | {'plant': 2, 'plant_resolved': 2} | True | [] |
| 4119/8672 | Lair | {'plant': 1, 'plant_resolved': 1} | True | [] |
| 4120/8673 | Kafe Dostoyevsky | {'plant': 2, 'plant_resolved': 2} | True | [] |
| 4112/8360 | Lair | {'plant': 7, 'plant_resolved': 7} | True | [{'player': 'live.LOUD', 'old': 7, 'new': 8}, {'player': 'R4re.BD', 'old': 6, 'new': 7}, {'player': 'guto.BD', 'old': 9, 'new': 10}] |
| 4133/7860 | Kafe Dostoyevsky | {'plant': 2, 'plant_resolved': 1, 'disable': 1, 'disable_resolved': 1, 'plant_unresolved': 1} | False | [] |
| 4283/8685 | Lair | {'plant': 2, 'plant_resolved': 2} | True | [] |
| 4283/8686 | Chalet | {'plant': 3, 'plant_resolved': 3, 'disable': 2, 'disable_resolved': 2} | True | [{'player': 'Nayqo.VP', 'old': 9, 'new': 10}] |
| 4283/8687 | Fortress | {'plant': 2, 'plant_resolved': 2, 'disable': 1, 'disable_resolved': 1} | True | [] |
| 3563/6673 | Nighthaven Labs | {'plant': 2, 'plant_resolved': 2} | True | [] |
| 3563/6675 | Bank | {'plant': 2, 'plant_resolved': 2, 'disable': 2, 'disable_resolved': 2} | True | [{'player': 'kyno', 'old': 6, 'new': 7}] |
| 3563/6676 | Kafe Dostoyevsky | {'plant': 1, 'plant_resolved': 1} | True | [] |
| 6156/10425 | Kafe Dostoyevsky | {'plant': 4, 'plant_resolved': 4, 'disable': 2, 'disable_resolved': 2} | True | [{'player': 'AsK', 'old': 11, 'new': 12}, {'player': 'Yoggah', 'old': 12, 'new': 13}] |
| 6156/10426 | Chalet | {'plant': 3, 'plant_resolved': 2, 'plant_unresolved': 1} | False | [] |
| 6157/10428 | Border | {'plant': 3, 'plant_resolved': 3} | True | [] |
| 6157/10430 | Lair | {'plant': 4, 'plant_resolved': 4, 'disable': 2, 'disable_resolved': 2} | True | [{'player': 'VolpsZ', 'old': 7, 'new': 8}] |
| 3554/6677 | Clubhouse | {'plant': 2, 'plant_resolved': 2} | True | [] |
| 3554/6678 | Bank | {'plant': 4, 'plant_resolved': 4} | True | [{'player': 'kyno', 'old': 7, 'new': 8}] |
| 3554/6679 | Chalet | {'plant': 3, 'plant_resolved': 3} | True | [{'player': 'kyno', 'old': 3, 'new': 4}] |
| 3880/7625 | Bank | {'plant': 5, 'plant_resolved': 5, 'disable': 1, 'disable_resolved': 1} | True | [{'player': 'Pikanzu.Daystar', 'old': 4, 'new': 5}] |
| 3879/7624 | Clubhouse | {'plant': 3, 'plant_resolved': 3} | True | [] |
| 3585/6720 | Lair | {'plant': 2, 'plant_resolved': 2} | True | [] |
| 3585/6721 | Chalet | {'plant': 2, 'plant_resolved': 2} | True | [] |
| 3585/6722 | Consulate | {'plant': 4, 'plant_resolved': 4, 'disable': 1, 'disable_resolved': 1} | True | [{'player': 'BGMan.ORC', 'old': 7, 'new': 8}, {'player': 'SouffIe.Daystar', 'old': 6, 'new': 7}] |
| 3073/5718 | Clubhouse | {'plant': 2, 'plant_resolved': 2, 'disable': 1, 'disable_resolved': 1} | True | [] |
| 3073/5719 | Border | {'plant': 3, 'plant_resolved': 3} | True | [] |
| 3579/6706 | Clubhouse | {'plant': 3, 'plant_resolved': 3, 'disable': 1, 'disable_resolved': 1} | True | [{'player': 'Ape5G.WBG', 'old': 5, 'new': 6}] |
| 3579/6707 | Nighthaven Labs | {'plant': 2, 'plant_resolved': 2} | True | [] |

Original dataset SHA256`2454eb35ebe06df8d91f950b17cab8cea0a26384d9c40cbdd786f7e4f11b04de` unchanged; frozen v2 SHA256`1d8386767247e0d78ed36a23ff09128ff94f7d65fc86599619573a7cbad0a295` unchanged. 86 live file hashes unchanged. No SQLite/public/archive/liveRating updates. Reproduce `.venv/Scripts/python.exe research/v3_objective_derive.py`; never run the original pipeline derive command to overwrite frozen observations for this experiment.
