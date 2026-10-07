#define QUEEN_PEARL_CLAIM_PERCENT 25
#define main battlecode_bot_main
#include "../cpp_bot/main.cpp"
#undef main

#include <cassert>

int main() {
    Game scenario(9, 9, 64);
    scenario.round_num = 100;
    game = &scenario;
    std::vector<Tile> tiles;
    for (int y = 1; y <= 7; ++y) for (int x = 1; x <= 7; ++x) {
        std::array<Edge, 4> edges{Edge(false, EdgeType::EMPTY), Edge(false, EdgeType::EMPTY),
                                  Edge(false, EdgeType::EMPTY), Edge(false, EdgeType::EMPTY)};
        tiles.emplace_back(Position(x, y), std::nullopt, -1, false, edges);
    }
    Controller controller(4, Team(Team::A), Direction::EAST, Vision(std::move(tiles)), 64);
    controller.head.position = Position(4, 4);
    controller.length = 6;
    controller.get_tile(Position(4, 4))->dragon_part =
        DragonPart(Position(4, 4), 4, Team(Team::A), Direction::EAST, true);
    ct = &controller;
    reset_target_state(); history.clear();

    Position pearl(6, 4);
    controller.get_tile(pearl)->pearl = true;
    auto* neighbour = controller.get_tile(Position(5, 4));
    neighbour->dragon_part = DragonPart(Position(5, 4), 0, Team(Team::A), Direction::EAST, true);
    assert(pearl_claimed_by_visible_queen(controller, scenario, pearl));
    int yielded = pearl_value(controller, scenario, Position(5, 4));

    neighbour->dragon_part = DragonPart(Position(5, 4), 8, Team(Team::A), Direction::EAST, true);
    assert(!pearl_claimed_by_visible_queen(controller, scenario, pearl));
    int unclaimed = pearl_value(controller, scenario, Position(5, 4));
    assert(yielded * 4 == unclaimed);

    neighbour->dragon_part = DragonPart(Position(5, 4), 0, Team(Team::B), Direction::EAST, true);
    assert(!pearl_claimed_by_visible_queen(controller, scenario, pearl));
}
