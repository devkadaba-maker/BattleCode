#define main battlecode_bot_main
#include "../cpp_bot/main.cpp"
#undef main

#include <cassert>
#include <sstream>

int main() {
    Game scenario(9, 9, 64);
    scenario.round_num = 100;
    game = &scenario;
    std::vector<Tile> tiles;
    for (int y = 1; y <= 7; ++y) for (int x = 1; x <= 7; ++x) {
        std::array<Edge, 4> edges{Edge(false, EdgeType::EMPTY), Edge(false, EdgeType::EMPTY),
                                  Edge(false, EdgeType::EMPTY), Edge(false, EdgeType::EMPTY)};
        tiles.emplace_back(Position(x,y), std::nullopt, -1, false, edges);
    }
    Controller controller(4, Team(Team::A), Direction::EAST, Vision(std::move(tiles)), 64);
    controller.head.position = Position(4,4);
    controller.length = 6;
    controller.unit_count = 1;
    ct = &controller;
    controller.get_tile(Position(4,4))->dragon_part = DragonPart(Position(4,4),4,Team(Team::A),Direction::EAST,true);
    reset_target_state(); history.clear();

    // A near-future pearl drives a route before any visible food exists.
    controller.get_tile(Position(6,4))->pearl_time = 1;
    auto values = visible_target_scores(controller, scenario);
    assert(values[direction_index(Direction::EAST)] > values[direction_index(Direction::WEST)]);

    // A target fully enclosed by kelp contributes no reachable reward.
    controller.get_tile(Position(6,4))->edges.fill(Edge(false, EdgeType::KELP));
    controller.get_tile(Position(6,3))->get_edge(Direction::SOUTH) = Edge(false, EdgeType::KELP);
    controller.get_tile(Position(7,4))->get_edge(Direction::WEST) = Edge(false, EdgeType::KELP);
    controller.get_tile(Position(6,5))->get_edge(Direction::NORTH) = Edge(false, EdgeType::KELP);
    controller.get_tile(Position(5,4))->get_edge(Direction::EAST) = Edge(false, EdgeType::KELP);
    values = visible_target_scores(controller, scenario);
    for (int value : values) assert(value == 0);

    // Friendly and enemy neighbours reduce desirability; self does not.
    Tile target(Position(2,4), std::nullopt, -1, true,
                {Edge(false,EdgeType::EMPTY),Edge(false,EdgeType::EMPTY),Edge(false,EdgeType::EMPTY),Edge(false,EdgeType::EMPTY)});
    int plain = visible_target_value(controller, scenario, target, 2);
    auto* neighbour = controller.get_tile(Position(2,3));
    neighbour->dragon_part = DragonPart(Position(2,3),4,Team(Team::A),Direction::EAST,false);
    assert(visible_target_value(controller, scenario, target, 2) == plain);
    neighbour->dragon_part = DragonPart(Position(2,3),6,Team(Team::A),Direction::EAST,true);
    assert(visible_target_value(controller, scenario, target, 2) < plain);
    neighbour->dragon_part = DragonPart(Position(2,3),7,Team(Team::B),Direction::EAST,true);
    assert(visible_target_value(controller, scenario, target, 2) < plain);
    neighbour->dragon_part.reset();

    // A teammate's current heading forecasts its next destination. Enemy heads
    // and our own head are handled by separate collision logic.
    neighbour = controller.get_tile(Position(2,4));
    neighbour->dragon_part = DragonPart(Position(2,4),6,Team(Team::A),Direction::EAST,true);
    assert(friendly_head_destinations(controller, Position(3,4)) == 1);
    assert(friendly_head_destinations(controller, Position(2,3)) == 0);
    neighbour->dragon_part = DragonPart(Position(2,4),7,Team(Team::B),Direction::EAST,true);
    assert(friendly_head_destinations(controller, Position(3,4)) == 0);
    neighbour->dragon_part.reset();

    // Repeated turns increment the individual parent's counter, then move.
    reset_target_state(); history.clear();
    std::ostringstream output;
    auto* old = std::cout.rdbuf(output.rdbuf());
    for (int n = 0; n < PARENT_SPLIT_LIMIT; ++n) {
        output.str(""); execute_turn();
        assert(output.str().starts_with("SPLIT 2"));
        assert(parent_split_count == n + 1);
    }
    output.str(""); execute_turn();
    assert(output.str().starts_with("MOVE "));
    assert(parent_split_count == PARENT_SPLIT_LIMIT);
    std::cout.rdbuf(old);
}
