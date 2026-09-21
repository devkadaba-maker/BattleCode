# BattleCode Python Flagship Bot

This is a Python-only UNSW Battlecode bot project. Run it from this directory:

```sh
unswbc run maps/default.map . .
```

The bot uses the flagship-and-scout strategy: a map-size target of 30–60
dragons, four or five protected flagship roles, pearl-guided movement,
visible-area flood fill, collision avoidance, controlled splitting, and late
survival behaviour.

## C++ parity proof

`tests/test_strategy.py` verifies the Python population targets, flagship
targets, and 32-bit role hash against values emitted by the C++ reference.

```sh
python3 tests/test_strategy.py
```

Engine verification also produced identical C++ and Python outcomes against
the starter bot:

| Map | Peak dragons | Self-collisions | Result |
| --- | ---: | ---: | --- |
| Default 32×32 | 60 vs 4 | 8 | Team A wins on round 453 |
| Trophy 25×25 | 53 vs 2 | 4 | Team A wins on round 239 |

The matching Python replays are in `replays/`.

## Medium practice opponent

`practice_bot/` is a stronger Python opponent built from the same safety,
flood-fill, pearl-scoring, and collision logic. It expands to roughly 12–32
dragons, protects a small flagship group, and sends short-lived scouts toward
safe head trades when turn order makes them favourable.

Run a practice match with:

```sh
unswbc run maps/default.map . practice_bot
```

The numbered replay sets are named `1 (easy).replay` through
`20 (easy).replay` and `1 (medium).replay` through `20 (medium).replay`.
The medium batch produced 15 wins from 20 matches (75%).
