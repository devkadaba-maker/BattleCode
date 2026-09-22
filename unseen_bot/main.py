import helper as unswbc
from helper import Controller, Direction, Game, Position, Tile

ct: Controller
game: Game
history: list[Position] = []


def distance(a: Position, b: Position) -> int:
    dx, dy = abs(a.x - b.x), abs(a.y - b.y)
    return min(dx, game.width - dx) + min(dy, game.height - dy)


def occupied(tile: Tile | None) -> bool:
    return tile is not None and tile.get_dragon() is not None


def enemy_danger(target: Position) -> bool:
    for tile in ct.get_tiles():
        dragon = tile.get_dragon()
        if dragon is None or dragon.get_team() == ct.get_team():
            continue
        d = distance(target, dragon.get_position())
        if (dragon.is_head() and d <= 2) or (not dragon.is_head() and d <= 1):
            return True
    return False


def open_area(start: Position) -> int:
    if ct.get_tile(start) is None:
        return 0
    queue, seen, index = [start], {start}, 0
    while index < len(queue):
        current = queue[index]
        index += 1
        tile = ct.get_tile(current)
        if tile is None:
            continue
        for direction in Direction.get_direction_list():
            if not tile.get_edge(direction).is_passable():
                continue
            nxt = current.add_dir(direction)
            next_tile = ct.get_tile(nxt)
            if next_tile is None or occupied(next_tile) or nxt in seen:
                continue
            seen.add(nxt)
            queue.append(nxt)
    return len(seen)


def pearl_score(start: Position) -> int:
    best = 0
    for tile in ct.get_tiles():
        if not tile.has_pearl():
            continue
        d = distance(start, tile.get_position())
        value = max(0, 100 - d * 11)
        if tile.get_pearl_time() in (0, 1, 2):
            value += 20
        best = max(best, value)
    return best


def legal(direction: Direction) -> bool:
    here = ct.get_tile(ct.get_position())
    if here is None or not here.get_edge(direction).is_passable():
        return False
    target = ct.get_position().add_dir(direction)
    ahead = ct.get_tile(target)
    return ahead is not None and not occupied(ahead) and not enemy_danger(target) and target not in history[-ct.get_length():]


def choose_move() -> Direction:
    directions = Direction.get_direction_list()
    offset = (game.get_round_num() * 17 + ct.get_id() * 31) % len(directions)
    directions = directions[offset:] + directions[:offset]
    best, best_score = ct.get_dir(), -10**9
    for direction in directions:
        if not legal(direction):
            continue
        target = ct.get_position().add_dir(direction)
        score = open_area(target) * 8 + pearl_score(target)
        if direction == ct.get_dir():
            score += 12
        elif direction == ct.get_dir().get_opposite():
            score -= 15
        if target.x in (0, game.width - 1) or target.y in (0, game.height - 1):
            score -= 35
        if score > best_score:
            best, best_score = direction, score
    if best_score > -10**9:
        return best
    for direction in directions:
        here = ct.get_tile(ct.get_position())
        target = ct.get_position().add_dir(direction)
        ahead = ct.get_tile(target)
        if here is not None and here.get_edge(direction).is_passable() and ahead is not None and not occupied(ahead):
            return direction
    return ct.get_dir()


def execute_turn() -> None:
    history.append(ct.get_position())
    if len(history) > 160:
        del history[:-160]
    if (game.get_round_num() < 220 and ct.get_unit_count() < 8 and ct.get_length() >= 8
            and ct.can_split(2) and open_area(ct.get_position()) >= 12):
        ct.do_split(2)
        return
    ct.make_move(choose_move())


def main() -> None:
    global ct, game
    ct, game = unswbc.init()
    while unswbc.update(ct, game):
        execute_turn()
        unswbc.end_turn()


if __name__ == "__main__":
    main()
