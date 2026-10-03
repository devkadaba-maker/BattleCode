#define main battlecode_bot_main
#include "../cpp_bot/main.cpp"
#undef main

#include <cassert>

int main() {
    Game scenario(9, 9, 64);
    game = &scenario;
    std::vector<Tile> tiles;
    for (int y = 1; y <= 7; ++y) for (int x = 1; x <= 7; ++x)
        tiles.emplace_back(Position(x, y), std::nullopt, -1, false);
    Controller controller(4, Team(Team::A), Direction::EAST, Vision(std::move(tiles)), 64);
    controller.head.position = Position(4, 4);
    controller.length = 8;
    controller.unit_count = 8;
    ct = &controller;
    reset_target_state();
    history.clear();
    controller.get_tile(Position(4, 4))->dragon_part =
        DragonPart(Position(4, 4), 4, Team(Team::A), Direction::EAST, true);
    auto* landing = controller.get_tile(Position(6, 4));
    landing->pearl = true;

    auto route = free_pearl_route(Direction::EAST);
    assert(route.size() == 2 && route[0] == Direction::EAST && route[1] == Direction::EAST);
    assert(route.size() <= static_cast<std::size_t>((controller.length + 3) / 4));

    // A short dragon cannot use a second free step.
    controller.length = 4;
    assert(free_pearl_route(Direction::EAST).empty());
    controller.length = 8;

    // Growth is not worth landing in a kelp pocket with only one exit.
    landing->edges.fill(Edge(false, EdgeType::KELP));
    landing->get_edge(Direction::WEST) = Edge(false, EdgeType::EMPTY);
    assert(free_pearl_route(Direction::EAST).empty());
    landing->edges.fill(Edge(false, EdgeType::EMPTY));

    // An enemy near the landing square makes the extra step unsafe.
    auto* neighbour = controller.get_tile(Position(6, 3));
    neighbour->dragon_part = DragonPart(Position(6, 3), 7, Team(Team::B), Direction::EAST, true);
    assert(free_pearl_route(Direction::EAST).empty());
    neighbour->dragon_part.reset();

    // Never sprint through an occupied intermediate tile or towards no food.
    auto* middle = controller.get_tile(Position(5, 4));
    middle->dragon_part = DragonPart(Position(5, 4), 6, Team(Team::A), Direction::EAST, false);
    assert(free_pearl_route(Direction::EAST).empty());
    middle->dragon_part.reset();
    landing->pearl = false;
    assert(free_pearl_route(Direction::EAST).empty());
}
