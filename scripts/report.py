#!/usr/bin/env python3
"""Summarize completed match records; never count runtime faults as wins."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('files', nargs='+')
parser.add_argument('--by-map', action='store_true')
args = parser.parse_args()
records = []
for file in args.files:
    records.extend(json.loads(line) for line in Path(file).read_text().splitlines())
keys = ('candidate', 'opponent', 'map') if args.by_map else ('candidate', 'opponent')
print('| Candidate | Opponent | ' + ('Map | ' if args.by_map else '') + 'Games | Wins | Losses | Draws | Invalid | Score | Decisive win 95% CI |')
print('| --- | --- | ' + ('--- | ' if args.by_map else '') + '---: | ---: | ---: | ---: | ---: | ---: | --- |')
for identity in sorted({tuple(r[k] for k in keys) for r in records}):
    candidate, opponent = identity[:2]
    group = [r for r in records if tuple(r[k] for k in keys) == identity]
    outcomes = Counter(r['outcome'] for r in group if r['valid'])
    n = outcomes['win'] + outcomes['loss']
    valid = n + outcomes['draw']
    score = f"{100*(outcomes['win'] + .5*outcomes['draw'])/valid:.2f}%" if valid else 'n/a'
    interval = 'n/a'
    if n:
        p, z = outcomes['win']/n, 1.96
        centre = (p + z*z/(2*n))/(1+z*z/n)
        radius = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/(1+z*z/n)
        interval = f'{100*(centre-radius):.2f}–{100*(centre+radius):.2f}%'
    map_cell = f'{identity[2]} | ' if args.by_map else ''
    print(f"| {Path(candidate).name} | {Path(opponent).name} | {map_cell}{len(group)} | {outcomes['win']} | {outcomes['loss']} | {outcomes['draw']} | {sum(not r['valid'] for r in group)} | {score} | {interval} |")
if not args.by_map:
    print('\nScore counts draws as half a win; Wilson intervals exclude draws. These describe local match outcomes, not Elo or guaranteed performance on other maps/opponents. Map/seed pairs can be correlated.')
