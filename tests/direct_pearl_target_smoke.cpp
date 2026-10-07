#define PEARL_TARGET_MODE 2
#define main battlecode_bot_main
#include "../cpp_bot/main.cpp"
#undef main

#include <cassert>

int main() {
    std::array<Edge, 4> edges{Edge(false, EdgeType::EMPTY), Edge(false, EdgeType::EMPTY),
                              Edge(false, EdgeType::EMPTY), Edge(false, EdgeType::EMPTY)};
    Tile empty(Position(1, 1), std::nullopt, -1, false, edges);
    Tile future(Position(2, 1), std::nullopt, 2, false, edges);
    Tile imminent(Position(3, 1), std::nullopt, 0, false, edges);
    Tile pearl(Position(4, 1), std::nullopt, -1, true, edges);

    assert(!direct_pearl_target(nullptr));
    assert(!direct_pearl_target(&empty));
    assert(!direct_pearl_target(&future));
    assert(direct_pearl_target(&imminent));
    assert(direct_pearl_target(&pearl));
}
