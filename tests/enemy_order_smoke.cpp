#define main battlecode_bot_main
#include "../cpp_bot/main.cpp"
#undef main

#include <cassert>

int main() {
    Game schooltime(60, 40, 64);
    game = &schooltime;
    std::vector<Tile> tiles;
    for (int y = 1; y <= 7; ++y) for (int x = 1; x <= 7; ++x)
        tiles.emplace_back(Position(x, y), std::nullopt, -1, false);
    Controller controller(4, Team(Team::A), Direction::EAST, Vision(std::move(tiles)), 64);
    controller.head.position = Position(4, 4);
    ct = &controller;

    auto* enemy = controller.get_tile(Position(5, 3));
    enemy->dragon_part = DragonPart(Position(5, 3), 6, Team(Team::B), Direction::SOUTH, true);
    assert(!enemy_head_ahead(controller, Position(5, 4)));

    enemy->dragon_part = DragonPart(Position(5, 3), 2, Team(Team::B), Direction::SOUTH, true);
    assert(enemy_head_ahead(controller, Position(5, 4)));

    Game other(56, 40, 64);
    game = &other;
    enemy->dragon_part = DragonPart(Position(5, 3), 6, Team(Team::B), Direction::SOUTH, true);
    assert(enemy_head_ahead(controller, Position(5, 4)));
}
