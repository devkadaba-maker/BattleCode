#!/usr/bin/env python3
"""Reproduce a recorded native match and retain the turns before queen deaths.

This is diagnostic evidence, never a replacement for the original matrix row.
The manifest's native hashes must match before any engine or bot is started.
"""
from collections import deque
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

import benchmark

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('matrix', type=Path)
    parser.add_argument('--candidate', help='Candidate filename; required if selection is ambiguous')
    parser.add_argument('--opponent', help='Opponent filename')
    parser.add_argument('--map', required=True)
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--side', choices=['A', 'B'], required=True)
    parser.add_argument('--window', type=int, default=8)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.window < 1:
        parser.error('--window must be positive')
    if args.output.resolve() == args.matrix.resolve():
        parser.error('diagnostic output must not overwrite the matrix')
    if args.output.exists():
        parser.error('diagnostic output already exists; choose a new filename')
    rows = [json.loads(line) for line in args.matrix.read_text().splitlines()]
    selected = [r for r in rows if r['map'] == args.map and r['seed'] == args.seed and r['side'] == args.side
                and (not args.candidate or Path(r['candidate']).name == args.candidate)
                and (not args.opponent or Path(r['opponent']).name == args.opponent)]
    if len(selected) != 1:
        parser.error(f'selection must identify exactly one row; found {len(selected)}')
    original = selected[0]
    manifest = json.loads(args.matrix.with_suffix('.manifest.json').read_text())
    toolkit = importlib.metadata.version('unswbc')
    if toolkit != manifest['toolkit']:
        parser.error(f'toolkit mismatch: installed {toolkit}, recorded {manifest["toolkit"]}')
    binaries, hashes = {}, {}
    for role in ['candidate', 'opponent']:
        name = Path(original[role]).name
        listed = [p for p in manifest[role+'s'] if Path(p).name == name]
        if len(listed) != 1 or listed[0] not in manifest['sha256']:
            parser.error(f'{role} needs an unambiguous frozen native binary hash')
        path = Path(original[role])
        if not path.is_file():
            path = ROOT / listed[0]
        if not path.is_file():
            parser.error(f'missing native binary: {path}')
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != manifest['sha256'][listed[0]]:
            parser.error(f'{role} binary hash does not match the recorded manifest')
        binaries[role] = str(path.resolve())
        hashes[role] = actual_hash

    if not args.worker:
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                                    *sys.argv[1:], '--worker'],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, start_new_session=True)
        try:
            output, errors = process.communicate(timeout=300)
        except subprocess.TimeoutExpired:
            if os.name == 'posix':
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            process.communicate()
            parser.exit(1, 'diagnostic match exceeded 300 seconds; original matrix unchanged\n')
        sys.stdout.write(output)
        sys.stderr.write(errors)
        return process.returncode

    traces, inits = {}, {}
    original_bot = benchmark.Bot

    class TracedBot(original_bot):
        def __init__(self, *arguments, **keywords):
            init = keywords['init'].decode()
            fields = dict(line.split(maxsplit=1) for line in init.splitlines())
            self.trace_id = int(fields['ID'])
            self.trace_team = fields['TEAM']
            if self.trace_id < 2:
                inits[self.trace_team] = init
                traces[self.trace_team] = deque(maxlen=args.window + 1)
            super().__init__(*arguments, **keywords)

        def ask(self, block):
            response = super().ask(block)
            if self.trace_id < 2:
                traces[self.trace_team].append({
                    'id': self.trace_id, 'team': self.trace_team,
                    'round': int(block.decode().splitlines()[0].split()[1]),
                    'input': block.decode(), 'output': response.decode()})
            return response

    benchmark.Bot = TracedBot
    map_path = ROOT / 'maps' / f'{args.map}.map'
    try:
        rerun = benchmark.match(binaries['candidate'], binaries['opponent'], map_path, args.seed, args.side)
    finally:
        benchmark.Bot = original_bot
    # Exclude machine paths/timing/replay filenames. Compare the full game and
    # queen diagnostics before adding the extra diagnostic fields.
    fields = ['map', 'seed', 'side', 'outcome', 'valid', 'result', 'deaths',
              'queen_deaths', 'peak_population', 'faults', 'notices']
    different = [field for field in fields if rerun.get(field) != original.get(field)]
    for team, death in rerun['queen_deaths'].items():
        death['preceding_turns'] = [turn for turn in traces[team]
                                   if death['round'] - args.window <= turn['round'] <= death['round']]
        death['init'] = inits[team]
    rerun['diagnostic'] = {
        'kind': 'reproduction; excluded from match matrix evidence',
        'matrix': str(args.matrix), 'matches_original': not different,
        'different_fields': different, 'native_sha256': hashes, 'toolkit': toolkit,
        'map_sha256': hashlib.sha256(map_path.read_bytes()).hexdigest(),
        'window': args.window}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation also protects against a concurrently produced trace.
    with args.output.open('x') as output:
        output.write(json.dumps(rerun, indent=2) + '\n')
    print(json.dumps({'outcome': rerun['outcome'], 'valid': rerun['valid'],
                      'matches_original': not different, 'different_fields': different,
                      'output': str(args.output)}))
    return 0 if not different and rerun['valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
