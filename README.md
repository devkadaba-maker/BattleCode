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

The vision weight is **6**. Free pearl sprinting, disabling queen splits, and
queen hunting were tested but remain disabled by default.

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

Overall against the C++ baseline: **48–27–1**. The additional-map regression is
real and should be the next tuning priority; local win rate does not establish
an increase in competition Elo. Current online losses and active-submission
status were inaccessible because the competition account was not signed in.

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
```

Each map/seed is played from both starting sides. `--resume` requires identical
inputs and binaries. Workers run in separate processes. Native games screen
strategy; judge-sandbox runs are required before an online submission. Keep
fresh seeds and comparisons against the previous champion, rather than selecting
changes solely on the tuning sample.

## Checks and submission

```sh
g++ -std=c++20 -O2 tests/vision_target_smoke.cpp -o /tmp/vision-test && /tmp/vision-test
g++ -std=c++20 -O2 tests/corner_split_smoke.cpp -o /tmp/corner-test && /tmp/corner-test
git diff --check
.venv/bin/unswbc submit cpp_bot -n vision6-split3 -d "Three planned splits per parent; visible-graph pearl/countdown scoring"
```

Submitting requires competition authentication. Use the CLI's secure local key
configuration or the signed-in website; never commit API keys. Check the server
build and unranked scrims before activating. No online submission or Elo change
was made during this iteration. The original Python test suite has a pre-existing
population-target assertion failure; the new C++ strategy tests pass.
