"""Native benchmark framing keeps terminators authoritative when opted in."""
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.benchmark import Bot, ExplicitEndturnBot

bot = object.__new__(ExplicitEndturnBot)
for state in ('park', 'wait', 'data', 'exit'):
    with patch.object(Bot, '_poll', return_value=state) as parent:
        assert bot._poll(0.5) == ('wait' if state == 'park' else state)
        parent.assert_called_once_with(0.5)
print('PASS explicit ENDTURN polling preserves data, wait and exit; ignores sampled park')
