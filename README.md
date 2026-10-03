# BattleCode bot and improvement lab

The current candidate is **`cpp_bot/`**, tested with the official `unswbc 1.2.9`
engine. The root Python bot and other Python opponents remain available for
comparison. The original C++ baseline is commit `29245ea`.

The candidate limits each parent's planned splits to **3**, then favors growth.
Emergency splits may exceed this cap when no safe move exists; they also increment
the counter. New children start their own counter because each runs a fresh bot
process. Movement evaluates reachable squares in the visible 7×7 graph using
current pearls, spawn countdowns at estimated arrival time, nearby friendly and
enemy dragons (excluding self), and actual kelp edges. Existing collision,
reachable-area and queen protections still decide whether a step is allowed.

The vision weight is **6**, with a **0-weight fallback for Weakhold's 40×15
geometry**. That fallback repairs a repeated queen death in a narrow border
corridor. Free pearl sprinting, disabling queen splits, and queen hunting were
tested but remain disabled by default.

## Setup

From a checkout, install the environment with one command (Python 3.11+):

```sh
python scripts/setup.py
```

This creates `.venv`, installs the pinned toolkit, refreshes the C++ helper and
bundled maps, and checks the machine. The toolkit carries the engine and judge
sandbox C++ compiler. On Linux/macOS the CLI is `.venv/bin/unswbc`; on Windows it
is `.venv/Scripts/unswbc.exe`. Use the web visualiser for replays if no editor
viewer is installed.

```sh
.venv/bin/unswbc run maps/arena.map cpp_bot hard_bot_v2 --sandbox --seed 505
```

## Measured results

The October 4 iteration ran **316 recorded native screening/validation games**,
all without runtime faults or invalid actions, plus two successful sandbox
matches. The selected candidate played 108 of the recorded games:

| Opponent / batch | Wins | Losses | Draws |
| --- | ---: | ---: | ---: |
| Original C++ baseline, initial eight maps / seed 101 | 14 | 2 | 0 |
| Original C++ baseline, fresh seeds 202 and 303 / eight maps | 22 | 10 | 0 |
| Original C++ baseline, 14 additional official maps / seed 404 | 12 | 15 | 1 |
| Hard Python v2 / eight maps, both sides | 16 | 0 | 0 |
| Root Python bot / eight maps, both sides | 16 | 0 | 0 |

The subsequent fresh gate played **220 games across all 22 official maps**, both
sides, using seeds 505, 606, 707, 808 and 909. The same selected policy scored
**131 wins, 84 losses and 5 draws: 60.68%** counting draws as half a win. All
games were valid. The 95% Wilson interval for wins among decisive games is
54.27–67.21%; map/seed outcomes can be correlated, so this is descriptive local
evidence rather than a guarantee about competition Elo.

This supports retaining the vision6/split3 champion over the original repository
baseline. Weakhold returned **0–5–5**, with the candidate's B-side queen trapped
and dead on turn 188 in every seed. Stronghold, Trauma and UNSW returned 4–6
each. Current online losses and active-submission status remain unavailable;
the repository baseline is not verified as the active competition submission.

The next version is a targeted Weakhold repair. Against the previous champion,
it returned **5 wins, 5 draws and no losses** on ten fresh Weakhold games. Its
all-map regression batch returned **22–21–1**: the **42 games on the other 21
maps exactly matched champion self-play controls** for scores, death counts,
queen diagnostics, population peaks and faults. A separate all-map comparison
against the original C++ bot returned **24–18–2**. The promoted native binary
is byte-identical to the tested Weakhold variant. Its Weakhold sandbox match
won with queen length 4 against 0 and a 14.5M maximum CPU-point cost per turn.

This is a map-specific repair, not a statistically established broad strength
increase over the previous champion. The fallback identifies the current
official Weakhold map by dimensions. The wider sprint variant was rejected
after a fresh **44–44** comparison against the champion despite a 31–13 screen.

The selected vision policy completed a Big Empty judge-sandbox match with a
maximum of **23.8 million CPU points per turn**, below the 100 million limit.
See [`benchmarks/README.md`](benchmarks/README.md) and raw JSONL records for all
variants, losses, seeds, sides and queen-death diagnostics.

## Repeatable experiments

Materialize and compile the unchanged baseline with the current helper:

```sh
.venv/bin/python scripts/build_variant.py baseline --ref 29245ea --compile
.venv/bin/python scripts/build_variant.py candidate --split-limit 3 --vision-weight 6 --compile
.venv/bin/python scripts/benchmark.py --candidates .experiments/candidate --opponents .experiments/baseline --seeds 505 606 --output benchmarks/next-validation.jsonl --workers 2 --loss-replays .experiments/losses
.venv/bin/python scripts/report.py benchmarks/next-validation.jsonl
.venv/bin/python scripts/check_records.py benchmarks/next-validation.jsonl
```

Each map/seed is played from both starting sides. `--resume` requires identical
inputs and binaries. Each match runs in a separate process; threads only supervise
those processes. Native games screen
strategy; judge-sandbox runs are required before an online submission. Keep
fresh seeds and comparisons against the previous champion, rather than selecting
changes solely on the tuning sample.

Use `scripts/report.py --by-map` to inspect regressions as well as the aggregate
score. New policies must beat the previous champion on fresh validation games
before replacing it. Website sign-in attempts are paused; verified improvements
and their evidence are published to the continuation GitHub branch and PR #1.

## Checks and submission

```sh
g++ -std=c++20 -O2 tests/vision_target_smoke.cpp -o /tmp/vision-test && /tmp/vision-test
g++ -std=c++20 -O2 tests/corner_split_smoke.cpp -o /tmp/corner-test && /tmp/corner-test
g++ -std=c++20 -O2 tests/free_sprint_smoke.cpp -o /tmp/sprint-test && /tmp/sprint-test
git diff --check
.venv/bin/unswbc submit cpp_bot -n vision6-split3-weakhold -d "Three planned splits; visible-graph scoring with Weakhold corridor fallback"
```

Submitting requires competition authentication. Use the CLI's secure local key
configuration or the signed-in website; never commit API keys. Check the server
build and unranked scrims before activating. No online submission or Elo change
was made during this iteration. The original Python test suite has a pre-existing
population-target assertion failure; the new C++ strategy tests pass.

The subsequent queen-escape experiment was **not promoted**. Its fresh
88-game comparison against the current Weakhold champion returned 50–34–4
(59.09%; decisive Wilson lower bound 48.83%), missing the verification target.
The champion remains unchanged. Reproducible experiment patches, loss traces,
raw records and sandbox checks are in `benchmarks/`.
