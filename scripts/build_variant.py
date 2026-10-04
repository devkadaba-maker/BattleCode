#!/usr/bin/env python3
"""Materialize a baseline or parameter variant without editing the real bot.

Examples:
  python scripts/build_variant.py baseline --ref 29245ea
  python scripts/build_variant.py split3 --split-limit 3 --vision-weight 0
  unswbc run maps/arena.map .experiments/split3 .experiments/baseline --sandbox
"""
import argparse
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('name')
parser.add_argument('--ref')
parser.add_argument('--split-limit', type=int)
parser.add_argument('--vision-weight', type=int)
parser.add_argument('--weakhold-vision-weight', type=int)
parser.add_argument('--free-sprint', type=int, choices=[0,1,2], help='0 off, 1 all dragons, 2 queens only')
parser.add_argument('--queen-split-limit', type=int)
parser.add_argument('--queen-hunt', type=int, choices=[0,1])
parser.add_argument('--large-population-target', type=int)
parser.add_argument('--friendly-head-destination-penalty', type=int)
parser.add_argument('--friendly-priority-claim-penalty', type=int)
parser.add_argument('--enemy-heading-order-aware', type=int, choices=[0,1,2],
                    help='0 off, 1 all maps, 2 Schooltime 60x40 only')
parser.add_argument('--compile', action='store_true', help='Build native executable using the installed C++ compiler')
args = parser.parse_args()
if not args.name.replace('-','').replace('_','').isalnum():
    parser.error('name must contain only letters, numbers, dash or underscore')
if args.large_population_target is not None and args.large_population_target < 2:
    parser.error('--large-population-target must be at least 2')
if args.friendly_head_destination_penalty is not None and args.friendly_head_destination_penalty < 0:
    parser.error('--friendly-head-destination-penalty must be non-negative')
if args.friendly_priority_claim_penalty is not None and args.friendly_priority_claim_penalty < 0:
    parser.error('--friendly-priority-claim-penalty must be non-negative')
destination = ROOT / '.experiments' / args.name
destination.mkdir(parents=True, exist_ok=True)
if args.ref:
    source = subprocess.check_output(['git','show',f'{args.ref}:cpp_bot/main.cpp'],cwd=ROOT).decode()
else:
    source = (ROOT/'cpp_bot/main.cpp').read_text()
defines = {'PARENT_SPLIT_LIMIT':args.split_limit, 'VISION_TARGET_WEIGHT':args.vision_weight,
           'FREE_PEARL_SPRINT':args.free_sprint,'QUEEN_SPLIT_LIMIT':args.queen_split_limit,
           'QUEEN_HUNT':args.queen_hunt, 'WEAKHOLD_VISION_WEIGHT':args.weakhold_vision_weight}
defines['LARGE_POPULATION_TARGET'] = args.large_population_target
defines['FRIENDLY_HEAD_DESTINATION_PENALTY'] = args.friendly_head_destination_penalty
defines['FRIENDLY_PRIORITY_CLAIM_PENALTY'] = args.friendly_priority_claim_penalty
defines['ENEMY_HEADING_ORDER_AWARE'] = args.enemy_heading_order_aware
prefix = ''.join(f'#define {key} {value}\n' for key,value in defines.items() if value is not None)
(destination/'main.cpp').write_text(prefix+source)
for name in ('helper.hpp','bot.toml'):
    shutil.copyfile(ROOT/'cpp_bot'/name,destination/name)
if args.compile:
    from unswbc.project import Project
    print(Project.from_dir(str(destination)).compile())
print(destination)
