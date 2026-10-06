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
parser.add_argument('--child-split-limit', type=int)
parser.add_argument('--planned-split-min-length', type=int)
parser.add_argument('--split-visible-pearl-requirement', type=int)
parser.add_argument('--recent-region-penalty', type=int)
parser.add_argument('--queen-hunt', type=int, choices=[0,1])
parser.add_argument('--large-population-target', type=int)
parser.add_argument('--friendly-head-destination-penalty', type=int)
parser.add_argument('--friendly-priority-claim-penalty', type=int)
parser.add_argument('--enemy-heading-order-aware', type=int, choices=[0,1,2,3],
                    help='0 off, 1 all maps, 2 Schooltime 60x40 only, 3 Schooltime plus 48x24 maps')
parser.add_argument('--enemy-memory-rounds', type=int,
                    help='rounds before ordinary-map enemy memory begins to decay (default: 24)')
parser.add_argument('--special-enemy-memory-rounds', type=int,
                    help='rounds before special-policy enemy memory begins to decay (default: 18)')
parser.add_argument('--schooltime-contact-memory', type=int, choices=[0,1],
                    help='1 limits enemy memory to current contact on Schooltime only')
parser.add_argument('--hunt-pearl-weight', type=int,
                    help='pearl-drive weight while at the population target (default: 2)')
parser.add_argument('--pressure-pearl-weight', type=int,
                    help='pearl-drive weight while ahead but below the population target (default: 2)')
parser.add_argument('--flagship-border-extra-penalty', type=int,
                    help='extra penalty for flagship moves onto the map perimeter (default: 0)')
parser.add_argument('--new-child-clearance-weight', type=int,
                    help='extra friendly-pressure multiplier on a new child first move (default: 0)')
parser.add_argument('--late-harvest-mode', type=int, choices=[0,1,2],
                    help='after the cutoff: 1 disables chase, 2 also raises pearl weight to 3')
parser.add_argument('--late-harvest-round', type=int,
                    help='first round of the optional late harvesting policy (default: 400)')
parser.add_argument('--earned-flagship-length', type=int,
                    help='length at which any collector gains flagship protection (default: 16)')
parser.add_argument('--pearl-cluster-graph-mode', type=int, choices=[0,1,2],
                    help='0 geometric, 1 reachable pearls, 2 also use route distance')
parser.add_argument('--head-attack-visible-margin', type=int,
                    help='minimum visible enemy length advantage for a head trade (default: 4)')
parser.add_argument('--head-attack-last-round', type=int,
                    help='last round when an expendable head trade is allowed (default: 500)')
parser.add_argument('--head-attack-target-role', type=int, choices=[0,1,2],
                    help='0 all enemies, 1 queens only, 2 non-queens only')
parser.add_argument('--compile', action='store_true', help='Build native executable using the installed C++ compiler')
args = parser.parse_args()
if not args.name.replace('-','').replace('_','').isalnum():
    parser.error('name must contain only letters, numbers, dash or underscore')
if args.large_population_target is not None and args.large_population_target < 2:
    parser.error('--large-population-target must be at least 2')
if args.child_split_limit is not None and args.child_split_limit < 0:
    parser.error('--child-split-limit must be non-negative')
if args.planned_split_min_length is not None and args.planned_split_min_length < 4:
    parser.error('--planned-split-min-length must be at least 4')
if args.split_visible_pearl_requirement is not None and args.split_visible_pearl_requirement < 0:
    parser.error('--split-visible-pearl-requirement must be non-negative')
if args.recent_region_penalty is not None and args.recent_region_penalty < 0:
    parser.error('--recent-region-penalty must be non-negative')
if args.friendly_head_destination_penalty is not None and args.friendly_head_destination_penalty < 0:
    parser.error('--friendly-head-destination-penalty must be non-negative')
if args.friendly_priority_claim_penalty is not None and args.friendly_priority_claim_penalty < 0:
    parser.error('--friendly-priority-claim-penalty must be non-negative')
if args.enemy_memory_rounds is not None and args.enemy_memory_rounds < 0:
    parser.error('--enemy-memory-rounds must be non-negative')
if args.special_enemy_memory_rounds is not None and args.special_enemy_memory_rounds < 0:
    parser.error('--special-enemy-memory-rounds must be non-negative')
if args.hunt_pearl_weight is not None and args.hunt_pearl_weight < 0:
    parser.error('--hunt-pearl-weight must be non-negative')
if args.pressure_pearl_weight is not None and args.pressure_pearl_weight < 0:
    parser.error('--pressure-pearl-weight must be non-negative')
if args.flagship_border_extra_penalty is not None and args.flagship_border_extra_penalty < 0:
    parser.error('--flagship-border-extra-penalty must be non-negative')
if args.new_child_clearance_weight is not None and args.new_child_clearance_weight < 0:
    parser.error('--new-child-clearance-weight must be non-negative')
if args.late_harvest_round is not None and not 0 <= args.late_harvest_round <= 500:
    parser.error('--late-harvest-round must be between 0 and 500')
if args.earned_flagship_length is not None and args.earned_flagship_length < 2:
    parser.error('--earned-flagship-length must be at least 2')
if args.head_attack_visible_margin is not None and args.head_attack_visible_margin < 0:
    parser.error('--head-attack-visible-margin must be non-negative')
if args.head_attack_last_round is not None and args.head_attack_last_round < 0:
    parser.error('--head-attack-last-round must be non-negative')
destination = ROOT / '.experiments' / args.name
destination.mkdir(parents=True, exist_ok=True)
if args.ref:
    source = subprocess.check_output(['git','show',f'{args.ref}:cpp_bot/main.cpp'],cwd=ROOT).decode()
else:
    source = (ROOT/'cpp_bot/main.cpp').read_text()
defines = {'PARENT_SPLIT_LIMIT':args.split_limit, 'VISION_TARGET_WEIGHT':args.vision_weight,
           'FREE_PEARL_SPRINT':args.free_sprint,'QUEEN_SPLIT_LIMIT':args.queen_split_limit,
           'QUEEN_HUNT':args.queen_hunt, 'WEAKHOLD_VISION_WEIGHT':args.weakhold_vision_weight}
defines['CHILD_SPLIT_LIMIT'] = args.child_split_limit
defines['PLANNED_SPLIT_MIN_LENGTH'] = args.planned_split_min_length
defines['SPLIT_VISIBLE_PEARL_REQUIREMENT'] = args.split_visible_pearl_requirement
defines['RECENT_REGION_PENALTY'] = args.recent_region_penalty
defines['LARGE_POPULATION_TARGET'] = args.large_population_target
defines['FRIENDLY_HEAD_DESTINATION_PENALTY'] = args.friendly_head_destination_penalty
defines['FRIENDLY_PRIORITY_CLAIM_PENALTY'] = args.friendly_priority_claim_penalty
defines['ENEMY_HEADING_ORDER_AWARE'] = args.enemy_heading_order_aware
defines['ENEMY_MEMORY_ROUNDS'] = args.enemy_memory_rounds
defines['SPECIAL_ENEMY_MEMORY_ROUNDS'] = args.special_enemy_memory_rounds
defines['SCHOOLTIME_CONTACT_MEMORY'] = args.schooltime_contact_memory
defines['HUNT_PEARL_WEIGHT'] = args.hunt_pearl_weight
defines['PRESSURE_PEARL_WEIGHT'] = args.pressure_pearl_weight
defines['FLAGSHIP_BORDER_EXTRA_PENALTY'] = args.flagship_border_extra_penalty
defines['NEW_CHILD_CLEARANCE_WEIGHT'] = args.new_child_clearance_weight
defines['LATE_HARVEST_MODE'] = args.late_harvest_mode
defines['LATE_HARVEST_ROUND'] = args.late_harvest_round
defines['EARNED_FLAGSHIP_LENGTH'] = args.earned_flagship_length
defines['PEARL_CLUSTER_GRAPH_MODE'] = args.pearl_cluster_graph_mode
defines['HEAD_ATTACK_VISIBLE_MARGIN'] = args.head_attack_visible_margin
defines['HEAD_ATTACK_LAST_ROUND'] = args.head_attack_last_round
defines['HEAD_ATTACK_TARGET_ROLE'] = args.head_attack_target_role
prefix = ''.join(f'#define {key} {value}\n' for key,value in defines.items() if value is not None)
(destination/'main.cpp').write_text(prefix+source)
for name in ('helper.hpp','bot.toml'):
    shutil.copyfile(ROOT/'cpp_bot'/name,destination/name)
if args.compile:
    from unswbc.project import Project
    print(Project.from_dir(str(destination)).compile())
print(destination)
