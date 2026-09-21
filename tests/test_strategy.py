import sys
from pathlib import Path

BOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BOT_DIR))
import helper as unswbc
import main as strategy


def main() -> None:
    assert [strategy.population_target(unswbc.Game(*case)) for case in [
        (10, 10, 64), (11, 11, 64), (16, 16, 64), (25, 25, 64), (64, 64, 48)
    ]] == [8, 30, 30, 53, 48]
    assert [strategy.flagship_target(unswbc.Game(*case)) for case in [
        (16, 16, 64), (25, 25, 64)
    ]] == [4, 5]
    assert [strategy.role_hash(dragon_id) for dragon_id in [0, 1, 2, 17, 23, 59, 60, 255]] == [
        1679741386, 3828559020, 1682401043, 3676020301, 3705810780, 3755058151, 1608800467, 577342704
    ]


if __name__ == "__main__":
    main()
