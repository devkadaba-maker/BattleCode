# October 4, 2026 experiments

Engine/toolkit: `unswbc==1.2.9`; current bundled maps; native C++ built with
`g++ -std=c++20 -O2`. All 316 recorded games are valid, with no invalid actions
or bot runtime faults. These are local games, not Elo measurements.

## Selection and limitations

`vision6` is the selected candidate: `PARENT_SPLIT_LIMIT=3`,
`VISION_TARGET_WEIGHT=6`, `FREE_PEARL_SPRINT=0`, `QUEEN_HUNT=0`,
`QUEEN_SPLIT_LIMIT=3`. The baseline uses `cpp_bot/main.cpp` from `29245ea`, with
the updated official helper, and the same updated maps as the candidates.

The eight screening maps are Arena, Default Small, Default, Big Empty,
Schooltime, Trophy, Colosseum and Queen of Spades. Every map/seed has both sides.
Seed 101 was used for tuning; 202 and 303 were fresh validation seeds. Fourteen
additional maps and two Python opponents were checked with seed 404. Do not
reuse these as unseen evidence in subsequent tuning.

| Variant | Baseline wins | Baseline losses | Draws | Evidence |
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

The additional maps returned 12–15–1. Losses on Maze, Portals, Stripes, Tower
Defense and UNSW occurred on both tested sides. Some queens walked into walls
after becoming trapped; some died in head collisions, and some survived but
lost on growth. The final turn is evidence of the immediate death, not proof
of the strategic cause. Follow-up work should replay the preceding turns and
test corridor survival, portal safety and spawn anticipation on fresh seeds.

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
