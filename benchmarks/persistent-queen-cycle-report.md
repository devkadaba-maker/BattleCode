# Verified UNSW queen survival improvement — 7 October 2026

The frozen new bot beat the previous production champion **85–15 in 100 independent UNSW games**, across 50 entirely new seeds from both sides. The change meets every preregistered promotion gate. The other 21 official maps retain exactly the previous champion's outcomes and diagnostics in their controls.

| Check | Result |
| --- | --- |
| Independent UNSW strength, seeds 10500–10549 | 85 wins, 15 losses, 0 draws |
| Candidate as A / B | 47–3 / 38–12 |
| Decisive Wilson 95% interval | 76.72–90.69% |
| Paired-seed sign test | 36 positive, 1 negative, 13 ties; one-sided p=2.764863893e-10 |
| Queens alive at game end | Candidate 71/100; champion 1/100 |
| Other 21 maps, seed 10560 | All 42 candidate/control pairs exactly equal; 84 games including controls |
| Original C++ baseline / historical Python v2, seeds 10570–10574 | 10–0 / 10–0, both sides |
| Judge sandbox, candidate A / B | Wins at round 500; queen 3–0 / 5–0; max 24.5M / 23.9M CPU points per turn |
| Production native rebuild | Byte-identical to the frozen candidate |

All 204 final validation/control/diverse-opponent games are complete, unique, valid and fault-free. The separate 9–1 ten-game screening batch is excluded from the strength claim. The plan was written before the independent batch began; thresholds were score ≥60%, Wilson lower bound >50%, paired-seed p<0.025, full validity, exact unaffected-map equivalence and sandbox CPU below 100M points.

## What changed

The previous queen often followed food into a corridor where its own body removed the exit. On the UNSW starting footprint (64×64 board, ten own-team dragons at the queen's first turn), queens now reconstruct their ordered body, use verified movement history for off-screen segments, and predict movement, pearl growth and tail release. When necessary, a short paid move can shed a segment to escape, subject to the engine's two-segment minimum.

The strongest change is retaining a verified loop containing no pearl-spawning tiles. Its length must exceed the queen's body, so repeated movement does not cause a self collision or unwanted growth. Every actual next step is rechecked against visible dragons, enemy heads, kelp and portals; a blocked route is abandoned and replanned. Other official starting footprints and every non-queen retain the champion's policy.

The native benchmark has an opt-in explicit ENDTURN framing mode; process exits and timeouts still fail. Final matrix files are rewritten from the completed in-memory records, preventing workspace synchronization from leaving a summary that disagrees with the file. The official sandbox remains the execution check.

## Exact identities and reproduction

- New production/candidate SHA256: `e790e2ab49da5dda35397ceb5973712735cb16a79c01de3f02907ba5ee525bec`.
- Previous champion SHA256: `74aa63378c4739a97b8bcc7f1d90083ce1341ed186b7593f828502636bf91533`.
- Toolkit: `unswbc 1.2.9`.
- Previous source: remote checkpoint `45d306b404523bf77500cd3c5b5930b049c44a8c` (same production bot as before this change).

```sh
python scripts/setup.py
.venv/bin/python scripts/build_variant.py contact1 --ref 45d306b404523bf77500cd3c5b5930b049c44a8c --compile
.venv/bin/python scripts/build_variant.py persistent-queen-cycle --compile
.venv/bin/python scripts/benchmark.py --candidates .experiments/persistent-queen-cycle/.unswbc-build/bot --opponents .experiments/contact1/.unswbc-build/bot --maps unsw --seeds $(seq 10500 10549) --workers 4 --explicit-endturn --output /tmp/queen-confirmation.jsonl
.venv/bin/python scripts/verify_queen_survival.py
```

The verifier checks the committed matrices, fixed hashes, promotion criteria, exact control equivalence and archived sandbox logs. Native binary hashes depend on reproducing the build environment. The sandbox logs and raw JSONL files beside this report preserve the original checks. Smoke tests cover persistent-loop traversal, a newly blocked route, spawning-bed exclusion, future growth, tail-release collision semantics, off-screen reconstruction and scope exclusion.

## Rejected work and limits

Earlier promising screens did not automatically become production policy. The 220-game pearl-allocation retest returned 113–96–11; the 220-game harvest-path confirmation returned 100–108–12; a 400-game Arena history repair returned 184–216; the first moving-body queen confirmation returned 54–46. These were rejected. `research/bot-improvement-2026-10-07-index.json` inventories the retained local selection, rejected and diagnostic evidence. The large redundant binary ZIP is intentionally not committed; promotion evidence is published directly in the readable matrices beside this report. The incomplete queen-route screen and the invalid route-safety matrix are explicitly excluded.

This proves a local scoped improvement over the previous bot on UNSW with matched controls elsewhere. Historical opponents are not current ladder opponents, and these results are not measured competition Elo. No online competition submission or activation is performed.
