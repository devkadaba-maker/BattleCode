#!/usr/bin/env python3
"""Paired, seeded matches using the official engine (unswbc==1.2.9).

Build C++ binaries once before running. Each candidate gets both starting sides
on every map/seed. Native results screen strategy; --sandbox CLI matches are
still required before promotion. Runtime faults invalidate a game.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys
import signal
import subprocess
import time

from unswbc.bot import Bot, Pool
from unswbc.engine import EngineModule
from unswbc.run import _resolve

ROOT = Path(__file__).resolve().parents[1]


class ExplicitEndturnBot(Bot):
    """For bots promising ENDTURN, avoid native /proc stdin-park races.

    The official sandbox remains the execution gate. Native /proc sampling
    can observe stdin parked before a queued stdout record has been drained.
    An explicit terminator (or exit/wall timeout) is unambiguous instead.
    Opt in only for bots that emit ENDTURN after every action.
    """
    def _poll(self, timeout):
        state = super()._poll(timeout)
        return 'wait' if state == 'park' else state


def replay_bot_label(value):
    """Return a readable, collision-resistant label for a replay filename."""
    path = Path(value)
    if path.name == 'bot' and path.parent.name == '.unswbc-build':
        name = path.parent.parent.name
    else:
        name = path.stem or path.name or 'bot'
    identity = (hashlib.sha256(path.read_bytes()).hexdigest()[:12]
                if path.is_file() else hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:12])
    return f'{name}-{identity}'


def invalid_action_diagnostic(dragon_id, team, round_num, last_turn):
    """Preserve the engine input and bot output immediately before death A."""
    return {'id': dragon_id, 'team': team, 'round': round_num,
            'last_turn': last_turn}


def match(candidate, opponent, map_path, seed, side, replay_dir=None, explicit_endturn=False):
    paths = {side: candidate, ('B' if side == 'A' else 'A'): opponent}
    pools, live, teams = {}, {}, {}
    deaths = {'A': Counter(), 'B': Counter()}
    queen_deaths, queen_turns, last_turns, invalid_actions, faults, notices = {}, {}, {}, [], [], []
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
            bot_type = ExplicitEndturnBot if explicit_endturn else Bot
            live[dragon_id] = bot_type(pools[team], init=init, name=str(dragon_id))
            peaks[team] = max(peaks[team], sum(teams[i] == team for i in live))

        def reply(dragon_id, block):
            bot = live[dragon_id]
            response = bot.ask(block)
            turn = {'input': block.decode(errors='replace'),
                    'output': response.decode(errors='replace')}
            last_turns[dragon_id] = turn
            if dragon_id < 2:
                queen_turns[teams[dragon_id]] = turn
            if bot.error is not None:
                faults.append({'id': dragon_id, 'team': teams[dragon_id], 'error': str(bot.error)})
            return response

        def death(dragon_id, round_num, reason):
            deaths[teams[dragon_id]][reason] += 1
            if reason == 'A':
                invalid_actions.append(invalid_action_diagnostic(
                    dragon_id, teams[dragon_id], round_num, last_turns.get(dragon_id)))
            if dragon_id < 2:
                queen_deaths[teams[dragon_id]] = {'round': round_num, 'reason': reason,
                                                 'last_turn': queen_turns.get(teams[dragon_id])}
            last_turns.pop(dragon_id, None)
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
        if invalid_actions:
            record['invalid_actions'] = invalid_actions
        if replay_dir and (outcome == 'loss' or invalid_actions):
            replay_dir = Path(replay_dir)
            replay_dir.mkdir(parents=True, exist_ok=True)
            name = (f'{replay_bot_label(candidate)}-{replay_bot_label(opponent)}-'
                    f'{Path(map_path).stem}-{seed}-{side}.replay')
            (replay_dir/name).write_bytes(engine.replay(str(paths['A']), str(paths['B'])))
            record['replay'] = str(replay_dir/name)
        return record
    finally:
        for bot in live.values():
            bot.stop()
        for pool in pools.values():
            pool.close()


def isolated_match(*job):
    """Threads supervise subprocesses; each engine lives in a fresh process."""
    process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--single-match'],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, start_new_session=True)
    try:
        output, errors = process.communicate(json.dumps([str(x) if isinstance(x, Path) else x for x in job]), timeout=300)
    except subprocess.TimeoutExpired:
        if os.name == 'posix':
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.communicate()
        raise RuntimeError('isolated match exceeded 300 seconds')
    if process.returncode:
        raise RuntimeError(f'isolated worker exited {process.returncode}: {errors[-2000:]}')
    return json.loads(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidates', nargs='+', required=True)
    parser.add_argument('--opponents', nargs='+', required=True)
    parser.add_argument('--maps', nargs='+', default=['arena','default_small','default','big_empty','schooltime','trophy','Colosseum','queen_of_spades'])
    parser.add_argument('--seeds', nargs='+', type=int, default=[101])
    parser.add_argument('--sides', nargs='+', choices=['A','B'], default=['A','B'], help='Both sides by default; a single side can run identical-bot controls')
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--output', required=True)
    parser.add_argument('--loss-replays')
    parser.add_argument('--resume', action='store_true', help='Continue an interrupted batch with the identical manifest')
    parser.add_argument('--explicit-endturn', action='store_true',
                        help='Require ENDTURN on native replies; use only when both bots promise it')
    args = parser.parse_args()
    missing_maps = [name for name in args.maps if not (ROOT/'maps'/f'{name}.map').is_file()]
    if missing_maps:
        parser.error('unknown map names (use filename stems, case-sensitive): ' + ', '.join(missing_maps))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    jobs = [(str(Path(c).resolve()), str(Path(o).resolve()), ROOT/'maps'/f'{m}.map', seed, side)
            for c in args.candidates for o in args.opponents for m in args.maps
            for seed in args.seeds for side in args.sides]
    metadata = {'toolkit': '1.2.9', 'candidates': args.candidates, 'opponents': args.opponents,
                'maps': args.maps, 'seeds': args.seeds, 'games': len(jobs),
                'sha256': {str(p): hashlib.sha256(Path(p).read_bytes()).hexdigest()
                           for p in args.candidates + args.opponents if Path(p).is_file()}}
    if args.sides != ['A', 'B']:
        metadata['sides'] = args.sides
    if args.explicit_endturn:
        metadata['explicit_endturn'] = True
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
    # The parent never runs Wasmtime concurrently in threads. One subprocess
    # owns each engine, avoiding reuse and process-pool worker lifecycle stalls.
    if not args.resume:
        output.write_text('')
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(isolated_match, *job, args.loss_replays, args.explicit_endturn): job for job in jobs}
        for future in as_completed(futures):
            job = futures[future]
            try:
                record = future.result()
            except Exception as error:
                record = {'candidate':job[0], 'opponent':job[1], 'map':job[2].stem,
                          'seed':job[3], 'side':job[4], 'valid':False, 'error':str(error)}
            records.append(record)
            # Reopen for each record so a workspace checkpoint replacing the
            # file cannot leave this process appending to an unlinked inode.
            with output.open('a') as log:
                log.write(json.dumps(record)+'\n')
                log.flush()
            print(f"[{len(records)}/{total}] {Path(job[0]).name} vs {Path(job[1]).name} {job[2].stem} seed={job[3]} side={job[4]}: {record.get('outcome', record.get('error'))}", flush=True)
    # Publish the completed in-memory matrix again so its final tally and
    # saved records agree even if a workspace checkpoint replaced a live log.
    output.write_text(''.join(json.dumps(record) + '\n' for record in records))
    for candidate in args.candidates:
        valid = [r for r in records if r['candidate']==str(Path(candidate).resolve()) and r['valid']]
        tally = Counter(r['outcome'] for r in valid)
        print(Path(candidate).name, dict(tally), f"{len(valid)} valid games")
    return 0 if len(records) == total and all(r['valid'] for r in records) else 1


if __name__ == '__main__':
    if sys.argv[1:] == ['--single-match']:
        print(json.dumps(match(*json.load(sys.stdin))))
    else:
        sys.exit(main())
