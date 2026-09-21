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
