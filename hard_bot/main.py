import helper as unswbc
from helper import Controller, Direction, Game, Position, Tile

ct: Controller
game: Game
history: list[Position] = []
INT_MIN = -(1 << 31)
UINT32_MASK = (1 << 32) - 1
HUNTER_MAX_LENGTH = 6
MODE_COLLECT = "collect"
MODE_BALANCED = "balanced"
MODE_PRESSURE = "pressure"
MODE_HUNT = "hunt"


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


def favourable_head_attack(controller: Controller, game_state: Game, target: Position) -> bool:
    """Allow a short scout to trade for a visible head when we have the advantage."""
    if controller.get_length() > HUNTER_MAX_LENGTH or game_state.get_round_num() >= 470:
        return False
    if combat_mode(controller, game_state) not in (MODE_PRESSURE, MODE_HUNT):
        return False
    for tile in controller.get_tiles():
        dragon = tile.get_dragon()
        if dragon is None or dragon.get_team() == controller.get_team() or not dragon.is_head():
            continue
        if dragon.get_position() == target and controller.get_id() < dragon.get_id():
            return True
    return False


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
    return 0 if best is None else (current - best) * 8 + (80 if best == 0 else 0)


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
    """Reward safe moves that close distance to visible enemy heads."""
    score = 0
    for tile in controller.get_tiles():
        dragon = tile.get_dragon()
        if dragon is None or dragon.get_team() == controller.get_team() or not dragon.is_head():
            continue
        d = distance(start, dragon.get_position(), game_state)
        if d <= 10:
            score += max(0, 96 - d * 8)
    return score


def friendly_pressure(controller: Controller, game_state: Game, start: Position) -> int:
    score = 0
    for tile in controller.get_tiles():
        dragon = tile.get_dragon()
        if dragon is None or dragon.get_team() != controller.get_team() or dragon.get_id() == controller.get_id():
            continue
        d = distance(start, dragon.get_position(), game_state)
        if d <= 1:
            score -= 70
        elif d == 2:
            score -= 28 if dragon.is_head() else 12
        elif d == 3 and dragon.is_head():
            score -= 6
    return score


def population_target(game_state: Game) -> int:
    area = game_state.width * game_state.height
    if game_state.width <= 10 and game_state.height <= 10:
        return min(game_state.get_unit_limit(), 12)
    return min(game_state.get_unit_limit(), max(24, min(60, area // 12 + 20)))


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
    visible = visible_enemy_count(controller)
    return strategy_mode(
        controller.get_unit_count(),
        visible if visible else None,
        population_target(game_state),
    )


def strategy_weights(mode: str) -> tuple[int, int]:
    """Return (pearl weight, enemy-chase weight) for the active mode."""
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


def is_flagship(controller: Controller, game_state: Game) -> bool:
    return (controller.get_id() < 2 or controller.get_length() >= 16 or
            role_hash(controller.get_id()) % population_target(game_state) < flagship_target(game_state) - 1)


def recent_collision(target: Position, positions: list[Position], length: int) -> bool:
    return target in positions[-length:]


def score_move(controller: Controller, game_state: Game, direction: Direction, positions: list[Position]) -> int:
    start = controller.get_position()
    here = controller.get_tile(start)
    if here is None or not here.get_edge(direction).is_passable():
        return INT_MIN
    target = start.add_dir(direction)
    ahead = controller.get_tile(target)
    head_attack = favourable_head_attack(controller, game_state, target)
    if ahead is None or (occupied(ahead) and not head_attack) or enemy_head_ahead(controller, target) or recent_collision(target, positions, controller.get_length()):
        return INT_MIN
    if head_attack:
        return 1800
    future_mobility = mobility(controller, game_state, target)
    if future_mobility == 0:
        return INT_MIN
    area = open_area(controller, target)
    flagship, late = is_flagship(controller, game_state), game_state.get_round_num() >= 380
    mode = combat_mode(controller, game_state)
    pearl_weight, chase_weight = strategy_weights(mode)
    required_area = min(30, max(10, controller.get_length() + 4)) if flagship else 6
    if area < required_area:
        return INT_MIN
    if late and (area < 10 or future_mobility < 2 or here.get_edge(direction).is_portal()):
        return INT_MIN
    score = area * 12 + future_mobility * 12
    if not late and area >= 10 and future_mobility >= 2:
        score += pearl_drive(controller, game_state, target) * pearl_weight * (2 if flagship else 1)
    score += enemy_chase_value(controller, game_state, target) * chase_weight
    if future_mobility == 1:
        score -= 80
    score += enemy_pressure(controller, game_state, target) + friendly_pressure(controller, game_state, target)
    if enemy_collision_risk(controller, game_state, target):
        if late:
            return INT_MIN
        score -= 500
    if target.x == 0 or target.y == 0 or target.x == game_state.width - 1 or target.y == game_state.height - 1:
        score -= 150
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


def split_size(controller: Controller, game_state: Game) -> int:
    round_number, target, flagships = game_state.get_round_num(), population_target(game_state), flagship_target(game_state)
    ramped_target = min(target, flagships + max(0, round_number - 8) // 2)
    if (round_number < 8 or round_number >= 420 or controller.get_unit_count() >= ramped_target or
            has_enemy_near(controller, game_state, controller.get_position(), 2) or open_area(controller, controller.get_position()) < 12):
        return 0
    flagship = is_flagship(controller, game_state)
    if flagship and controller.get_unit_count() >= flagships and controller.get_length() < 30:
        return 0
    return 2 if controller.can_split(2) and controller.get_length() - 2 >= (9 if flagship else 2) else 0


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
    history.append(ct.get_position())
    if len(history) > 256:
        history.pop(0)
    planned_split = split_size(ct, game)
    if planned_split:
        ct.do_split(planned_split)
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
    if best_score == INT_MIN:
        for direction in Direction.get_direction_list():
            here, target = ct.get_tile(ct.get_position()), ct.get_position().add_dir(direction)
            ahead = ct.get_tile(target)
            if here is not None and here.get_edge(direction).is_passable() and ahead is not None and not occupied(ahead) and not enemy_head_ahead(ct, target):
                best = direction
                break
    if (not has_empty_step(ct) and game.get_round_num() < 420 and ct.get_unit_count() < population_target(game) and ct.can_split(2) and ct.get_length() >= 6):
        ct.do_split(2)
        return
    sprint = game.get_round_num() < 120 and ct.get_unit_count() < 4 and ct.get_length() >= 12 and safe_sprint(ct, game, best, 2, history)
    if sprint:
        history.extend([ct.get_position().add_dir(best), ct.get_position().add_dir(best).add_dir(best)])
        ct.make_moves([best, best])
    else:
        ct.make_move(best)


def main() -> None:
    global ct, game
    ct, game = unswbc.init()
    while unswbc.update(ct, game):
        execute_turn()
        unswbc.end_turn()


if __name__ == "__main__":
    main()
