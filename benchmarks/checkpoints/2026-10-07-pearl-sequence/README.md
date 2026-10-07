# Pearl-sequence validation checkpoint — 7 October 2026

Decision: retain champion 58a7d1fc6d951d905fd2eec71dda1adc876a06c5. No production strategy is changed by this checkpoint.

## Completed independent test

The frozen pearl-sequence candidate evaluates legal short continuations with a projected trail, rewarding pearl sequences rather than only the nearest target. Default Small retains its existing pocket policy.

- Candidate native SHA256: ab9737c93a71b739269438d25a9011b86a10b05e43ce76e4b560f915786b298c.
- Champion native SHA256: 74aa63378c4739a97b8bcc7f1d90083ce1341ed186b7593f828502636bf91533.
- Seeds 10087 and 10088; all 22 official maps, both sides.
- 88 complete unique valid fault-free games: 50 wins, 34 losses, 4 draws.
- Score with half-credit draws: 59.09%.
- Decisive Wilson 95% interval: 48.83–69.38%.
- Maze, Tower Defense and Trauma each 1–3; Schooltime, Stripes and Dilemma each 4–0.
- scripts/check_records.py passes. Both local binaries hash-match this manifest.

This completed batch misses the requested >=60% score and decisive Wilson lower bound >50%. Positive map subsets are not independently validated scoped repairs. No promotion is justified.

The attached manifest opts into explicit ENDTURN native polling. This runner change prevents a sampled stdin-park event from ending a reply before its explicit terminator is read. Its focused polling regression check passes. Official judge sandbox remains required; native polling changes must be disclosed when comparing this evidence to older matrices. These records are archived as this candidate's completed validation, without revising the published aggregate evidence count.

## Work in progress — excluded from conclusions

At the audit snapshot, the independent five-seed all-map confirmation contained 171 of 220 rows (84 wins, 85 losses, 2 draws). The Arena sprint-history repair contained 66 of 100 rows (37 wins, 29 losses). These are partial, completion-order-dependent observations, not accepted matrices or proof of improvement. Both jobs were still running; neither was restarted, stopped or modified.

Arena repair candidate native SHA256: f154056bd64bdb215eb1abccb3a5785b85d8911e68f99d0a8b1e404186ce1737. A scoped promotion still requires completed fresh repair evidence, exact unaffected-map controls and judge-sandbox validation.

The extended plan currently records a 55% score threshold. This checkpoint does not authorize relaxing the requested >=60% promotion target. Evaluate the finished independent matrix honestly against the applicable user requirements, inspect regressions, and require diverse-opponent evidence and exact-hash sandbox execution before any broad promotion.

Concurrent working edits and live matrix logs were preserved. Only this checkpoint and a snapshot of the completed 88-game matrix are published. Local results are not measured competition Elo. No website submission or activation occurred.
