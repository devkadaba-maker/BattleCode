#!/usr/bin/env python3
"""Paired, seeded matches using the official engine (unswbc==1.2.9).

Build C++ binaries once before running. Each candidate gets both starting sides
on every map/seed. Native results screen strategy; --sandbox CLI matches are
still required before promotion. Runtime faults invalidate a game.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
import hashlib
import json
import multiprocessing
from pathlib import Path
import sys
import time

from unswbc.bot import Bot, Pool
from unswbc.engine import EngineModule
from unswbc.run import _resolve

ROOT = Path(__file__).resolve().parents[1]


def match(candidate, opponent, map_path, seed, side, replay_dir=None):
    paths = {side: candidate, ('B' if side == 'A' else 'A'): opponent}
    pools, live, teams = {}, {}, {}
    deaths = {'A': Counter(), 'B': Counter()}
    queen_deaths, queen_turns, faults, notices = {}, {}, [], []
    peaks = {'A': 0, 'B': 0}
    started = time.monotonic()
    engine = EngineModule()
    try:
        for team, path in paths.items():
            argv, cwd, kind = _resolve(str(path))
            pools[team] = Pool(argv, cwd=str(cwd), size=2)

        def spawn(dragon_id, init):
            team = next(line.split()[1] for line in init.decode().splitlines()
                        if line.startswith('TEAM '))
            teams[dragon_id] = team
            live[dragon_id] = Bot(pools[team], init=init, name=str(dragon_id))
            peaks[team] = max(peaks[team], sum(teams[i] == team for i in live))

        def reply(dragon_id, block):
            bot = live[dragon_id]
            response = bot.ask(block)
            if dragon_id < 2:
                queen_turns[teams[dragon_id]] = {'input': block.decode(errors='replace'),
                                               'output': response.decode(errors='replace')}
            if bot.error is not None:
                faults.append({'id': dragon_id, 'team': teams[dragon_id], 'error': str(bot.error)})
            return response

        def death(dragon_id, round_num, reason):
            deaths[teams[dragon_id]][reason] += 1
            if dragon_id < 2:
                queen_deaths[teams[dragon_id]] = {'round': round_num, 'reason': reason,
                                                 'last_turn': queen_turns.get(teams[dragon_id])}
            bot = live.pop(dragon_id, None)
            if bot:
                bot.stop()

        result = engine.run(Path(map_path).read_bytes(), reply, death, spawn,
                            notices.append, debug=0, seed=seed)
        outcome = 'draw' if result.winner is None else 'win' if result.winner == side else 'loss'
        record = dict(candidate=str(candidate), opponent=str(opponent), map=Path(map_path).stem,
                      seed=seed, side=side, outcome=outcome,
                      valid=not faults and not any(counts.get('A', 0) for counts in deaths.values()),
                      result=asdict(result), deaths={t: dict(c) for t, c in deaths.items()},
                      queen_deaths=queen_deaths, peak_population=peaks, faults=faults,
                      notices=notices, seconds=round(time.monotonic()-started, 3))
        if replay_dir and outcome == 'loss':
            replay_dir = Path(replay_dir)
            replay_dir.mkdir(parents=True, exist_ok=True)
            name = f'{Path(candidate).name}-{Path(opponent).name}-{Path(map_path).stem}-{seed}-{side}.replay'
            (replay_dir/name).write_bytes(engine.replay(str(paths['A']), str(paths['B'])))
            record['replay'] = str(replay_dir/name)
        return record
    finally:
        for bot in live.values():
            bot.stop()
        for pool in pools.values():
            pool.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidates', nargs='+', required=True)
    parser.add_argument('--opponents', nargs='+', required=True)
    parser.add_argument('--maps', nargs='+', default=['arena','default_small','default','big_empty','schooltime','trophy','Colosseum','queen_of_spades'])
    parser.add_argument('--seeds', nargs='+', type=int, default=[101])
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--output', required=True)
    parser.add_argument('--loss-replays')
    parser.add_argument('--resume', action='store_true', help='Continue an interrupted batch with the identical manifest')
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    jobs = [(str(Path(c).resolve()), str(Path(o).resolve()), ROOT/'maps'/f'{m}.map', seed, side)
            for c in args.candidates for o in args.opponents for m in args.maps
            for seed in args.seeds for side in ('A','B')]
    metadata = {'toolkit': '1.2.9', 'candidates': args.candidates, 'opponents': args.opponents,
                'maps': args.maps, 'seeds': args.seeds, 'games': len(jobs),
                'sha256': {str(p): hashlib.sha256(Path(p).read_bytes()).hexdigest()
                           for p in args.candidates + args.opponents if Path(p).is_file()}}
    records = []
    manifest = output.with_suffix('.manifest.json')
    if args.resume and output.exists():
        if not manifest.exists() or json.loads(manifest.read_text()) != metadata:
            parser.error('resume requires the identical candidates, binaries, maps and seeds')
        records = [json.loads(line) for line in output.read_text().splitlines()]
        done = {(r['candidate'],r['opponent'],r['map'],r['seed'],r['side']) for r in records}
        jobs = [j for j in jobs if (j[0],j[1],j[2].stem,j[3],j[4]) not in done]
    else:
        manifest.write_text(json.dumps(metadata, indent=2)+'\n')
    total = metadata['games']
    # Each worker owns an engine and its bot processes. Do not run multiple
    # Wasmtime engines from threads in one Python process.
    with output.open('a' if args.resume else 'w') as log, ProcessPoolExecutor(
            max_workers=args.workers, mp_context=multiprocessing.get_context('spawn')) as executor:
        futures = {executor.submit(match, *job, args.loss_replays): job for job in jobs}
        for future in as_completed(futures):
            job = futures[future]
            try:
                record = future.result()
            except Exception as error:
                record = {'candidate':job[0], 'opponent':job[1], 'map':job[2].stem,
                          'seed':job[3], 'side':job[4], 'valid':False, 'error':str(error)}
            records.append(record)
            log.write(json.dumps(record)+'\n')
            log.flush()
            print(f"[{len(records)}/{total}] {Path(job[0]).name} vs {Path(job[1]).name} {job[2].stem} seed={job[3]} side={job[4]}: {record.get('outcome', record.get('error'))}", flush=True)
    for candidate in args.candidates:
        valid = [r for r in records if r['candidate']==str(Path(candidate).resolve()) and r['valid']]
        tally = Counter(r['outcome'] for r in valid)
        print(Path(candidate).name, dict(tally), f"{len(valid)} valid games")
    return 0 if len(records) == total and all(r['valid'] for r in records) else 1


if __name__ == '__main__':
    sys.exit(main())
