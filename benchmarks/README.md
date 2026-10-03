# October 4, 2026 experiments

Engine/toolkit: `unswbc==1.2.9`; current bundled maps; native C++ built with
`g++ -std=c++20 -O2`. Recorded matches are checked against their full manifests
with `scripts/check_records.py`, including uniqueness and engine-winner consistency.
All 1,105 recorded games form complete matrices with no invalid actions
or bot runtime faults. These are local games, not Elo measurements.

## Selection and limitations

`vision6` was the first selected candidate: `PARENT_SPLIT_LIMIT=3`,
`VISION_TARGET_WEIGHT=6`, `FREE_PEARL_SPRINT=0`, `QUEEN_HUNT=0`,
`QUEEN_SPLIT_LIMIT=3`. The baseline uses `cpp_bot/main.cpp` from `29245ea`, with
the updated official helper, and the same updated maps as the candidates.

The eight screening maps are Arena, Default Small, Default, Big Empty,
Schooltime, Trophy, Colosseum and Queen of Spades. Every map/seed has both sides.
Seed 101 was used for tuning; 202 and 303 were fresh validation seeds. Fourteen
additional maps and two Python opponents were checked with seed 404. Do not
reuse these as unseen evidence in subsequent tuning.

| Variant | Wins vs baseline | Losses vs baseline | Draws | Evidence |
| --- | ---: | ---: | ---: | --- |
| Split limit 2, vision off | 7 | 9 | 0 | 16 screening games |
| Split limit 3, vision off | 23 | 25 | 0 | 16 screen + 32 validation |
| Split limit 4, vision off | 8 | 8 | 0 | 16 screening games |
| Split 3, vision weight 1 | 4 | 12 | 0 | 16 screening games |
| Split 3, vision weight 3 | 9 | 7 | 0 | 16 screening games |
| Split 3, vision weight 6 | 48 | 27 | 1 | 16 screen + 32 validation + 28 new-map games |
| Split 3, free pearl sprint | 9 | 7 | 0 | 16 screening games |
| Split 3, queen never plans a split | 9 | 7 | 0 | 16 screening games |
| Split 3, queen never splits + free sprint | 7 | 9 | 0 | 16 screening games |
| Split 3, queen hunting | 23 | 25 | 0 | 16 screen + 32 validation |

The cap alone did not improve the baseline on the combined sample. The result
supports the selected combination, not a claim that three is universally the
best split limit. The vision candidate also beat the root Python bot and hard
v2 16–0 each. Those opponents are historical local bots, not current ladder
leaders. Native bot randomness is not fully controlled by the toolkit seed;
the C++ policies here are deterministic.

The initial additional-map sample returned 12–15–1. Losses on Maze, Portals, Stripes, Tower
Defense and UNSW occurred on both tested sides. Some queens walked into walls
after becoming trapped; some died in head collisions, and some survived but
lost on growth. The final turn is evidence of the immediate death, not proof
of the strategic cause. Follow-up work should replay the preceding turns and
test corridor survival, portal safety and spawn anticipation on fresh seeds.

## Fresh gate against the original repository baseline

`submission-gate.jsonl` records 220 complete matches against `29245ea`: all 22
official bundled maps, both sides, five fresh seeds (505, 606, 707, 808, 909).
The selected policy returned **131–84–5**, a **60.68% score** with draws counted
as half a win. All games are valid. The decisive-game Wilson 95% interval is
**54.27–67.21%**. Map/seed observations can be correlated; this interval does
not measure Elo or guarantee performance against unseen opponents.

Weakhold returned 0–5–5: the B-side queen died against a wall on turn 188 in
each seed, while the A side drew. Stronghold, Trauma and UNSW each returned
4–6. Maze (9–1), Portals (8–2), Stripes (9–1) and Tower Defense (7–3) improved
on their earlier two-game samples, illustrating why small map samples are
insufficient for selection. Run `scripts/report.py --by-map` for the full table.

Tracing the deterministic Weakhold seed505 B-side loss found the queen moving
from (29,1) north to (29,0), then west along the corridor to (24,0), splitting
on turns186 and187, and dying on turn188. On UNSW, it moved from (43,21) west
to (41,21), north to (41,20), east to (42,20), split on turn4, and died on
turn5. These are corridor traps rather than illegal actions. This motivates
testing lookahead and growth changes against the current champion.

The original repository baseline is not confirmed as the active online bot.
Dev has paused website sign-in and requested GitHub publication of verified
improvements. Further policy promotions require fresh evidence against the
previous champion; these five seeds must no longer be treated as unseen.

## Follow-up experiments and selected Weakhold repair

Broad policy changes were screened against `final`, the first vision6/split3
champion from `1d622384`. These screens are tuning evidence, not final gates.

| Policy | Wins vs champion | Losses vs champion | Draws | Evidence |
| --- | ---: | ---: | ---: | --- |
| Head-destination threat penalty | 21 | 23 | 0 | All 22 maps, both sides, seed 1111 |
| Three-step simple-path lookahead | 22 | 22 | 0 | Same 44-game screen |
| Both changes together | 22 | 22 | 0 | Same 44-game screen |
| Vision weight 9 | 23 | 19 | 2 | All 22 maps, both sides, seed 1212 |
| Free pearl sprint, all dragons | 31 | 13 | 0 | Same 44-game screen |
| Free pearl sprint, queens only | 23 | 21 | 0 | All 22 maps, both sides, seed 1616 |

The all-dragon sprint was then compared on fresh seeds 1313 and 1414 over all 22
maps and both sides: **44–44 against the champion**. It is not promoted. The
separate original-baseline comparison is in the same `sprint-validation` file;
beating that weaker bot alone would not qualify a replacement for the champion.
Its UNSW sandbox success and 24.5M peak CPU cost validate execution, not strength.
The sprint's separate original-baseline result was 52–34–2; the champion
comparison is the reason it remains disabled. The head-avoidance/lookahead experiment is reproducible by applying
`research/survival-variants.patch` with `git apply --unidiff-zero` to `1d622384` and using the added build flags:
head weight 4000, path weight 3000, or both. These additions are not in the active
bot. Queen-only sprint is available as `--free-sprint 2` but remains disabled.
To reproduce these pre-repair screens from the current source, set the
Weakhold weight equal to the selected vision weight (6, or 9 for the weight 9 bot).

The selected change instead disables the vision bonus only on Weakhold's 40×15
geometry. Split limits, movement safety and all other map policies retain the
champion's behavior. The Weakhold screen (seeds 1818, 1919, 2020, 2121 and 2222) returned **5–0–5**.
The separate fresh Weakhold check (2424, 2525, 2626, 2727 and 2828) also returned **5–0–5**. The
repaired queen survived with length 4; the prior B-side queen hit a wall on turn 188.

The fresh all-map regression seed 2323 returned **22–21–1**. For each of the
21 other maps, both candidate sides were compared with one canonical game of
champion vs champion on the same seed. All **42** non-Weakhold games exactly
matched engine result, deaths, queen inputs/outputs at death, population peaks,
faults and notices. `weakhold-routing-control-check.json` records the compared
fields and input hashes. This supports a narrowly scoped repair; it does not
claim the all-map score establishes a broad >60% improvement. A fresh all-map
test against the original baseline (seed 3030) returned **24–18–2**.

The selected policy completed a Weakhold judge-sandbox match (seed 2929),
winning with queen 4 vs 0. Its peak was **14.5M CPU points/turn**, below 100M.
The final source builds a native executable with the same SHA256 as the tested
variant: `5f57c816de5ea0844b3460449407d7a1569d080a93e8e506f2affe5a6dc62b18`.
Sandbox summaries are in `weakhold-sandbox.json` and `sprint-sandbox.json`.

Some long batches ended before their intended matrix completed, without a
useful Python exception. They were resumed using identical manifests and
binaries, retaining completed games and checking for missing/duplicate cases.
The runner now gives each match its own subprocess with a five-minute limit;
supervisor threads never run Wasmtime engines. Always run `check_records.py`
before counting a matrix as a completed gate. No missing game counts as a win.

## Records

Each `*.jsonl` file has a matching `*.manifest.json` with binary hashes and
the intended matrix. Records include outcome, official queen/longest/total
scores, death counts, queen death rounds, population peaks and runtime faults.
Later batches also retain each queen's last input and output at death.
Loss replays were generated locally under `.experiments/`; the structured
diagnostics are committed here. Paths in records describe the original run.

`vision-screen` initially stopped after 31 records without a Python exception.
Its missing games were completed with an identical manifest using isolated
process workers. The benchmark now uses that isolation and checks batch
completion. No missing match was counted as a win.

Sandbox checks completed on Arena and Big Empty. The selected vision policy's
Big Empty maximum was 23.8M points/turn (100M limit); it lost that particular
game to the baseline. A sandbox run validates execution, not strategy strength.

The legacy root Python tests already fail on their population-target assertion
in the untouched root bot. The C++ corner-split and new vision/counter tests
pass. No competition account was available, so no current online replay audit,
submission, activation or measured Elo improvement is claimed.
