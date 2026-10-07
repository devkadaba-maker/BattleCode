#!/usr/bin/env python3
"""Recheck the frozen UNSW promotion gate and unaffected-map equivalence."""
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
PREFIX='persistent-queen-cycle'

def read(name):
    return [json.loads(line) for line in (ROOT/'benchmarks'/name).read_text().splitlines()]

def bot_name(path):
    p=Path(path)
    return p.parent.parent.name if p.name=='bot' and p.parent.name=='.unswbc-build' else p.name

def main():
    paths=[f'{PREFIX}-fresh-validation.jsonl', f'{PREFIX}-other-map-controls.jsonl', f'{PREFIX}-diverse-opponents.jsonl']
    subprocess.run([sys.executable,str(ROOT/'scripts/check_records.py'),*[str(ROOT/'benchmarks'/p) for p in paths]],check=True)
    rows=read(paths[0]);plan=json.loads((ROOT/'benchmarks'/f'{PREFIX}-validation-plan.json').read_text())
    assert len(rows)==plan['games']==100
    assert {(r['seed'],r['side']) for r in rows}=={(seed,side) for seed in plan['seeds'] for side in ('A','B')}
    manifest=json.loads((ROOT/'benchmarks'/f'{PREFIX}-fresh-validation.manifest.json').read_text())
    assert set(manifest['sha256'].values())=={plan['candidate_sha256'],plan['champion_sha256']}
    production=ROOT/'cpp_bot/.unswbc-build/bot'
    if production.is_file():
        assert hashlib.sha256(production.read_bytes()).hexdigest()==plan['candidate_sha256']
    counts=Counter(r['outcome'] for r in rows)
    w,l,d=counts['win'],counts['loss'],counts['draw'];n=w+l;p=w/n;z=1.96
    centre=(p+z*z/(2*n))/(1+z*z/n)
    radius=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    score=100*(w+.5*d)/len(rows)
    paired=defaultdict(float)
    for r in rows:paired[r['seed']]+={'win':.5,'draw':0,'loss':-.5}[r['outcome']]
    positive=sum(v>0 for v in paired.values());negative=sum(v<0 for v in paired.values());paired_n=positive+negative
    sign_p=sum(math.comb(paired_n,k) for k in range(positive,paired_n+1))/2**paired_n
    assert score>=plan['criteria']['minimum_score_percent']
    assert 100*(centre-radius)>plan['criteria']['decisive_wilson95_lower_above']
    assert sign_p<plan['criteria']['paired_seed_sign_test_one_sided_p_below']
    controls=read(paths[1]);grouped=defaultdict(dict)
    for r in controls:grouped[bot_name(r['candidate'])][(r['map'],r['seed'],r['side'])]=r
    new=grouped[PREFIX];old=grouped['contact1'];assert new.keys()==old.keys() and len(new)==42
    assert len({key[0] for key in new})==21 and all(key[0]!='unsw' for key in new)
    fields=('result','outcome','deaths','queen_deaths','peak_population','faults','notices','valid')
    for key in new:
        for field in fields:assert new[key].get(field)==old[key].get(field),(key,field)
    sandbox=[]
    for side in ('A','B'):
        txt=(ROOT/'benchmarks'/f'{PREFIX}-sandbox-{side}.txt').read_text()
        assert not re.search(r'invalid action|timed out|runtime error',txt,re.I)
        match=re.search(rf'team {side} points per turn:.*max ([\d.]+)M',txt)
        assert match,side
        maximum=int(float(match[1])*1_000_000)
        assert maximum<plan['criteria']['judge_sandbox_cpu_below']
        sandbox.append({'candidate_side':side,'maximum_points':maximum,'rounds':500})
        assert 'after 500 rounds' in txt
    alive=Counter()
    for r in rows:
        side=r['side'].lower();enemy='b' if side=='a' else 'a'
        alive['candidate']+=r['result'][side+'_queen']>0
        alive['champion']+=r['result'][enemy+'_queen']>0
    diverse=defaultdict(Counter)
    for r in read(paths[2]):diverse[bot_name(r['opponent'])][r['outcome']]+=1
    result={'decision':'promote','scope':plan['scope'],'wins':w,'losses':l,'draws':d,'score_percent':score,
        'decisive_wilson95_percent':[100*(centre-radius),100*(centre+radius)],
        'paired_seeds':{'positive':positive,'negative':negative,'ties':50-paired_n,'one_sided_sign_p':sign_p},
        'queen_alive_at_end':dict(alive),'unaffected_maps':21,'exactly_equal_candidate_control_pairs':42,
        'sandbox':sandbox,'diverse_opponents':{k:dict(v) for k,v in diverse.items()},
        'candidate_sha256':plan['candidate_sha256'],'champion_sha256':plan['champion_sha256'],
        'screening_excluded':True,'limitations':'Local UNSW matches against frozen opponents, not measured ladder Elo.'}
    output=ROOT/'benchmarks'/f'{PREFIX}-decision.json'
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
