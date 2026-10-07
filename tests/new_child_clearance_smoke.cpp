#define NEW_CHILD_CLEARANCE_WEIGHT 2
#define main battlecode_bot_main
#include "../cpp_bot/main.cpp"
#undef main

#include <cassert>

int main() {
    Game scenario(16, 16, 64);
    scenario.round_num = 10;
    game = &scenario;
    std::vector<Tile> tiles;
    for (int y = 0; y < 7; ++y) for (int x = 0; x < 7; ++x) {
        std::array<Edge, 4> edges{Edge(false, EdgeType::EMPTY), Edge(false, EdgeType::EMPTY),
                                  Edge(false, EdgeType::EMPTY), Edge(false, EdgeType::EMPTY)};
        tiles.emplace_back(Position(x, y), std::nullopt, -1, false, edges);
    }
    Controller controller(7, Team(Team::A), Direction::EAST, Vision(std::move(tiles)), 64);
    controller.head.position = Position(3, 3);
    controller.get_tile(Position(4, 3))->dragon_part =
        DragonPart(Position(4, 3), 4, Team(Team::A), Direction::NORTH, true);

    history = {controller.get_position()};
    assert(friendly_pressure(controller, scenario, Position(3, 3)) == -180);
    assert(new_child_clearance_adjustment(controller, scenario, Position(3, 3), false) == -360);

    history.push_back(Position(3, 2));
    assert(new_child_clearance_adjustment(controller, scenario, Position(3, 3), false) == 0);
    controller.head.dragon_id = 0;
    history = {controller.get_position()};
    assert(new_child_clearance_adjustment(controller, scenario, Position(3, 3), false) == 0);
}
