import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.benchmark import invalid_action_diagnostic, replay_bot_label


def main():
    turn = {'input': 'ROUND 7\n', 'output': 'MOVE N\nENDTURN\n'}
    assert invalid_action_diagnostic(12, 'B', 7, turn) == {
        'id': 12, 'team': 'B', 'round': 7, 'last_turn': turn,
    }
    assert invalid_action_diagnostic(3, 'A', 9, None)['last_turn'] is None

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        first = root/'alpha'/'.unswbc-build'/'bot'
        second = root/'beta'/'.unswbc-build'/'bot'
        first.parent.mkdir(parents=True)
        second.parent.mkdir(parents=True)
        first.write_bytes(b'first binary')
        second.write_bytes(b'second binary')
        first_label = replay_bot_label(first)
        second_label = replay_bot_label(second)
        assert first_label.startswith('alpha-')
        assert second_label.startswith('beta-')
        assert first_label != second_label
        assert first_label == replay_bot_label(first)


if __name__ == '__main__':
    main()
