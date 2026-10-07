#define FLAGSHIP_BORDER_EXTRA_PENALTY 400
#define main battlecode_bot_main
#include "../cpp_bot/main.cpp"
#undef main

#include <cassert>

int main() {
    Game scenario(16, 16, 64);
    scenario.round_num = 100;
    game = &scenario;
    std::vector<Tile> tiles;
    for (int y = 0; y < 7; ++y) for (int x = 0; x < 7; ++x) {
        std::array<Edge, 4> edges{Edge(false, EdgeType::EMPTY), Edge(false, EdgeType::EMPTY),
                                  Edge(false, EdgeType::EMPTY), Edge(false, EdgeType::EMPTY)};
        tiles.emplace_back(Position(x, y), std::nullopt, -1, false, edges);
    }
    Controller controller(0, Team(Team::A), Direction::EAST, Vision(std::move(tiles)), 64);
    controller.head.position = Position(3, 3);
    controller.length = 12;
    controller.unit_count = 10;
    ct = &controller;
    controller.get_tile(Position(3, 3))->dragon_part =
        DragonPart(Position(3, 3), 0, Team(Team::A), Direction::EAST, true);

    // The perimeter adjustment applies only to a designated flagship.
    assert(is_flagship(controller, scenario));
    assert(extra_flagship_border_penalty(controller, scenario, Position(3, 0)) == 400);
    assert(extra_flagship_border_penalty(controller, scenario, Position(4, 3)) == 0);
    controller.head.dragon_id = 20;
    while (is_flagship(controller, scenario)) ++controller.head.dragon_id;
    assert(extra_flagship_border_penalty(controller, scenario, Position(3, 0)) == 0);
}
