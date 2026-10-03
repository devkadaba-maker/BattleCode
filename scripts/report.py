#!/usr/bin/env python3
"""Summarize completed match records; never count runtime faults as wins."""
import argparse
from collections import Counter
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('files', nargs='+')
args = parser.parse_args()
records = []
for file in args.files:
    records.extend(json.loads(line) for line in Path(file).read_text().splitlines())
print('| Candidate | Opponent | Games | Wins | Losses | Draws | Invalid |')
print('| --- | --- | ---: | ---: | ---: | ---: | ---: |')
for candidate, opponent in sorted({(r['candidate'],r['opponent']) for r in records}):
    group = [r for r in records if (r['candidate'],r['opponent'])==(candidate,opponent)]
    outcomes = Counter(r['outcome'] for r in group if r['valid'])
    print(f"| {Path(candidate).name} | {Path(opponent).name} | {len(group)} | {outcomes['win']} | {outcomes['loss']} | {outcomes['draw']} | {sum(not r['valid'] for r in group)} |")
