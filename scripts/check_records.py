#!/usr/bin/env python3
"""Reject incomplete, duplicated, mismatched or invalid benchmark matrices."""
import argparse
import itertools
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('files', nargs='+')
args = parser.parse_args()
failed = False
for filename in args.files:
    path = Path(filename)
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    manifest = json.loads(path.with_suffix('.manifest.json').read_text())
    # Record paths refer to the original machine; match their terminal names.
    expected = set(itertools.product(
        [Path(p).name or Path(__file__).resolve().parents[1].name for p in manifest['candidates']],
        [Path(p).name or Path(__file__).resolve().parents[1].name for p in manifest['opponents']],
        manifest['maps'], manifest['seeds'], manifest.get('sides', ['A', 'B'])))
    actual = [(Path(r['candidate']).name, Path(r['opponent']).name,
               r['map'], r['seed'], r['side']) for r in rows]
    errors = []
    if len(rows) != manifest['games'] or set(actual) != expected:
        errors.append(f"matrix has {len(rows)}/{manifest['games']} records; "
                      f"{len(expected-set(actual))} missing, {len(set(actual)-expected)} unexpected")
    if len(actual) != len(set(actual)):
        errors.append('duplicate map/seed/side records')
    for r in rows:
        if not r.get('valid') or r.get('faults'):
            errors.append('runtime or invalid-action failure')
            break
        winner = r['result']['winner']
        outcome = 'draw' if winner is None else 'win' if winner == r['side'] else 'loss'
        if r['outcome'] != outcome:
            errors.append('outcome disagrees with engine winner')
            break
    if errors:
        failed = True
        print(f"FAIL {path}: {'; '.join(errors)}")
    else:
        print(f'PASS {path}: {len(rows)} complete, unique, valid matches')
raise SystemExit(1 if failed else 0)
