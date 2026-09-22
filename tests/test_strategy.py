import sys
from pathlib import Path

BOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BOT_DIR))
import helper as unswbc
import main as strategy


class _Dragon:
    def __init__(self, position, dragon_id, team, heading=unswbc.Direction.NORTH, head=True):
        self.position = position
        self.dragon_id = dragon_id
        self.team = team
        self.heading = heading
        self.head = head

    def get_position(self):
        return self.position

    def get_id(self):
        return self.dragon_id

    def get_team(self):
        return self.team

    def get_dir(self):
        return self.heading

    def is_head(self):
        return self.head


class _Tile:
    def __init__(self, dragon):
        self.dragon = dragon

    def get_dragon(self):
        return self.dragon


class _Edge:
    def __init__(self, portal=False):
        self.portal = portal

    def is_passable(self):
        return True

    def is_portal(self):
        return self.portal


class _RelayTile(_Tile):
    def __init__(self, dragon=None, portal=False):
        super().__init__(dragon)
        self.edge = _Edge(portal)

    def get_edge(self, direction):
        return self.edge


class _PearlTile(_RelayTile):
    def __init__(self, pearl_time, dragon=None, portal=False, has_pearl=False):
        super().__init__(dragon, portal)
        self.pearl_time = pearl_time
        self.pearl_present = has_pearl

    def has_pearl(self):
        return self.pearl_present

    def get_pearl_time(self):
        return self.pearl_time


class _Controller:
    def __init__(self, dragon_id, team, length, tiles, heading=unswbc.Direction.NORTH):
        self.dragon_id = dragon_id
        self.team = team
        self.length = length
        self.tiles = tiles
        self.heading = heading
        self.unit_count = 1

    def get_id(self):
        return self.dragon_id

    def get_team(self):
        return self.team

    def get_length(self):
        return self.length

    def get_unit_count(self):
        return self.unit_count

    def can_split(self, child_size):
        return True

    def get_dir(self):
        return self.heading

    def get_tiles(self):
        return self.tiles


class _RelayController(_Controller):
    def __init__(self, dragon_id, team, length, tiles, position, visible,
                 heading=unswbc.Direction.NORTH):
        super().__init__(dragon_id, team, length, tiles, heading)
        self.position = position
        self.visible = visible

    def get_position(self):
        return self.position

    def get_tile(self, position):
        return self.visible.get((position.x, position.y))


def main() -> None:
    assert [strategy.population_target(unswbc.Game(*case)) for case in [
        (10, 10, 64), (11, 11, 64), (16, 16, 64), (25, 25, 64), (64, 64, 48)
    ]] == [8, 36, 49, 60, 48]
    assert [strategy.flagship_target(unswbc.Game(*case)) for case in [
        (16, 16, 64), (25, 25, 64)
    ]] == [4, 5]
    assert [strategy.role_hash(dragon_id) for dragon_id in [0, 1, 2, 17, 23, 59, 60, 255]] == [
        1679741386, 3828559020, 1682401043, 3676020301, 3705810780, 3755058151, 1608800467, 577342704
    ]
    roles = [strategy.role_for(dragon_id) for dragon_id in range(60)]
    assert roles[0] == strategy.ROLE_COLLECTOR
    assert roles[1] == strategy.ROLE_HUNTER
    spawned_roles = roles[2:]
    assert strategy.ROLE_COLLECTOR in spawned_roles
    assert strategy.ROLE_HUNTER in spawned_roles
    assert abs(roles.count(strategy.ROLE_COLLECTOR) - roles.count(strategy.ROLE_HUNTER)) <= 8
    assert strategy.strategy_mode(30, 12, 30) == strategy.MODE_HUNT
    assert strategy.strategy_mode(8, 12, 30) == strategy.MODE_COLLECT
    assert strategy.strategy_mode(14, 8, 30) == strategy.MODE_PRESSURE
    assert strategy.strategy_mode(10, 10, 30) == strategy.MODE_BALANCED
    assert strategy.strategy_mode(8, None, 30) == strategy.MODE_COLLECT
    assert strategy.strategy_weights(strategy.MODE_COLLECT) == (3, 0)
    assert strategy.strategy_weights(strategy.MODE_PRESSURE) == (1, 2)
    assert strategy.strategy_weights(strategy.MODE_HUNT) == (1, 4)

    packet = strategy.pack_target(strategy.SONAR_TARGET, 12, 9, 37, unswbc.Direction.WEST, 42)
    decoded = strategy.unpack_target(packet)
    assert decoded is not None
    assert (decoded.x, decoded.y, decoded.target_id_modulo, decoded.heading) == (12, 9, 5, unswbc.Direction.WEST)
    assert packet & strategy.SONAR_CHECK_MASK == strategy.sonar_checksum(packet & ~strategy.SONAR_CHECK_MASK)
    assert strategy.unpack_target(packet ^ 1) is None
    assert strategy.target_packet_age(decoded, 45) == 3
    assert strategy.is_target_packet_fresh(decoded, 48)
    assert not strategy.is_target_packet_fresh(decoded, 49)

    game = unswbc.Game(16, 16, 64)
    game.round_num = 42
    unswbc.game = game
    strategy.reset_target_state()
    relay_start = unswbc.Position(1, 1)
    relay_friend = _Dragon(9, 9, unswbc.Team.A)
    relay_controller = _RelayController(
        1, unswbc.Team.A, 3, [], relay_start,
        {(2, 1): _RelayTile(), (3, 1): _RelayTile(relay_friend)},
    )
    assert strategy.sonar_receiver_value(
        relay_controller, game, relay_start, unswbc.Direction.EAST
    ) == 0
    strategy.target_memory = strategy.TargetMemory(decoded)
    relay_controller.visible[(2, 1)] = _RelayTile(relay_friend)
    relay_controller.visible[(3, 1)] = _RelayTile()
    assert strategy.sonar_receiver_value(
        relay_controller, game, relay_start.add_dir(unswbc.Direction.EAST), unswbc.Direction.EAST
    ) == 0
    relay_controller.visible[(3, 1)] = _RelayTile(relay_friend)
    assert strategy.sonar_receiver_value(
        relay_controller, game, relay_start.add_dir(unswbc.Direction.EAST), unswbc.Direction.EAST
    ) == strategy.SONAR_RELAY_BONUS
    relay_controller.visible[(3, 1)] = _RelayTile(portal=True)
    assert strategy.sonar_receiver_value(
        relay_controller, game, relay_start.add_dir(unswbc.Direction.EAST), unswbc.Direction.EAST
    ) == 0
    strategy.reset_target_state()

    safe_start = unswbc.Position(5, 5)
    safe_visible = {
        (x, y): _RelayTile()
        for x in range(3, 8)
        for y in range(3, 8)
    }
    safe_controller = _RelayController(
        1, unswbc.Team.A, 3, [], safe_start, safe_visible, unswbc.Direction.EAST
    )
    arena_game = unswbc.Game(11, 11, 64)
    arena_game.round_num = 100
    unswbc.game = arena_game
    split_controller = _RelayController(
        3, unswbc.Team.B, 7, [], safe_start, safe_visible, unswbc.Direction.EAST
    )
    split_controller.unit_count = strategy.population_target(arena_game) - 1
    assert strategy.split_size(split_controller, arena_game) == 2
    split_controller.unit_count = strategy.population_target(arena_game)
    assert strategy.split_size(split_controller, arena_game) == 0
    arena_game.round_num = 11
    assert strategy.split_size(split_controller, arena_game) == 0
    arena_game.round_num = 100
    flagship_controller = _RelayController(
        0, unswbc.Team.B, 10, [], safe_start, safe_visible, unswbc.Direction.EAST
    )
    flagship_controller.unit_count = strategy.flagship_target(arena_game) - 1
    assert strategy.split_size(flagship_controller, arena_game) == 2
    flagship_controller.unit_count = strategy.flagship_target(arena_game)
    assert strategy.split_size(flagship_controller, arena_game) == 0
    flagship_b_controller = _RelayController(
        1, unswbc.Team.B, 10,
        [_PearlTile(250, has_pearl=False) for _ in range(25)], safe_start,
        {(x, y): _PearlTile(250, has_pearl=False) for x in range(3, 8) for y in range(3, 8)},
        unswbc.Direction.EAST
    )
    flagship_b_controller.unit_count = strategy.flagship_target(arena_game) - 1
    colosseum_game = unswbc.Game(16, 16, 64)
    assert strategy.role_for_controller(flagship_b_controller, colosseum_game) == strategy.ROLE_COLLECTOR
    assert strategy.is_flagship(flagship_b_controller, colosseum_game)
    default_tiles = [_PearlTile(1000, has_pearl=False) for _ in range(25)]
    default_controller = _RelayController(
        1, unswbc.Team.B, 10, default_tiles, safe_start,
        {(x, y): _PearlTile(1000, has_pearl=False) for x in range(3, 8) for y in range(3, 8)},
        unswbc.Direction.EAST
    )
    default_game = unswbc.Game(16, 16, 64)
    assert strategy.role_for_controller(default_controller, default_game) == strategy.ROLE_HUNTER
    dense_default_controller = _RelayController(
        2, unswbc.Team.B, 10,
        [_PearlTile(50, has_pearl=False) for _ in range(25)], safe_start,
        {(x, y): _PearlTile(50, has_pearl=False) for x in range(3, 8) for y in range(3, 8)},
        unswbc.Direction.EAST
    )
    assert not strategy._colosseum_like(dense_default_controller, default_game)
    colosseum_movement_roles = []
    for dragon_id in range(2, 32):
        controller = _RelayController(
            dragon_id, unswbc.Team.B, 5,
            [_PearlTile(250, has_pearl=False) for _ in range(25)], safe_start,
            {(x, y): _PearlTile(250, has_pearl=False) for x in range(3, 8) for y in range(3, 8)},
            unswbc.Direction.EAST
        )
        role = strategy.movement_role(controller, colosseum_game)
        expected = (strategy.ROLE_HUNTER
                    if (strategy.role_hash(dragon_id) ^ dragon_id) % 5 < 3
                    else strategy.ROLE_COLLECTOR)
        assert role == expected
        colosseum_movement_roles.append(role)
    assert colosseum_movement_roles.count(strategy.ROLE_HUNTER) == 18
    assert strategy.movement_role(default_controller, default_game) == strategy.role_for(1)
    strategy.reset_target_state()
    strategy.enemy_memory_count = 0
    strategy.enemy_memory_round = -10_000
    arena_pressure_controller = _RelayController(
        2, unswbc.Team.A, 5, [], safe_start, safe_visible, unswbc.Direction.EAST
    )
    assert strategy.special_pressure_policy(arena_pressure_controller, arena_game)
    low_signal_controller = _Controller(
        2, unswbc.Team.A, 5,
        [_Tile(_Dragon(unswbc.Position(5, 5), 9, unswbc.Team.B))],
    )
    high_signal_controller = _Controller(
        2, unswbc.Team.A, 5,
        [_Tile(_Dragon(unswbc.Position(x, 5), 9 + x, unswbc.Team.B)) for x in (1, 3, 5, 7, 9)],
    )
    arena_game.round_num = 1
    for round_number in range(1, 21):
        arena_game.round_num = round_number
        assert not strategy.special_pressure_signal(low_signal_controller, arena_game)
    assert not strategy.special_pressure_active(arena_pressure_controller, arena_game)
    strategy.reset_target_state()
    for round_number in range(1, 20):
        arena_game.round_num = round_number
        assert not strategy.special_pressure_signal(high_signal_controller, arena_game)
    arena_game.round_num = 20
    assert strategy.special_pressure_signal(high_signal_controller, arena_game)
    assert strategy.special_pressure_active(arena_pressure_controller, arena_game)
    arena_game.round_num = 120
    assert strategy.special_pressure_active(arena_pressure_controller, arena_game)
    arena_game.round_num = 379
    assert strategy.special_pressure_active(arena_pressure_controller, arena_game)
    arena_game.round_num = 380
    assert not strategy.special_pressure_active(arena_pressure_controller, arena_game)
    arena_game.round_num = 100
    strategy.reset_target_state()
    capacity_controller = _Controller(
        2, unswbc.Team.A, 5,
        [_Tile(_Dragon(unswbc.Position(5, 5), 9, unswbc.Team.B))],
    )
    capacity_controller.unit_count = strategy.special_population_target(arena_game)
    assert not strategy.special_pressure_signal(capacity_controller, arena_game)
    strategy.reset_target_state()
    assert not strategy.special_pressure_policy(
        _RelayController(2, unswbc.Team.B, 5, [], safe_start, safe_visible, unswbc.Direction.EAST),
        arena_game,
    )
    strategy.reset_target_state()
    for round_number in range(1, 21):
        arena_game.round_num = round_number
        strategy.special_pressure_signal(high_signal_controller, arena_game)
    assert strategy.special_pressure_role(
        _RelayController(0, unswbc.Team.A, 5, [], safe_start, safe_visible, unswbc.Direction.EAST),
        arena_game,
    ) == (strategy.ROLE_HUNTER if (strategy.role_hash(0) ^ 0) % 5 < 3 else strategy.ROLE_COLLECTOR)
    arena_pressure_roles = []
    for dragon_id in range(1, 31):
        controller = _RelayController(
            dragon_id, unswbc.Team.A, 5, [], safe_start, safe_visible, unswbc.Direction.EAST
        )
        expected_role = (strategy.ROLE_HUNTER
                         if (strategy.role_hash(dragon_id) ^ dragon_id) % 5 < 3
                         else strategy.ROLE_COLLECTOR)
        role = strategy.special_pressure_role(controller, arena_game)
        arena_pressure_roles.append(role)
        assert role == expected_role
    assert arena_pressure_roles.count(strategy.ROLE_HUNTER) == 18
    queen_game = unswbc.Game(25, 35, 64)
    queen_pressure_controller = _RelayController(
        2, unswbc.Team.B, 5, [], safe_start, safe_visible, unswbc.Direction.EAST
    )
    assert strategy.special_pressure_policy(queen_pressure_controller, queen_game)
    strategy.reset_target_state()
    assert strategy.special_pressure_signal(
        _Controller(
        2, unswbc.Team.B, 5,
            [_Tile(_Dragon(unswbc.Position(x, 5), 9 + x, unswbc.Team.A)) for x in (1, 3, 5, 7, 9)],
        ),
        queen_game,
    )
    assert strategy.special_pressure_role(queen_pressure_controller, queen_game) == (
        strategy.ROLE_HUNTER
        if (strategy.role_hash(2) ^ 2) % 5 < 3 else strategy.ROLE_COLLECTOR
    )
    assert not strategy.special_pressure_policy(
        _RelayController(2, unswbc.Team.A, 5, [], safe_start, safe_visible, unswbc.Direction.EAST),
        queen_game,
    )
    assert not strategy.special_pressure_policy(arena_pressure_controller, colosseum_game)
    strategy.reset_target_state()
    arena_game.round_num = 100
    arena_b_id1 = _RelayController(
        1, unswbc.Team.B, 5, [], safe_start, safe_visible, unswbc.Direction.EAST
    )
    assert strategy.role_for_controller(arena_b_id1, arena_game) == strategy.role_for(1)
    hunter_split_controller = _RelayController(
        2, unswbc.Team.B, 5, [], safe_start, safe_visible, unswbc.Direction.EAST
    )
    hunter_split_controller.unit_count = strategy.population_target(arena_game) - 1
    assert strategy.role_for(hunter_split_controller.get_id()) == strategy.ROLE_HUNTER
    assert strategy.split_size(hunter_split_controller, arena_game) == 2
    unswbc.game = game
    assert strategy.strategy_weights(strategy.strategy_mode(0, 1, 30)) == (3, 0)
    assert strategy.strategy_weights(strategy.strategy_mode(2, 1, 30)) == (1, 2)
    assert strategy.strategy_weights(strategy.strategy_mode(30, 1, 30)) == (1, 4)

    near_packet = strategy.pack_target(
        strategy.SONAR_TARGET, 8, 5, 37, unswbc.Direction.WEST, 42
    )
    near_decoded = strategy.unpack_target(near_packet)
    strategy.target_memory = strategy.TargetMemory(near_decoded)
    remote_hunter = _RelayController(
        2, unswbc.Team.A, 3, [], safe_start, safe_visible, unswbc.Direction.EAST
    )
    remote_hint = strategy.sonar_intercept_value(remote_hunter, game, unswbc.Position(6, 5))
    assert 0 < remote_hint <= 24
    late_hunter = _RelayController(
        6, unswbc.Team.B, 3, [], safe_start, safe_visible, unswbc.Direction.EAST
    )
    assert strategy.sonar_intercept_value(late_hunter, game, unswbc.Position(6, 5)) == 0
    stale_packet = strategy.pack_target(strategy.SONAR_TARGET, 8, 5, 37, unswbc.Direction.WEST, 40)
    strategy.target_memory = strategy.TargetMemory(strategy.unpack_target(stale_packet))
    assert strategy.sonar_intercept_value(remote_hunter, game, unswbc.Position(6, 5)) == 0
    strategy.target_memory = strategy.TargetMemory(decoded)
    assert strategy.sonar_intercept_value(remote_hunter, game, unswbc.Position(6, 5)) == 0
    collector_controller = _RelayController(
        0, unswbc.Team.A, 3, [], safe_start, safe_visible, unswbc.Direction.EAST
    )
    strategy.target_memory = strategy.TargetMemory(near_decoded)
    assert strategy.sonar_intercept_value(collector_controller, game, unswbc.Position(6, 5)) == 0
    strategy.target_memory = strategy.TargetMemory(near_decoded, target_id=9, local=True)
    assert strategy.sonar_intercept_value(remote_hunter, game, unswbc.Position(6, 5)) == 0
    danger_enemy = _Dragon(unswbc.Position(6, 5), 9, unswbc.Team.B)
    remote_hunter.tiles = [_Tile(danger_enemy)]
    strategy.target_memory = strategy.TargetMemory(decoded)
    assert strategy.sonar_intercept_value(remote_hunter, game, unswbc.Position(6, 5)) == 0
    strategy.reset_target_state()

    enemy = _Dragon(unswbc.Position(3, 3), 5, unswbc.Team.B)
    target = unswbc.Position(3, 3)
    hunter = _Controller(2, unswbc.Team.A, 3, [_Tile(enemy)])
    assert strategy.favourable_head_attack(hunter, game, target, 5)
    assert not strategy.favourable_head_attack(hunter, game, target, 4)
    assert not strategy.favourable_head_attack(_Controller(6, unswbc.Team.A, 3, [_Tile(enemy)]), game, target, 5)
    assert not strategy.favourable_head_attack(hunter, game, target, 5, local_visible=False)
    assert not strategy.favourable_head_attack(_Controller(0, unswbc.Team.A, 3, [_Tile(enemy)]), game, target, 5)
    assert not strategy.favourable_head_attack(_Controller(1, unswbc.Team.A, 7, [_Tile(enemy)]), game, target, 5)
    game.round_num = 470
    assert not strategy.favourable_head_attack(hunter, game, target, 5)

    chase_head = _Dragon(unswbc.Position(4, 3), 5, unswbc.Team.A)
    early_b = _Controller(1, unswbc.Team.B, 3, [_Tile(chase_head)])
    late_b = _Controller(6, unswbc.Team.B, 3, [_Tile(chase_head)])
    late_a = _Controller(6, unswbc.Team.A, 3, [_Tile(_Dragon(
        unswbc.Position(4, 3), 5, unswbc.Team.B
    ))])
    assert strategy.enemy_chase_value(early_b, game, unswbc.Position(3, 3)) == 168
    assert strategy.enemy_chase_value(late_b, game, unswbc.Position(3, 3)) == 0
    assert strategy.enemy_chase_value(late_a, game, unswbc.Position(3, 3)) == 168
    far_head = _Dragon(unswbc.Position(7, 3), 5, unswbc.Team.A)
    far_late_b = _Controller(6, unswbc.Team.B, 3, [_Tile(far_head)])
    assert 0 < strategy.enemy_chase_value(far_late_b, game, unswbc.Position(3, 3)) < 132

    game.round_num = 42
    local_enemy = _Dragon(unswbc.Position(6, 5), 9, unswbc.Team.B,
                          heading=unswbc.Direction.NORTH)
    local_visible = dict(safe_visible)
    local_visible[(6, 5)] = _RelayTile(local_enemy)
    local_controller = _RelayController(
        2, unswbc.Team.A, 3, [_Tile(local_enemy)], safe_start, local_visible,
        unswbc.Direction.EAST
    )
    assert strategy.score_move(local_controller, game, unswbc.Direction.EAST, []) == 1800


if __name__ == "__main__":
    main()
