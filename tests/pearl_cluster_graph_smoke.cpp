#define PEARL_CLUSTER_GRAPH_MODE 2
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

    controller.get_tile(Position(6, 4))->pearl = true;
    controller.get_tile(Position(6, 3))->pearl = true;
    int open_value = pearl_cluster_value(controller, scenario, Position(5, 4));
    assert(open_value > 0);

    // Kelp isolates both pearls from the proposed east step. Geometric
    // distance still sees a close cluster, while graph-aware scoring rejects it.
    controller.get_tile(Position(6, 4))->edges.fill(Edge(false, EdgeType::KELP));
    controller.get_tile(Position(6, 3))->edges.fill(Edge(false, EdgeType::KELP));
    controller.get_tile(Position(5, 4))->get_edge(Direction::EAST) = Edge(false, EdgeType::KELP);
    controller.get_tile(Position(5, 3))->get_edge(Direction::EAST) = Edge(false, EdgeType::KELP);
    controller.get_tile(Position(7, 4))->get_edge(Direction::WEST) = Edge(false, EdgeType::KELP);
    controller.get_tile(Position(7, 3))->get_edge(Direction::WEST) = Edge(false, EdgeType::KELP);
    controller.get_tile(Position(6, 5))->get_edge(Direction::NORTH) = Edge(false, EdgeType::KELP);
    controller.get_tile(Position(6, 2))->get_edge(Direction::SOUTH) = Edge(false, EdgeType::KELP);
    assert(pearl_cluster_value(controller, scenario, Position(5, 4)) == 0);
}
