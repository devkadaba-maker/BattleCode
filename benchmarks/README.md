# October 4, 2026 experiments

Engine/toolkit: `unswbc==1.2.9`; current bundled maps; native C++ built with
`g++ -std=c++20 -O2`. Recorded matches are checked against their full manifests
with `scripts/check_records.py`, including uniqueness and engine-winner consistency.
All 1,773 accepted records form complete matrices with no invalid actions
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

## Queen escape experiment against champion 43ebea6

A new six-move simple-path search scores queen exits while excluding the
new body trail and the visible straight-ahead destinations of other heads.
It applies to queens only and contributes to emergency movement as well as
normal movement. The archived patch uses weight 4000. An opening-only version
stops after turn 15; the longer version remains active through turn 499.
The forecasts are conservative fixed obstacles, not a complete simulation of
body motion or opponent decisions; unseen continuations are optimistic.

The opening-only UNSW screen (seeds 3434 and 3535, both sides) returned
**1–3** despite saving every queen from the original turn-5 trap. Their later
deaths were on turns 95, 106, 280 and 483. Keeping the check active throughout
the game returned **3–1** on the same tuning games. The global longer policy
returned **7–7** on seven screening maps at seed 3434, then **26–16–2** on all
22 maps at seed 3939. None of these games enters the final gate.

The frozen global candidate's separate fresh gate (3636 and 3737; all 22 maps,
both sides) returned **50 wins, 34 losses and 4 draws**, a **59.09% score**.
Its decisive-game Wilson 95% interval is **48.83–69.38%**. It misses both the
60% score target and the lower-bound-above-50% target. **Do not promote it.**
The active bot remains exactly the 43ebea6 champion. A result against the
original baseline or a historical Python opponent does not override this gate.

Default, Maze, Slithery Fight and Stripes each returned 1–3 in the fresh gate;
Tower Defense returned 3–1 after a 2–0 screen. Devil and Default Small, each
0–2 in the all-map screen, returned 2–2 in the fresh gate. The saved Devil
trace shows the candidate queen traversing a border pocket on turns 78–86
and dying against a wall at (0,15). Short lookahead cannot guarantee a future
exit, particularly with changing bodies and a limited view. Future work should
model when occupied segments vacate and examine congestion before entering
corridors; this evidence does not justify selectively disabling losing maps.

Judge sandbox checks completed on UNSW (scope limited to UNSW, seed 3838;
24.5M maximum points/turn) and Devil (global candidate, seed 4141; 22.0M), both
below the 100M limit. These execution checks do not establish strategy strength.
`queen-escape-decision.json` records the rejected candidate and exact binary
hashes. Its SHA256 is
`351f8e5098b3d831ed0be1e6d4a8738391b3babeb3658c353518483be45a16d0`;
the retained champion is
`5f57c816de5ea0844b3460449407d7a1569d080a93e8e506f2affe5a6dc62b18`.

To reproduce, check out 43ebea6 and apply `research/queen-escape.patch` with `git apply --unidiff-zero`, then
materialize with `--queen-escape-weight 4000 --queen-escape-rounds 500
--queen-escape-scope 0`. Scope 1 restricts it to UNSW's 64×64 dimensions;
rounds 16 reproduces the opening-only screen. Compile the archived
`research/queen-escape-smoke.cpp` after applying the patch; it checks a dead-end
versus a longer exit and friendly/enemy head forecasts. This smoke check passed.
The active source has no enabled escape-policy changes.

Two incorrectly specified map arguments failed before matches could start and
are excluded from evidence. Their failed request logs remain local. Valid games
from the second request were retained, the intended seven-map manifest corrected,
and its three missing matches resumed. The runner now rejects unknown map names
before writing a manifest or starting any engine. Every counted matrix must pass
`check_records.py`; incomplete batches are never accepted as evidence.

The separate diverse-opponent batch at seed 4040 covered all 22 maps and both
sides: **27–15–2** against the original C++ baseline and **36–6–2** against
historical hard Python v2. All 242 matches in this iteration's six matrices
are complete, unique and free of bot runtime faults or invalid actions.
Together with prior evidence, 1,347 matrix records pass `check_records.py`.
The original source is retained, and the rejected patch can reproduce its
exact tested native SHA256. No website submission or measured Elo change is
claimed.

## UNSW follow-up: scope, duration and moving-body estimates

The next screen restricted queen escape to UNSW's 64×64 geometry, using
both sides of seeds 4242, 4343, 4444, 4545 and 4646. These seeds are now tuning
evidence, including all later parameter trials; they are not fresh validation.
The comparison remained the unchanged champion from 43ebea6.

| Queen escape policy | Wins | Losses | Draws | Games |
| --- | ---: | ---: | ---: | ---: |
| UNSW only, weight 4000, through turn 499 | 4 | 6 | 0 | 10 |
| UNSW only, weight 250, through turn 499 | 2 | 8 | 0 | 10 |
| UNSW only, weight 750, through turn 499 | 4 | 6 | 0 | 10 |
| UNSW only, weight 1500, through turn 499 | 4 | 6 | 0 | 10 |
| UNSW only, weight 4000, turn 0 only | 5 | 5 | 0 | 10 |
| UNSW only, weight 4000, turns 0–1 | 3 | 7 | 0 | 10 |
| UNSW only, weight 4000, turns 0–3 | 3 | 7 | 0 | 10 |
| Moving-body estimate, weight 750, through turn 499 | 4 | 6 | 0 | 10 |
| Moving-body estimate, weight 4000, through turn 499 | 4 | 6 | 0 | 10 |

None qualifies for a fresh validation gate or promotion. Restricting the failed
global policy to UNSW did not establish a repair, and lowering its weight or
duration did not solve the tradeoff. The persistent static policy saved all
ten queens from the original turn-5 death, yet still lost more final games.
Queen survival alone is an insufficient selection criterion.

`research/queen-escape-unsw-20-trace.json` retains preceding turns from the
seed 4444 B-side loss. After surviving the opening, its queen zigzagged from
(47,21) on turn 12 to (49,18) on turn 17, moved west twice to (47,18), split
on turn 19, and died against a wall on turn 20. Saving the original opening
does not prevent a later corridor trap.

The moving-body experiment reconstructs visible body order by following each
segment's arrow towards its predecessor, including bends. Its depth search
permits old body and earlier path squares only after a conservative release
estimate plus one extra move; pearls and predicted spawns delay that release.
Unknown segments stay blocked. Other dragons' visible bodies and predicted
straight head destinations remain fixed obstacles. Immediate moves still use
the champion's safety checks; the prediction changes route ranking only.

An initial straight-chain reconstruction was superseded before selection. Its
20 complete diagnostic games contained three invalid-action games, including
an invalid action by the opponent in two of them, with no process faults.
Those records and their exact manifests are preserved in `research/failed/`
and are excluded from accepted evidence. A traced repetition of seed 4242 A
did not reproduce the invalid action; that repetition is diagnostic, not a
replacement for the failed record. The cause remains unresolved. The corrected
bend reconstruction's separate 20-game screen was complete and fault-free,
but both weights still returned 4–6. Neither prototype is enabled.

Apply `research/queen-body-release.patch` to 43ebea6 with
`git apply --unidiff-zero`, then use `--queen-escape-weight 750` (or 4000),
`--queen-escape-rounds 500 --queen-escape-scope 1 --queen-escape-release 1`.
The archived smoke test checks body order through bends, a route opened by
body release, and pearl growth closing that route; it passed. The earlier
prototype is reproducible with `research/queen-body-release-straight.patch`.
Static scope/weight/duration trials use the existing `queen-escape.patch`.
Binary hashes and exact outcomes are in `queen-unsw-followup-decision.json`
and each matrix manifest.

This follow-up adds 90 complete, valid screening games and 20 failed-matrix
diagnostic games. There was no new sandbox run or final validation because
all candidates failed screening. All 1,437 accepted matrix records pass
`check_records.py`; the failed diagnostic matrix intentionally fails that check.
The active source and native champion hash remain unchanged. Future work
should examine the limited-view assumption at corridor entry and collisions
with moving teammates, rather than promoting the static forecast family.

## Saturated escape-budget screen — champion retained

The next hypothesis capped the queen's escape-depth reward once a route had
enough steps, preserving the champion's food/congestion ordering among equally
adequate routes. Both candidates kept the earlier six-step search, own-trail
exclusion and fixed straight-head forecasts. One saturated at three moves;
the other at `min(6, length + 1)`. These were global policies with weight 4000
through turn 499, without moving-body release.

`queen-threshold-screen.jsonl` contains all 22 official maps, both sides,
seed 4747, against the current champion from 43ebea6: 88 complete, unique,
valid games. This seed is now tuning evidence, not unseen validation.

| Policy | Wins | Losses | Draws | Score | Decisive Wilson 95% |
| --- | ---: | ---: | ---: | ---: | --- |
| Three-step saturation | 16 | 26 | 2 | 38.64% | 25.00–53.19% |
| Body-length saturation | 22 | 20 | 2 | 52.27% | 37.72–66.64% |

Neither warrants a fresh promotion gate. Both lost both sides on Big Empty,
Default, Dilemma, Islands and Stripes. Body-length saturation also lost both
sides on Arena and Slithery Fight. Its two Colosseum wins did not preserve the
queens: they died on turns 81 and 56. Do not select a map-specific repair from
that two-game result without a diagnosed repair and separate fresh controls.
There was no new sandbox or diverse-opponent gate because screening failed.
The active bot's source and native hash remain unchanged.

The three-step Colosseum A-side loss was reproduced exactly, including scores,
deaths, queen inputs/outputs, population peaks and notices. Its queen was at
(14,13), length 8, on turn 83; it moved to the right edge, down, left, down,
and right into (15,15) on turn 88. It split on turns 88–90 and died against the
wall on turn 91. At turn 83 only the east step was immediately safe; by turn
86 both west and south had only two moves in the static forecast. The fatal
corner must be prevented earlier than the final wall move. This trace does
not establish that a longer static horizon would succeed.

`scripts/trace_loss.py` now reproduces a selected matrix row using its exact
native binary hashes and the pinned toolkit. It retains queen spawn data and
the preceding eight rounds, compares the full game diagnostics with the
original row, and labels the output as a diagnostic rerun excluded from matrix
evidence. It rejects ambiguous selections, missing/mismatched binaries and
existing output files. The Colosseum reproduction matched exactly; ambiguity
and binary-mismatch rejection checks passed. Example:

```sh
.venv/bin/python scripts/trace_loss.py benchmarks/queen-threshold-screen.jsonl --candidate escape-threshold3 --map Colosseum --seed 4747 --side A --output .experiments/colosseum-diagnostic.json
```

The retained reproduction is `research/queen-threshold-colosseum-reproduction.json`.
Apply `research/queen-threshold.patch` to 43ebea6 with `git apply --unidiff-zero`, then build
with `--queen-escape-weight 4000 --queen-escape-rounds 500 --queen-escape-scope 0`
and `--queen-escape-threshold 1` or `2`. Both native binaries were reproduced
byte-for-byte from the archived patch. The smoke test passed for both modes,
checking saturation, the queen-only scope and friendly/enemy head forecasts.
Exact hashes, build flags, outcomes and decision are in `queen-threshold-decision.json`.

This screen adds 88 accepted records, bringing the complete valid matrices to
1,525 games. The 20 previously failed diagnostic records remain separate and
unchanged. Future work should test a materially different corridor-entry or
teammate-motion hypothesis rather than retune the rejected depth-reward family.

## Pre-emptive queen split — fresh validation failed

The original UNSW trace showed a precise timing failure. On turn 3 the queen
had one legal exit and that exit had no onward move. It entered the exit, then
split on turn 4 only after becoming completely boxed in, and died against a
wall on turn 5. This experiment split two tail segments one turn earlier when
that condition was visible. It applied only to queens, required length at least
four, and retained both the parent and queen split caps.

Two modes were selected on UNSW seeds 4848, 4949, 5050, 5151 and 5252, both
sides. The strict zero-onward trigger scored **6–4**; a broader trigger that
also treated one onward move as dangerous scored **5–5**. These are tuning
results. The strict trigger's all-map tuning batch on seed 5353 returned
**21–19–4**, a 52.27% score. It did not justify a broad promotion gate.

The strict policy was then frozen behind the official UNSW queen spawn
signature so other maps could not activate it. On five fresh seeds 5454,
5555, 5656, 5757 and 5858, both sides, it returned **4 wins and 6 losses**.
It therefore failed scoped validation and was not promoted. No sandbox,
diverse-opponent or unaffected-map equivalence gate was run after that failure.

The intervention did repair the immediate deterministic symptom: in the fresh
batch the candidate queen survived beyond turn 5 in every game and died in nine
of ten games only on turns 78–415, while the champion opponent's queen usually
died on turn 5. That survival did not translate into stronger final outcomes.
This is why queen lifespan alone is not used as the selection metric.

All 74 records across the three matrices are complete, unique and valid. An
interrupted all-map file contained only 25 of 44 records despite completed
progress output; it was resumed with the exact manifest and binaries before
being counted. The active champion remains unchanged. Apply
`research/queen-preemptive-split.patch` to 43ebea6 using
`git apply --unidiff-zero` for global modes 1/2, or the separate
`research/queen-preemptive-split-unsw.patch` for scoped mode 3. All three native
binaries were reproduced byte-for-byte. The archived smoke test verifies the
strict trigger, a route with an onward move, the split cap and queen-only scope.
Exact hashes, manifests, per-map results and limitations are in
`queen-preemptive-split-decision.json`.

This iteration brings the accepted complete matrices to 1,599 games. Seeds
4848 through 5858 listed in the decision file are now seen evidence. Future
work should address why long-lived queens still lose growth races rather than
retuning this rejected split timing rule.

## Queen split cap two — failed diagnostic matrix

The next growth hypothesis tested whether a queen should stop after two planned
splits rather than the champion's three. The candidate changed only
`QUEEN_SPLIT_LIMIT` from 3 to 2 and was screened against the unchanged champion
on all 22 official maps, both starting sides, with tuning seed 5959.

The 44-row matrix is not accepted strength evidence. Its Slithery Fight A-side
game recorded an invalid action on the candidate side (death code `A`) despite
no process fault. Among the 43 valid rows, the candidate returned **21 wins,
20 losses and 2 draws**, a 51.16% score. That valid subset is reported for
transparency only; removing a failed row does not repair the matrix or establish
an improvement.

`scripts/trace_loss.py` reran the exact failed case after checking both native
hashes and the pinned toolkit. The rerun was valid but changed from the recorded
candidate win to a candidate loss, with different result and death diagnostics.
It therefore did not reproduce the fault and is not a substitute observation.
The failed matrix and manifest are preserved in `research/failed/`, while the
rerun is `research/queen-split2-invalid-reproduction.json`.

The tested binary SHA256 is
`440f931317c8c53b20c3f07e2e25e902b53477d3cb9b38d0a3cf7531d81599ba`.
Rebuilding from the champion source with `--queen-split-limit 2` reproduced it
byte-for-byte. No fresh validation, diverse-opponent batch or judge sandbox was
run after the screen failed. Seed 5959 is now seen tuning evidence. The accepted
corpus remains 1,599 complete fault-free records; the failed diagnostic corpus
now contains 64 matrix rows. Exact details are in
`queen-split2-decision.json`. The cap-three champion remains active.

## Large-map population target — tuning rejected

The next experiment varied the planned population ceiling on maps larger than
1,000 tiles. The champion uses 40. Targets 32, 44 and 48 were compared against
that unchanged champion on Maze, Stronghold, Trauma, Slithery Fight, Islands,
Schooltime, Australia, Big Empty and UNSW, from both sides of tuning seed 6060.
Maps of 1,000 tiles or fewer were unaffected by the parameter and were not
replayed in this screen.

| Large-map target | Wins | Losses | Score | Mean total-length delta | Mean longest delta |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 32 | 8 | 10 | 44.44% | -6.44 | -4.33 |
| 44 | 7 | 11 | 38.89% | +20.89 | -1.22 |
| 48 | 9 | 9 | 50.00% | +3.44 | +1.00 |

All 54 games are complete, unique and valid. The lower ceiling lost both sides
on Maze and Big Empty. Target 44 lost both sides on Islands, Australia and Big
Empty. Target 48 won both sides on Islands, Big Empty and UNSW, but lost both
sides on Stronghold, Schooltime and Australia. These two-game map results are
diagnostic only and are too small to justify map-specific selection.

Higher population sometimes increased final total length without improving the
engine result. That rejects the simple assumption that more board coverage, or
more aggregate length by itself, is a sufficient strength objective. None of
the candidates advanced to fresh validation, diverse opponents or judge
sandbox. Seed 6060 is now tuning evidence.

`LARGE_POPULATION_TARGET` defaults to 40, preserving the active policy. The
default build remains byte-identical to the champion native SHA256. The build
helper accepts `--large-population-target` so all three rejected binaries are
reproducible; exact hashes and growth deltas are in
`population-target-decision.json`. The 54 valid records raise the accepted
corpus to 1,653 games. The cap-three, target-40 champion remains active.

## Friendly straight-head forecast — fresh validation failed

The next congestion hypothesis penalized a move into the square a visible
friendly head is currently pointing toward. It excludes self and enemy heads,
and unlike the earlier broad head-risk experiment it forecasts only the single
straight destination rather than every possible turn. The default penalty is
zero, preserving champion behavior.

On the standard eight-map tuning set, both sides of seed 6161, penalty 240
returned **10–6** and penalty 720 returned **11–5**. The stronger 720 binary was
frozen before fresh validation. Across all 22 official maps, both sides, fresh
seeds 6262 and 6363, it returned **40 wins, 44 losses and 4 draws**: a 47.73%
score with a decisive-game Wilson 95% interval of 37.28–58.17%. It therefore
failed both promotion thresholds.

The fresh matrix was complete, unique and fault-free. The candidate accumulated
4,292 head deaths versus 4,762 for the champion side, and 15,522 total deaths
versus 16,685. Its mean final total-length delta was +3.77, but its mean
longest-dragon delta was -0.88. Avoiding the predicted congestion improved
survival proxies while worsening the result that actually selects the bot.
Those aggregate counts are descriptive because each policy also changes the
opponent's interaction opportunities.

No diverse-opponent or judge-sandbox gate was run after fresh validation
failed. The default build remains byte-identical to the champion. The frozen
720 binary was independently reproduced with SHA256
`9ecaffb11867cfd16bdbe33af4d130d81bfbdf0ae9a0b7bb5f6464bba9ee6296`;
the 240 binary is also recorded in `teammate-destination-decision.json`. The
smoke test checks friendly, enemy and self classification. Seeds 6161, 6262 and
6363 are now seen evidence; do not retune this unchanged straight-destination
family on them.

These 120 complete valid records bring the accepted corpus to 1,773 games. The
policy is disabled and the champion remains unchanged. Future congestion work
must predict the teammate's actual scored move or coordinate reservations,
rather than assuming every head continues straight.

## Deterministic teammate priority — failed matrix

The follow-up attempted asymmetric right-of-way. When a lower-ID friendly head
could legally enter a candidate destination without reversing or using a portal,
the higher-ID snake received a movement penalty. This gives queens and older
snakes priority and avoids the symmetry of the rejected straight-head forecast.

On both sides of standard tuning seed 6464, penalty 120 returned **9–7** across
its 16 valid games. Penalty 360 returned **5–9** across 14 valid games. Its two
Schooltime rows recorded candidate wins but also opponent-side invalid actions,
one from each starting side. The complete 32-row combined matrix is therefore
invalid and is preserved in `research/failed/`; it is not accepted evidence.

Exact reruns verified the same binary hashes and toolkit. Both reruns were
valid, so neither opponent invalid action reproduced. The A-side rerun remained
a candidate win but differed in result and death diagnostics; the B-side rerun
flipped from a recorded candidate win to a loss. These diagnostic reruns do not
replace the failed rows or rescue the matrix.

The policy did not advance to fresh all-map validation, diverse opponents or
judge sandbox. The build helper retains
`--friendly-priority-claim-penalty` for reproducibility, with default zero. The
default native build remains byte-identical to the champion, and the smoke test
checks lower-ID, higher-ID and enemy classification. Exact hashes and replay
details are in `teammate-priority-decision.json`.

Seed 6464 is now seen tuning evidence. The accepted corpus remains 1,773 games.
Failed diagnostic matrices now contain 96 rows and six invalid games in total;
all stay excluded. Do not retest this unchanged priority rule or infer strength
from the valid subset.
