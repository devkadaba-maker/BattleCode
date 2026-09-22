# UNSW Battlecode Python sonar bot

The production bot is `main.py`; `helper.py` implements the engine protocol.
Run commands from this directory:

```sh
unswbc run maps/default.map . .
unswbc run maps/default.map . practice_bot
```

The strategy combines a protected flagship swarm with 50/50 collector and
hunter roles. It uses pearl seeking, flood-fill and mobility safety checks,
controlled splitting, late survival priorities, and compact validated sonar
target reports. Sonar is only a hint: local occupancy, turn order, and reachable
space checks always take priority. Portal use remains conservative.

## Final acceptance matrix

The fixed matrix contains 20 games per opponent, with no timeouts or crashes:

| Opponent | Wins | Losses | Rate |
| --- | ---: | ---: | ---: |
| baseline | 20 | 0 | 100% |
| practice | 18 | 2 | 90% |
| hard | 17 | 3 | 85% |
| hard v2 | 20 | 0 | 100% |
| unseen | 20 | 0 | 100% |

All five opponents pass the 80% acceptance gate. The 100 replay files and the
full report are in `replays/sonar-final/`:

- `easy (100%)/`
- `medium (90%)/`
- `hard (85%)/`
- `hard v2 (100%)/`
- `unseen (100%)/`
- `full-report.txt`

Each score-labelled folder contains 20 numbered `.replay` files. A copy is
also stored at `~/Desktop/applications/battlecode/replays/sonar-final/`.

## Verification

From `BattleCode/`:

```sh
python3 tests/test_strategy.py
python3 -m py_compile main.py helper.py
git diff --check
graft build
```

These final gates passed after the acceptance matrix. Replay validation was
structural and marker-scanned; visual viewer inspection remains optional.
