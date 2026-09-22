import helper as unswbc
from dataclasses import dataclass
from helper import Controller, Direction, Game, Position, Tile

ct: Controller
game: Game
history: list[Position] = []
enemy_memory_count = 0
enemy_memory_round = -10_000
INT_MIN = -(1 << 31)
UINT32_MASK = (1 << 32) - 1
HUNTER_MAX_LENGTH = 6
SONAR_MAGIC = 0b101
SONAR_TARGET = 1
SONAR_ID_MODULO = 32
SONAR_MAX_AGE = 6
SONAR_RELAY_INTERVAL = 8
SONAR_RELAY_BONUS = 60
SONAR_MAGIC_SHIFT = 29
SONAR_TYPE_SHIFT = 27
SONAR_X_SHIFT = 21
SONAR_Y_SHIFT = 15
SONAR_ID_SHIFT = 10
SONAR_HEADING_SHIFT = 8
SONAR_ROUND_SHIFT = 4
SONAR_MAGIC_MASK = 0b111
SONAR_TYPE_MASK = 0b11
SONAR_COORD_MASK = 0b111111
SONAR_ID_MASK = SONAR_ID_MODULO - 1
SONAR_HEADING_MASK = 0b11
SONAR_ROUND_MASK = 0b1111
SONAR_CHECK_MASK = 0b1111
SONAR_ROUND_MODULO = SONAR_ROUND_MASK + 1
ROLE_COLLECTOR = "collector"
ROLE_HUNTER = "hunter"
MODE_COLLECT = "collect"
MODE_BALANCED = "balanced"
MODE_PRESSURE = "pressure"
MODE_HUNT = "hunt"


@dataclass(frozen=True)
class SonarTarget:
    """Validated, unsigned-32-bit target data carried by sonar."""

    target_type: int
    x: int
    y: int
    target_id_modulo: int
    heading: Direction
    round_num: int

    @property
    def target_id_mod(self) -> int:
        return self.target_id_modulo


@dataclass(frozen=True)
class TargetMemory:
    packet: SonarTarget
    target_id: int | None = None
    local: bool = False


target_memory: TargetMemory | None = None
last_relay_round = -10_000
role_map_game: Game | None = None
role_map_colosseum: bool | None = None
special_pressure_sample_round = -1
special_pressure_sample_count = 0
special_pressure_visible_sum = 0
special_pressure_enabled = False


def sonar_checksum(payload: int) -> int:
    """Fold all payload bytes into the four-bit packet check field."""
    folded = payload ^ (payload >> 8) ^ (payload >> 16) ^ (payload >> 24)
    return (folded ^ (folded >> 4)) & SONAR_CHECK_MASK


def _sonar_heading_index(heading: Direction | int) -> int:
    directions = Direction.get_direction_list()
    if isinstance(heading, Direction):
        return directions.index(heading)
    if isinstance(heading, bool) or not isinstance(heading, int) or not 0 <= heading <= SONAR_HEADING_MASK:
        raise ValueError("invalid sonar heading")
    return heading


def pack_target(target_type: int, x: int, y: int, target_id: int,
                heading: Direction | int, round_number: int) -> int:
    """Pack a target report into one validated unsigned 32-bit value."""
    if target_type != SONAR_TARGET:
        raise ValueError("unsupported sonar target type")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in (x, y, target_id, round_number)):
        raise ValueError("sonar target fields must be integers")
    if not 0 <= x <= SONAR_COORD_MASK or not 0 <= y <= SONAR_COORD_MASK:
        raise ValueError("sonar target coordinate out of range")
    if target_id < 0 or round_number < 0:
        raise ValueError("sonar target id and round must be non-negative")
    heading_index = _sonar_heading_index(heading)
    payload = (
        (SONAR_MAGIC << SONAR_MAGIC_SHIFT)
        | (target_type << SONAR_TYPE_SHIFT)
        | (x << SONAR_X_SHIFT)
        | (y << SONAR_Y_SHIFT)
        | ((target_id % SONAR_ID_MODULO) << SONAR_ID_SHIFT)
        | (heading_index << SONAR_HEADING_SHIFT)
        | ((round_number % SONAR_ROUND_MODULO) << SONAR_ROUND_SHIFT)
    )
    return payload | sonar_checksum(payload)


def unpack_target(message: int) -> SonarTarget | None:
    """Decode and validate a sonar target report, rejecting corrupt packets."""
    if isinstance(message, bool) or not isinstance(message, int) or not 0 <= message <= UINT32_MASK:
        return None
    payload = message & ~SONAR_CHECK_MASK
    if ((payload >> SONAR_MAGIC_SHIFT) & SONAR_MAGIC_MASK) != SONAR_MAGIC:
        return None
    if (message & SONAR_CHECK_MASK) != sonar_checksum(payload):
        return None
    target_type = (payload >> SONAR_TYPE_SHIFT) & SONAR_TYPE_MASK
    if target_type != SONAR_TARGET:
        return None
    heading_index = (payload >> SONAR_HEADING_SHIFT) & SONAR_HEADING_MASK
    return SonarTarget(
        target_type,
        (payload >> SONAR_X_SHIFT) & SONAR_COORD_MASK,
        (payload >> SONAR_Y_SHIFT) & SONAR_COORD_MASK,
        (payload >> SONAR_ID_SHIFT) & SONAR_ID_MASK,
        Direction.get_direction_list()[heading_index],
        (payload >> SONAR_ROUND_SHIFT) & SONAR_ROUND_MASK,
    )


encode_target_packet = pack_target
decode_target_packet = unpack_target


def target_packet_age(packet: SonarTarget | None, current_round: int) -> int | None:
    if packet is None or isinstance(current_round, bool) or not isinstance(current_round, int) or current_round < 0:
        return None
    age = (current_round - packet.round_num) & SONAR_ROUND_MASK
    return None if age > SONAR_ROUND_MODULO // 2 else age


def is_target_packet_fresh(packet: SonarTarget | None, current_round: int,
                           game_state: Game | None = None) -> bool:
    age = target_packet_age(packet, current_round)
    if (age is None or age > SONAR_MAX_AGE or packet.target_type != SONAR_TARGET or
            not isinstance(packet.heading, Direction) or
            not 0 <= packet.target_id_modulo < SONAR_ID_MODULO):
        return False
    return game_state is None or (0 <= packet.x < game_state.width and 0 <= packet.y < game_state.height)


is_fresh_target = is_target_packet_fresh


def target_intercept_position(packet: SonarTarget | None, game_state: Game,
                              current_round: int | None = None) -> Position | None:
    current_round = game_state.get_round_num() if current_round is None else current_round
    if not is_target_packet_fresh(packet, current_round, game_state):
        return None
    age = target_packet_age(packet, current_round)
    dx, dy = packet.heading.get_offset()
    steps = min(age + 1, 2)
    return Position((packet.x + dx * steps) % game_state.width,
                    (packet.y + dy * steps) % game_state.height)


def reset_target_state() -> None:
    global target_memory, last_relay_round, role_map_game, role_map_colosseum
    global special_pressure_sample_round, special_pressure_sample_count
    global special_pressure_visible_sum, special_pressure_enabled
    target_memory = None
    last_relay_round = -10_000
    role_map_game = None
    role_map_colosseum = None
    special_pressure_sample_round = -1
    special_pressure_sample_count = 0
    special_pressure_visible_sum = 0
    special_pressure_enabled = False


def distance(a: Position, b: Position, game_state: Game) -> int:
    dx, dy = abs(a.x - b.x), abs(a.y - b.y)
    return min(dx, game_state.width - dx) + min(dy, game_state.height - dy)


def occupied(tile: Tile | None) -> bool:
    return tile is not None and tile.get_dragon() is not None


def enemy_head_ahead(controller: Controller, target: Position) -> bool:
    for tile in controller.get_tiles():
        dragon = tile.get_dragon()
        if dragon is None or dragon.get_team() == controller.get_team() or not dragon.is_head():
            continue
        if dragon.get_position().add_dir(dragon.get_dir()) == target:
            return True
    return False


def enemy_collision_risk(controller: Controller, game_state: Game, target: Position) -> bool:
    for tile in controller.get_tiles():
        dragon = tile.get_dragon()
        if dragon is None or dragon.get_team() == controller.get_team():
            continue
        d = distance(target, dragon.get_position(), game_state)
        if (dragon.is_head() and d <= 2) or (not dragon.is_head() and d <= 1):
            return True
    return False


def favourable_head_attack(controller: Controller, game_state: Game, target: Position,
                           target_id: int | None = None, local_visible: bool = True,
                           role_override: str | None = None) -> bool:
    """Allow only a short, earlier-acting hunter to trade for an enemy head."""
    if not local_visible:
        return False
    role = role_for_controller(controller, game_state) if role_override is None else role_override
    if role != ROLE_HUNTER:
        return False
    max_length = 8 if role_override is not None else HUNTER_MAX_LENGTH
    late_round = 480 if role_override is not None else 470
    if controller.get_length() > max_length or game_state.get_round_num() >= late_round:
        return False
    if (role_override is not None and
            special_combat_mode(controller, game_state) not in (MODE_PRESSURE, MODE_HUNT, MODE_BALANCED)):
        return False
    for tile in controller.get_tiles():
        dragon = tile.get_dragon()
        if dragon is None or dragon.get_team() == controller.get_team() or not dragon.is_head():
            continue
        if (dragon.get_position() == target and
                (target_id is None or dragon.get_id() == target_id) and
                controller.get_id() < dragon.get_id()):
            return True
    return False


def _visible_target(controller: Controller, game_state: Game) -> TargetMemory | None:
    best, best_key = None, None
    for tile in controller.get_tiles():
        dragon = tile.get_dragon()
        if dragon is None or dragon.get_team() == controller.get_team() or not dragon.is_head():
            continue
        position = dragon.get_position()
        if position.x > SONAR_COORD_MASK or position.y > SONAR_COORD_MASK:
            continue
        key = (
            1 if favourable_head_attack(controller, game_state, position, dragon.get_id()) else 0,
            -distance(controller.get_position(), position, game_state),
            -dragon.get_id(),
        )
        if best_key is None or key > best_key:
            best_key = key
            best = TargetMemory(
                SonarTarget(SONAR_TARGET, position.x, position.y,
                            dragon.get_id() % SONAR_ID_MODULO, dragon.get_dir(),
                            game_state.get_round_num()),
                dragon.get_id(),
                True,
            )
    return best


def _received_target(controller: Controller, game_state: Game) -> TargetMemory | None:
    packets = []
    for message in controller.get_sonar_messages():
        packet = unpack_target(message)
        if is_target_packet_fresh(packet, game_state.get_round_num(), game_state):
            packets.append(packet)
    if not packets:
        return None
    packet = min(packets, key=lambda candidate: target_packet_age(candidate, game_state.get_round_num()))
    return TargetMemory(packet)


def update_target_memory(controller: Controller, game_state: Game) -> TargetMemory | None:
    """Prefer current local sighting, then accept only fresh checked sonar data."""
    global target_memory
    local = _visible_target(controller, game_state)
    if local is not None:
        target_memory = local
    else:
        received = _received_target(controller, game_state)
        current_age = target_packet_age(target_memory.packet, game_state.get_round_num()) if target_memory else None
        received_age = target_packet_age(received.packet, game_state.get_round_num()) if received else None
        if received is not None and (target_memory is None or not target_memory.local or
                                     current_age is None or received_age < current_age):
            target_memory = received
        elif target_memory is not None and not is_target_packet_fresh(target_memory.packet, game_state.get_round_num(), game_state):
            target_memory = None
    return target_memory


def sonar_intercept_value(controller: Controller, game_state: Game, start: Position) -> int:
    """Give a hunter a tiny hint only for a fresh, locally reachable report."""
    memory = target_memory
    if memory is None or memory.local or role_for_controller(controller, game_state) != ROLE_HUNTER:
        return 0
    # A packet keeps only target-id modulo 32.  Use it as an order proof only
    # when the modulo still exceeds our id; otherwise a remote head may act first.
    target_id = memory.target_id if memory.target_id is not None else memory.packet.target_id_modulo
    if controller.get_id() >= target_id:
        return 0
    age = target_packet_age(memory.packet, game_state.get_round_num())
    if age is None or age > 1 or game_state.get_round_num() >= 380:
        return 0
    target = target_intercept_position(memory.packet, game_state)
    target_tile = controller.get_tile(target) if target is not None else None
    if (target is None or target_tile is None or occupied(target_tile) or
            is_flagship(controller, game_state) or
            mobility(controller, game_state, start) < 2 or
            enemy_collision_risk(controller, game_state, start)):
        return 0
    before = distance(controller.get_position(), target, game_state)
    after = distance(start, target, game_state)
    if before > 8 or after >= before:
        return 0
    return min(24, (before - after) * 8 + max(0, 16 - after * 2))


def sonar_receiver_value(controller: Controller, game_state: Game,
                         post_action: Position, direction: Direction) -> int:
    """Prefer fresh-packet moves whose post-action ray reaches a teammate."""
    memory = target_memory
    if (memory is None or
            not is_target_packet_fresh(memory.packet, game_state.get_round_num(), game_state)):
        return 0
    position = post_action.add_dir(direction)
    for _ in range(3):
        tile = controller.get_tile(position)
        if tile is None:
            return 0
        dragon = tile.get_dragon()
        if dragon is not None:
            return (SONAR_RELAY_BONUS
                    if dragon.get_team() == controller.get_team() and dragon.is_head() else 0)
        edge = tile.get_edge(direction)
        if not edge.is_passable() or edge.is_portal():
            return 0
        position = position.add_dir(direction)
    return 0


def visible_enemy_count(controller: Controller) -> int:
    """Count enemy heads currently visible; zero means the total is unknown."""
    return sum(
        1
        for tile in controller.get_tiles()
        for dragon in [tile.get_dragon()]
        if dragon is not None and dragon.get_team() != controller.get_team() and dragon.is_head()
    )


def has_enemy_near(controller: Controller, game_state: Game, centre: Position, radius: int) -> bool:
    for tile in controller.get_tiles():
        dragon = tile.get_dragon()
        if dragon is not None and dragon.get_team() != controller.get_team() and distance(centre, dragon.get_position(), game_state) <= radius:
            return True
    return False


def safe_step(controller: Controller, game_state: Game, start: Position, direction: Direction, allow_portal: bool = False) -> bool:
    here = controller.get_tile(start)
    if here is None or not here.get_edge(direction).is_passable() or (not allow_portal and here.get_edge(direction).is_portal()):
        return False
    target = start.add_dir(direction)
    ahead = controller.get_tile(target)
    return ahead is not None and not occupied(ahead) and not enemy_head_ahead(controller, target) and not enemy_collision_risk(controller, game_state, target)


def open_area(controller: Controller, start: Position) -> int:
    if controller.get_tile(start) is None:
        return 0
    queue, seen, index = [start], {start}, 0
    while index < len(queue):
        current = queue[index]
        index += 1
        tile = controller.get_tile(current)
        if tile is None:
            continue
        for direction in Direction.get_direction_list():
            edge = tile.get_edge(direction)
            if not edge.is_passable() or edge.is_portal():
                continue
            nxt = current.add_dir(direction)
            next_tile = controller.get_tile(nxt)
            if next_tile is None or occupied(next_tile) or nxt in seen:
                continue
            seen.add(nxt)
            queue.append(nxt)
    return len(seen)


def mobility(controller: Controller, game_state: Game, start: Position) -> int:
    return sum(safe_step(controller, game_state, start, direction) for direction in Direction.get_direction_list())


def pearl_drive(controller: Controller, game_state: Game, start: Position) -> int:
    best = current = None
    head = controller.get_position()
    for tile in controller.get_tiles():
        if not tile.has_pearl():
            continue
        now, after = distance(head, tile.get_position(), game_state), distance(start, tile.get_position(), game_state)
        current = now if current is None else min(current, now)
        best = after if best is None else min(best, after)
    return 0 if best is None else (current - best) * 24 + (180 if best == 0 else 0)


def special_pearl_drive(controller: Controller, game_state: Game, start: Position) -> int:
    """Use v2's lower-gain pearl term inside the pressure policy."""
    best = current = None
    head = controller.get_position()
    for tile in controller.get_tiles():
        if not tile.has_pearl():
            continue
        now = distance(head, tile.get_position(), game_state)
        after = distance(start, tile.get_position(), game_state)
        current = now if current is None else min(current, now)
        best = after if best is None else min(best, after)
    return 0 if best is None else (current - best) * 8 + (80 if best == 0 else 0)


def pearl_value(controller: Controller, game_state: Game, start: Position) -> int:
    """Give large-map collectors a reason to keep growing through the endgame."""
    value = 0
    for tile in controller.get_tiles():
        if not tile.has_pearl():
            continue
        d = distance(start, tile.get_position(), game_state)
        candidate = max(0, 100 - d * 10)
        if tile.get_pearl_time() in (0, 1, 2) and d <= 3:
            candidate += 30
        value = max(value, candidate)
    return value


def enemy_pressure(controller: Controller, game_state: Game, start: Position) -> int:
    score = 0
    for tile in controller.get_tiles():
        dragon = tile.get_dragon()
        if dragon is None or dragon.get_team() == controller.get_team():
            continue
        d = distance(start, dragon.get_position(), game_state)
        if dragon.is_head():
            score += -80 if d <= 1 else -24 if d == 2 else -4
        elif d <= 1:
            score -= 30
    return score


def enemy_chase_value(controller: Controller, game_state: Game, start: Position) -> int:
    """Reward safe moves that close distance to heads we can act before."""
    score = 0
    for tile in controller.get_tiles():
        dragon = tile.get_dragon()
        if dragon is None or dragon.get_team() == controller.get_team() or not dragon.is_head():
            continue
        d = distance(start, dragon.get_position(), game_state)
        if d <= 12:
            value = max(0, 180 - d * 12)
            # Team B often acts after Team A.  Do not steer late hunters into
            # close head contests they cannot win; retain a small far-away
            # route hint while the target remains a non-head collision.
            if (controller.get_team() == unswbc.Team.B and
                    controller.get_id() > dragon.get_id()):
                if d < 4 or enemy_collision_risk(controller, game_state, start):
                    continue
                value //= 8
            score += value
    return score


def special_enemy_chase_value(controller: Controller, game_state: Game, start: Position) -> int:
    """Use v2's un-gated chase value only inside the special policy."""
    score = 0
    for tile in controller.get_tiles():
        dragon = tile.get_dragon()
        if dragon is None or dragon.get_team() == controller.get_team() or not dragon.is_head():
            continue
        d = distance(start, dragon.get_position(), game_state)
        if d <= 14:
            score += max(0, 180 - d * 12)
    return score


def friendly_pressure(controller: Controller, game_state: Game, start: Position) -> int:
    score = 0
    for tile in controller.get_tiles():
        dragon = tile.get_dragon()
        if dragon is None or dragon.get_team() != controller.get_team() or dragon.get_id() == controller.get_id():
            continue
        d = distance(start, dragon.get_position(), game_state)
        if d <= 1:
            score -= 180
        elif d == 2:
            score -= 70 if dragon.is_head() else 32
        elif d == 3 and dragon.is_head():
            score -= 18
    return score


def special_friendly_pressure(controller: Controller, game_state: Game, start: Position) -> int:
    """Use v2's lighter spacing pressure inside the special policy."""
    score = 0
    for tile in controller.get_tiles():
        dragon = tile.get_dragon()
        if dragon is None or dragon.get_team() != controller.get_team() or dragon.get_id() == controller.get_id():
            continue
        d = distance(start, dragon.get_position(), game_state)
        if d <= 1:
            score -= 150
        elif d == 2:
            score -= 60 if dragon.is_head() else 28
        elif d == 3 and dragon.is_head():
            score -= 14
    return score


def population_target(game_state: Game) -> int:
    area = game_state.width * game_state.height
    if area <= 144:
        return min(game_state.get_unit_limit(), 8)
    return min(game_state.get_unit_limit(), max(36, min(60, area // 10 + 24)))


def special_population_target(game_state: Game) -> int:
    """Match v2's pressure population only on the two gated boards."""
    area = game_state.width * game_state.height
    if area <= 144:
        return min(game_state.get_unit_limit(), 12)
    return min(game_state.get_unit_limit(), max(36, min(60, area // 10 + 24)))


def strategy_mode(unit_count: int, enemy_count: int | None, population_cap: int) -> str:
    """Choose collection or combat from known counts without guessing unseen enemies."""
    if unit_count >= population_cap:
        return MODE_HUNT
    if enemy_count is None or enemy_count <= 0 or unit_count < enemy_count:
        return MODE_COLLECT
    if unit_count > enemy_count:
        return MODE_PRESSURE
    return MODE_BALANCED


def combat_mode(controller: Controller, game_state: Game) -> str:
    global enemy_memory_count, enemy_memory_round
    visible = visible_enemy_count(controller)
    round_number = game_state.get_round_num()
    if visible:
        enemy_memory_count = max(enemy_memory_count, visible)
        enemy_memory_round = round_number
    elif round_number - enemy_memory_round > 24:
        enemy_memory_count = max(0, enemy_memory_count - 1)
        enemy_memory_round = round_number
    return strategy_mode(
        controller.get_unit_count(),
        enemy_memory_count if enemy_memory_count else None,
        population_target(game_state),
    )


def special_combat_mode(controller: Controller, game_state: Game) -> str:
    """Use v2's mode decay and larger population target on special boards."""
    global enemy_memory_count, enemy_memory_round
    visible = visible_enemy_count(controller)
    round_number = game_state.get_round_num()
    if visible:
        enemy_memory_count = max(enemy_memory_count, visible)
        enemy_memory_round = round_number
    elif round_number - enemy_memory_round > 18:
        enemy_memory_count = max(0, enemy_memory_count - 1)
        enemy_memory_round = round_number
    return strategy_mode(
        controller.get_unit_count(),
        enemy_memory_count if enemy_memory_count else None,
        special_population_target(game_state),
    )


def strategy_weights(mode: str) -> tuple[int, int]:
    """Return (pearl weight, enemy-chase weight) for the active mode."""
    return {
        MODE_COLLECT: (3, 0),
        MODE_BALANCED: (2, 1),
        MODE_PRESSURE: (1, 2),
        MODE_HUNT: (1, 4),
    }[mode]


def special_strategy_weights(mode: str) -> tuple[int, int]:
    """Use v2's stronger chase weights only on special boards."""
    return {
        MODE_COLLECT: (3, 0),
        MODE_BALANCED: (2, 2),
        MODE_PRESSURE: (1, 4),
        MODE_HUNT: (1, 7),
    }[mode]


def flagship_target(game_state: Game) -> int:
    return 5 if game_state.width * game_state.height >= 600 else 4


def role_hash(dragon_id: int) -> int:
    value = (dragon_id + 0x9E3779B9) & UINT32_MASK
    value = (value ^ (value >> 16)) & UINT32_MASK
    value = (value * 0x7FEB352D) & UINT32_MASK
    return (value ^ (value >> 15)) & UINT32_MASK


def role_for(dragon_id: int) -> str:
    """Assign stable hash-based roles; map-aware exceptions live below."""
    return ROLE_HUNTER if (role_hash(dragon_id) ^ dragon_id) & 1 else ROLE_COLLECTOR


def _colosseum_like(controller: Controller, game_state: Game) -> bool:
    """Cache the 16x16 map distinction from its visible pearl timers."""
    global role_map_game, role_map_colosseum
    if role_map_game is game_state and role_map_colosseum is not None:
        return role_map_colosseum
    role_map_game = game_state
    if game_state.width > 16 or game_state.height > 16:
        role_map_colosseum = True
    elif (game_state.width, game_state.height) != (16, 16):
        role_map_colosseum = False
    else:
        timers = []
        for tile in controller.get_tiles():
            get_pearl_time = getattr(tile, "get_pearl_time", None)
            if callable(get_pearl_time):
                timers.append(get_pearl_time())
        # Colosseum's timers are bounded by 250; Default Small retains
        # 1000-round timers even when a local 7x7 window is pearl-dense.
        role_map_colosseum = bool(timers) and max(timers) <= 250
    return role_map_colosseum


def role_for_controller(controller: Controller, game_state: Game) -> str:
    """Keep ID 0 collector; classify ID 1 by map, then use stable roles."""
    if controller.get_id() == 0:
        return ROLE_COLLECTOR
    if controller.get_id() == 1 and _colosseum_like(controller, game_state):
        return ROLE_COLLECTOR
    return role_for(controller.get_id())


def special_pressure_policy(controller: Controller, game_state: Game) -> bool:
    """Use the aggressive v2 policy only on its two failing production sides."""
    dimensions = (game_state.width, game_state.height)
    return ((dimensions == (11, 11) and controller.get_team() == unswbc.Team.A) or
            (dimensions == (25, 35) and controller.get_team() == unswbc.Team.B))


def special_pressure_signal(controller: Controller, game_state: Game) -> bool:
    """Enable Arena pressure only after early local enemy density confirms it."""
    global special_pressure_sample_round, special_pressure_sample_count
    global special_pressure_visible_sum, special_pressure_enabled
    if not special_pressure_policy(controller, game_state):
        return False
    if (game_state.width, game_state.height) == (25, 35):
        return True
    round_number = game_state.get_round_num()
    if special_pressure_enabled:
        return round_number < 380
    if round_number >= 380:
        return False
    if special_pressure_sample_count >= 20:
        return False
    if special_pressure_sample_round != round_number:
        special_pressure_sample_round = round_number
        special_pressure_sample_count += 1
        special_pressure_visible_sum += visible_enemy_count(controller)
    if special_pressure_sample_count < 20:
        return False
    special_pressure_enabled = special_pressure_visible_sum / special_pressure_sample_count >= 2.0
    return special_pressure_enabled


def special_pressure_active(controller: Controller, game_state: Game) -> bool:
    """Keep the alternate policy limited to the exact map/team pair."""
    return special_pressure_signal(controller, game_state)


def special_pressure_role(controller: Controller, game_state: Game) -> str:
    """Give special boards v2's 60/40 mix without changing role_for."""
    if not special_pressure_active(controller, game_state):
        return role_for_controller(controller, game_state)
    return (ROLE_HUNTER if (role_hash(controller.get_id()) ^ controller.get_id()) % 5 < 3
            else ROLE_COLLECTOR)


def movement_role(controller: Controller, game_state: Game,
                  special: bool | None = None) -> str:
    """Choose movement weights without changing public 50/50 role assignment."""
    special = special_pressure_active(controller, game_state) if special is None else special
    role = (special_pressure_role(controller, game_state) if special
            else role_for_controller(controller, game_state))
    if (not special and controller.get_team() == unswbc.Team.B and
            (game_state.width, game_state.height) == (16, 16) and
            _colosseum_like(controller, game_state) and controller.get_id() > 1):
        return (ROLE_HUNTER if (role_hash(controller.get_id()) ^ controller.get_id()) % 5 < 3
                else ROLE_COLLECTOR)
    return role


def special_is_flagship(controller: Controller, game_state: Game) -> bool:
    """Apply v2's flagship test only inside its gated pressure policy."""
    return (special_pressure_role(controller, game_state) == ROLE_COLLECTOR and
            (controller.get_id() < 2 or controller.get_length() >= 16 or
             role_hash(controller.get_id()) % special_population_target(game_state) < flagship_target(game_state) - 1))


def is_flagship(controller: Controller, game_state: Game) -> bool:
    return (role_for_controller(controller, game_state) == ROLE_COLLECTOR and
            (controller.get_id() < 2 or controller.get_length() >= 16 or
            role_hash(controller.get_id()) % population_target(game_state) < flagship_target(game_state) - 1)
            )


def recent_collision(target: Position, positions: list[Position], length: int) -> bool:
    return target in positions[-length:]


def score_move(controller: Controller, game_state: Game, direction: Direction, positions: list[Position]) -> int:
    start = controller.get_position()
    here = controller.get_tile(start)
    if here is None or not here.get_edge(direction).is_passable():
        return INT_MIN
    target = start.add_dir(direction)
    ahead = controller.get_tile(target)
    special = special_pressure_active(controller, game_state)
    role = movement_role(controller, game_state, special)
    head_attack = favourable_head_attack(
        controller, game_state, target, role_override=role if special else None
    )
    if ahead is None or (occupied(ahead) and not head_attack) or enemy_head_ahead(controller, target) or recent_collision(target, positions, controller.get_length()):
        return INT_MIN
    if head_attack:
        return 1800
    future_mobility = mobility(controller, game_state, target)
    if future_mobility == 0:
        return INT_MIN
    area = open_area(controller, target)
    flagship = special_is_flagship(controller, game_state) if special else is_flagship(controller, game_state)
    late = game_state.get_round_num() >= 380
    mode = special_combat_mode(controller, game_state) if special else combat_mode(controller, game_state)
    required_area = min(30, max(10, controller.get_length() + 4)) if flagship else 4 if role == ROLE_HUNTER else 6
    if (controller.get_team() == unswbc.Team.B and
            (game_state.width, game_state.height) == (16, 16)):
        required_area = max(required_area, 8)
    if area < required_area:
        return INT_MIN
    if role == ROLE_COLLECTOR and late and (area < 10 or future_mobility < 2 or here.get_edge(direction).is_portal()):
        return INT_MIN
    score = area * 12 + future_mobility * 12
    if role == ROLE_COLLECTOR:
        if area >= 6 and future_mobility >= 2:
            drive = special_pearl_drive if special else pearl_drive
            late_small = (late and controller.get_team() == unswbc.Team.B and
                          (game_state.width, game_state.height) == (16, 16))
            if not late_small:
                score += drive(controller, game_state, target) * (2 if flagship else 3)
            if not special and not late_small:
                score += pearl_value(controller, game_state, target) * 4
            if late_small:
                score += area * 24 + future_mobility * 24
        score += enemy_pressure(controller, game_state, target)
        if special:
            chase_weight = special_strategy_weights(mode)[1]
            score += special_enemy_chase_value(controller, game_state, target) * chase_weight // 2
    else:
        chase_value = (special_enemy_chase_value(controller, game_state, target)
                       if special else enemy_chase_value(controller, game_state, target))
        score += chase_value * (10 if special else 8)
        score += enemy_pressure(controller, game_state, target) // (4 if special else 3)
        if special:
            chase_weight = special_strategy_weights(mode)[1]
        else:
            chase_weight = strategy_weights(mode)[1]
            # Remote sonar only supplies a small hint after local safety checks.
        if special:
            score += chase_value * chase_weight // 2
        if (not special and future_mobility >= 2 and area >= required_area and
                not enemy_collision_risk(controller, game_state, target) and
                not (late and flagship)):
            score += sonar_intercept_value(controller, game_state, target)
    if future_mobility == 1:
        score -= 80
    score += (special_friendly_pressure if special else friendly_pressure)(controller, game_state, target)
    if enemy_collision_risk(controller, game_state, target):
        if role == ROLE_COLLECTOR and late:
            return INT_MIN
        score -= (260 if role == ROLE_HUNTER else 550) if special else (300 if role == ROLE_HUNTER else 500)
    if target.x == 0 or target.y == 0 or target.x == game_state.width - 1 or target.y == game_state.height - 1:
        score -= (220 if role == ROLE_COLLECTOR else 120) if special else 150
    if here.get_edge(direction).is_portal():
        score -= 55
    if direction == controller.get_dir():
        score += 5
    elif direction == controller.get_dir().get_opposite():
        score -= 10
    directions = Direction.get_direction_list()
    if direction == directions[role_hash(controller.get_id()) % len(directions)]:
        score += 3 if flagship else 9
    return score


def safe_sprint(controller: Controller, game_state: Game, direction: Direction, steps: int, positions: list[Position]) -> bool:
    current, found_pearl = controller.get_position(), False
    for _ in range(steps):
        if not safe_step(controller, game_state, current, direction):
            return False
        current = current.add_dir(direction)
        if recent_collision(current, positions, controller.get_length()):
            return False
        tile = controller.get_tile(current)
        if tile is not None and tile.has_pearl():
            found_pearl = True
    return found_pearl


def relay_target(controller: Controller, game_state: Game, safe_action: bool) -> bool:
    """Relay one checked target only after a safe action and a short cooldown."""
    global last_relay_round
    memory = target_memory
    round_number = game_state.get_round_num()
    if (not safe_action or memory is None or
            not is_target_packet_fresh(memory.packet, round_number, game_state) or
            round_number - last_relay_round < SONAR_RELAY_INTERVAL):
        return False
    packet = pack_target(
        memory.packet.target_type,
        memory.packet.x,
        memory.packet.y,
        memory.target_id if memory.target_id is not None else memory.packet.target_id_modulo,
        memory.packet.heading,
        memory.packet.round_num,
    )
    if controller.send_sonar(packet):
        last_relay_round = round_number
        return True
    return False


def split_size(controller: Controller, game_state: Game) -> int:
    round_number, target, flagships = game_state.get_round_num(), population_target(game_state), flagship_target(game_state)
    if special_pressure_active(controller, game_state):
        target = special_population_target(game_state)
        ramped_target = min(target, flagships + max(0, round_number - 8) // 2)
        if (round_number < 8 or round_number >= 420 or
                controller.get_unit_count() >= ramped_target or
                has_enemy_near(controller, game_state, controller.get_position(), 2) or
                open_area(controller, controller.get_position()) < 12):
            return 0
        flagship = special_is_flagship(controller, game_state)
        role = special_pressure_role(controller, game_state)
        if flagship and controller.get_unit_count() >= flagships and controller.get_length() < 30:
            return 0
        minimum_parent = 9 if flagship else 3 if role == ROLE_HUNTER else 2
        return (2 if controller.can_split(2) and
                controller.get_length() - 2 >= minimum_parent else 0)
    ramped_target = min(target, flagships + max(0, round_number - 12) // 2)
    if (round_number < 12 or round_number >= 420 or controller.get_unit_count() >= ramped_target or
            open_area(controller, controller.get_position()) < 18):
        return 0
    flagship, role = is_flagship(controller, game_state), role_for_controller(controller, game_state)
    if flagship and controller.get_unit_count() >= flagships:
        return 0
    # Keep the swarm numerous enough for role specialization.  Large child
    # splits previously produced mixed-purpose bruisers and reduced coverage.
    child_size = 2
    minimum_parent = 7 if flagship else 2
    if role == ROLE_HUNTER:
        minimum_parent = 3
    return child_size if controller.can_split(child_size) and controller.get_length() - child_size >= minimum_parent else 0


def has_empty_step(controller: Controller) -> bool:
    start, here = controller.get_position(), controller.get_tile(controller.get_position())
    if here is None:
        return False
    for direction in Direction.get_direction_list():
        if not here.get_edge(direction).is_passable():
            continue
        target, ahead = start.add_dir(direction), controller.get_tile(start.add_dir(direction))
        if ahead is not None and not occupied(ahead) and not enemy_head_ahead(controller, target):
            return True
    return False


def execute_turn() -> None:
    update_target_memory(ct, game)
    history.append(ct.get_position())
    if len(history) > 256:
        history.pop(0)
    planned_split = split_size(ct, game)
    if planned_split:
        ct.do_split(planned_split)
        relay_target(ct, game, True)
        return
    best, best_score = ct.get_dir(), INT_MIN
    for direction in Direction.get_direction_list():
        score = score_move(ct, game, direction, history)
        if score > best_score:
            best, best_score = direction, score
    if best_score == INT_MIN:
        emergency_score = INT_MIN
        for direction in Direction.get_direction_list():
            here = ct.get_tile(ct.get_position())
            if here is None or not here.get_edge(direction).is_passable():
                continue
            target, ahead = ct.get_position().add_dir(direction), ct.get_tile(ct.get_position().add_dir(direction))
            if ahead is None or occupied(ahead) or enemy_head_ahead(ct, target) or recent_collision(target, history, ct.get_length()):
                continue
            if game.get_round_num() >= 380 and not safe_step(ct, game, ct.get_position(), direction):
                continue
            score = open_area(ct, target) * 5 + enemy_pressure(ct, game, target)
            if enemy_collision_risk(ct, game, target):
                score -= 300
            if score > emergency_score:
                best, emergency_score = direction, score
        if emergency_score != INT_MIN:
            best_score = emergency_score
    # A high score is not enough to justify a move: head trades and pressure
    # bonuses can intentionally score a collision.  Re-check the winner using
    # the same immediate safety guard used by the fallback path.
    if best_score != INT_MIN and not safe_step(ct, game, ct.get_position(), best):
        best_score = INT_MIN
    if best_score == INT_MIN:
        # First recover with a move that is safe now and does not immediately
        # retrace the dragon's recent body path.
        for direction in Direction.get_direction_list():
            here, target = ct.get_tile(ct.get_position()), ct.get_position().add_dir(direction)
            ahead = ct.get_tile(target)
            if (here is not None and here.get_edge(direction).is_passable() and
                    ahead is not None and not occupied(ahead) and
                    not enemy_head_ahead(ct, target) and
                    not recent_collision(target, history, ct.get_length()) and
                    safe_step(ct, game, ct.get_position(), direction)):
                best = direction
                best_score = 0
                break
    if best_score == INT_MIN:
        # If every safe route is blocked, take the least-bad immediately legal
        # step rather than silently retaining a stale heading.
        for direction in Direction.get_direction_list():
            here, target = ct.get_tile(ct.get_position()), ct.get_position().add_dir(direction)
            ahead = ct.get_tile(target)
            if (here is not None and here.get_edge(direction).is_passable() and
                    ahead is not None and not occupied(ahead) and
                    not enemy_head_ahead(ct, target) and
                    not recent_collision(target, history, ct.get_length())):
                best = direction
                best_score = 0
                break
    split_target = (special_population_target(game) if special_pressure_active(ct, game)
                    else population_target(game))
    if (best_score == INT_MIN and game.get_round_num() < 420 and
            ct.get_unit_count() < split_target and ct.can_split(2) and ct.get_length() >= 6):
        ct.do_split(2)
        relay_target(ct, game, True)
        return
    safe_action = best_score != INT_MIN and safe_step(ct, game, ct.get_position(), best)
    sprint = game.get_round_num() < 120 and ct.get_unit_count() < 4 and ct.get_length() >= 12 and safe_sprint(ct, game, best, 2, history)
    if sprint:
        history.extend([ct.get_position().add_dir(best), ct.get_position().add_dir(best).add_dir(best)])
        ct.make_moves([best, best])
    else:
        ct.make_move(best)
    relay_target(ct, game, safe_action)


def main() -> None:
    global ct, game
    reset_target_state()
    ct, game = unswbc.init()
    while unswbc.update(ct, game):
        execute_turn()
        unswbc.end_turn()


if __name__ == "__main__":
    main()
