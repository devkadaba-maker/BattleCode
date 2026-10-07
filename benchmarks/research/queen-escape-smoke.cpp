#define QUEEN_ESCAPE_WEIGHT 4000
#define QUEEN_ESCAPE_ROUNDS 500
#define main battlecode_bot_main
#include "../../cpp_bot/main.cpp"
#undef main
#include <cassert>
int main() {
    Game scenario(9,9,64); scenario.round_num=100;
    std::vector<Tile> tiles;
    for(int y=1;y<=7;++y) for(int x=1;x<=7;++x)
        tiles.emplace_back(Position(x,y),std::nullopt,-1,false,
            std::array<Edge,4>{Edge(false,EdgeType::EMPTY),Edge(false,EdgeType::EMPTY),Edge(false,EdgeType::EMPTY),Edge(false,EdgeType::EMPTY)});
    Controller c(0,Team(Team::A),Direction::EAST,Vision(std::move(tiles)),64);
    c.head.position=Position(4,4); c.length=4; c.unit_count=1;
    ct=&c; game=&scenario; reset_target_state(); history.clear();
    c.get_tile(Position(4,4))->dragon_part=DragonPart(Position(4,4),0,Team(Team::A),Direction::EAST,true);
    for(int x=5;x<=7;++x) {
        auto* t=c.get_tile(Position(x,4)); t->edges.fill(Edge(false,EdgeType::KELP));
        t->get_edge(Direction::WEST)=Edge(false,EdgeType::EMPTY);
        if(x<7) t->get_edge(Direction::EAST)=Edge(false,EdgeType::EMPTY);
    }
    auto depths=opening_queen_escape_scores(c,scenario);
    assert(depths[direction_index(Direction::EAST)]==3);
    assert(depths[direction_index(Direction::WEST)]==6);
    // A friendly head moving into the first west step invalidates that route.
    c.get_tile(Position(3,3))->dragon_part=DragonPart(Position(3,3),6,Team(Team::A),Direction::SOUTH,true);
    depths=opening_queen_escape_scores(c,scenario);
    assert(depths[direction_index(Direction::WEST)]==0);
    // The forecast applies equally to an enemy head.
    c.get_tile(Position(3,3))->dragon_part=DragonPart(Position(3,3),7,Team(Team::B),Direction::SOUTH,true);
    depths=opening_queen_escape_scores(c,scenario);
    assert(depths[direction_index(Direction::WEST)]==0);
}
