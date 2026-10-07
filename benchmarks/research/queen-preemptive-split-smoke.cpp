// Apply queen-preemptive-split.patch first.
#define PREEMPTIVE_QUEEN_SPLIT 1
#define main battlecode_bot_main
#include "../../cpp_bot/main.cpp"
#undef main
#include <cassert>
int main() {
    Game scenario(9,9,64); scenario.round_num=3;
    std::vector<Tile> tiles;
    for(int y=1;y<=7;++y) for(int x=1;x<=7;++x)
        tiles.emplace_back(Position(x,y),std::nullopt,-1,false,
            std::array<Edge,4>{Edge(false,EdgeType::KELP),Edge(false,EdgeType::KELP),Edge(false,EdgeType::KELP),Edge(false,EdgeType::KELP)});
    Controller queen(0,Team(Team::A),Direction::EAST,Vision(std::move(tiles)),64);
    queen.head.position=Position(4,4); queen.length=4; queen.unit_count=10;
    queen.get_tile(Position(4,4))->dragon_part=DragonPart(Position(4,4),0,Team(Team::A),Direction::EAST,true);
    queen.get_tile(Position(4,4))->get_edge(Direction::EAST)=Edge(false,EdgeType::EMPTY);
    queen.get_tile(Position(5,4))->get_edge(Direction::WEST)=Edge(false,EdgeType::EMPTY);
    ct=&queen; game=&scenario; history.clear(); parent_split_count=0;
    assert(should_preemptively_split_queen());
    queen.get_tile(Position(5,4))->get_edge(Direction::EAST)=Edge(false,EdgeType::EMPTY);
    queen.get_tile(Position(6,4))->get_edge(Direction::WEST)=Edge(false,EdgeType::EMPTY);
    assert(!should_preemptively_split_queen());
    parent_split_count=QUEEN_SPLIT_LIMIT;
    queen.get_tile(Position(5,4))->get_edge(Direction::EAST)=Edge(false,EdgeType::KELP);
    assert(!should_preemptively_split_queen());
    parent_split_count=0; queen.head.dragon_id=2;
    assert(!should_preemptively_split_queen());
}
