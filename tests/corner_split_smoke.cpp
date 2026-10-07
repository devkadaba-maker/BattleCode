#define main battlecode_bot_main
#include "../cpp_bot/main.cpp"
#undef main

#include <cassert>
#include <sstream>

std::string turn_output(bool north_open, int unit_count = 1, bool roomy_north_exit = false) {
    using namespace unswbc;
    Game scenario(7, 7, 64);
    scenario.round_num = 480;
    Position const head_position(3, 3);
    std::vector<Tile> tiles;
    for (int y = 0; y < 7; ++y) {
        for (int x = 0; x < 7; ++x) {
            Position const position(x, y);
            std::array<Edge, 4> edges{Edge(false, EdgeType::KELP), Edge(false, EdgeType::KELP),
                                      Edge(false, EdgeType::KELP), Edge(false, EdgeType::KELP)};
            std::optional<DragonPart> part;
            bool in_room = roomy_north_exit && x >= 1 && x <= 4 && y >= 0 && y <= 2;
            if (in_room) {
                if (y > 0) edges[0] = Edge(false, EdgeType::EMPTY);
                if (x < 4) edges[1] = Edge(false, EdgeType::EMPTY);
                if (y < 2) edges[2] = Edge(false, EdgeType::EMPTY);
                if (x > 1) edges[3] = Edge(false, EdgeType::EMPTY);
            }
            if (position == head_position) {
                edges = {Edge(false, EdgeType::KELP), Edge(true, EdgeType::KELP),
                         Edge(false, EdgeType::KELP), Edge(true, EdgeType::KELP)};
                if (north_open) edges[0] = Edge(false, EdgeType::EMPTY);
                part = DragonPart(position, 0, Team(Team::A), Direction::NORTH, true);
            }
            tiles.emplace_back(position, part, -1, false, edges);
        }
    }
    Controller controller(0, Team(Team::A), Direction::NORTH, Vision(std::move(tiles)), 64);
    controller.head.position = head_position;
    controller.length = 6;
    controller.unit_count = unit_count;
    game = &scenario;
    ct = &controller;
    history.clear();
    target_memory.reset();
    parent_split_count = 0;

    std::ostringstream output;
    auto* old_buffer = std::cout.rdbuf(output.rdbuf());
    execute_turn();
    std::cout.rdbuf(old_buffer);
    return output.str();
}

int main() {
    assert(turn_output(false, 32).starts_with("SPLIT 2"));
    assert(turn_output(true, 32).starts_with("MOVE N"));
    assert(turn_output(true, 32, true).starts_with("MOVE N"));
}
