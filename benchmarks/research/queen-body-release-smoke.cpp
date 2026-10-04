#define QUEEN_ESCAPE_RELEASE 1
#define main battlecode_bot_main
#include "../../cpp_bot/main.cpp"
#undef main
#include <cassert>

int main() {
    Game state(9,9,64); state.round_num = 100;
    std::vector<Position> positions{{4,4},{5,4},{5,3},{4,3},{3,3},{3,4},{2,4},{1,4}};
    std::vector<Tile> tiles;
    for (auto position : positions)
        tiles.emplace_back(position, std::nullopt, -1, false,
            std::array<Edge,4>{Edge(false,EdgeType::KELP),Edge(false,EdgeType::KELP),
                              Edge(false,EdgeType::KELP),Edge(false,EdgeType::KELP)});
    Controller c(0,Team(Team::A),Direction::EAST,Vision(std::move(tiles)),64);
    c.head.position = Position(4,4); c.length = 4; c.unit_count = 1;
    ct = &c; game = &state; reset_target_state(); history.clear();
    for (int x = 1; x <= 4; ++x)
        c.get_tile(Position(x,4))->dragon_part = DragonPart(Position(x,4),0,Team(Team::A),Direction::EAST,x==4);
    for (std::size_t i = 0; i + 1 < positions.size(); ++i) {
        for (auto direction : Direction::get_direction_list()) {
            if (positions[i].add_dir(direction) == positions[i+1]) {
                c.get_tile(positions[i])->get_edge(direction) = Edge(false,EdgeType::EMPTY);
                c.get_tile(positions[i+1])->get_edge(direction.get_opposite()) = Edge(false,EdgeType::EMPTY);
            }
        }
    }
    c.get_tile(Position(4,4))->get_edge(Direction::WEST) = Edge(false,EdgeType::EMPTY);
    c.get_tile(Position(3,4))->get_edge(Direction::EAST) = Edge(false,EdgeType::EMPTY);
    auto release = queen_body_release(c);
    assert(release.size() == 4);
    assert(release[1].first == Position(3,4) && release[1].second == 3);
    std::vector<Position> trail{Position(4,4),Position(5,4)};
    std::vector<Position> forecast;
    assert(1 + queen_escape_depth(c,Position(5,4),trail,forecast,5,release) == 6);
    // Two pearls delay release enough to make this short loop unsafe.
    c.get_tile(Position(5,3))->pearl = true;
    c.get_tile(Position(4,3))->pearl = true;
    assert(1 + queen_escape_depth(c,Position(5,4),trail,forecast,5,release) == 4);
    // A bent body must follow each segment's arrow towards its predecessor.
    c.get_tile(Position(2,4))->dragon_part.reset();
    c.get_tile(Position(1,4))->dragon_part.reset();
    c.get_tile(Position(3,3))->dragon_part = DragonPart(Position(3,3),0,Team(Team::A),Direction::SOUTH,false);
    c.get_tile(Position(4,3))->dragon_part = DragonPart(Position(4,3),0,Team(Team::A),Direction::WEST,false);
    release = queen_body_release(c);
    assert(release.size() == 4 && release[2].first == Position(3,3) && release[3].first == Position(4,3));
}
