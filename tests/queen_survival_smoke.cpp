#define main battlecode_bot_main
#ifndef BOT_SOURCE
#define BOT_SOURCE "../cpp_bot/main.cpp"
#endif
#include BOT_SOURCE
#undef main
#include <cassert>

int main() {
    Game scenario(64,64,64);game=&scenario;scenario.round_num=20;
    std::vector<Tile> tiles;
    for (int y=2;y<=5;++y) for (int x=2;x<=5;++x)
        tiles.emplace_back(Position(x,y),std::nullopt,-1,false,
            std::array<Edge,4>{Edge(false,EdgeType::KELP),Edge(false,EdgeType::KELP),Edge(false,EdgeType::KELP),Edge(false,EdgeType::KELP)});
    Controller controller(0,Team(Team::A),Direction::NORTH,Vision(std::move(tiles)),64);ct=&controller;
    controller.head.position=Position(3,3);controller.length=2;controller.unit_count=10;
    std::vector<Position> ring{{3,3},{4,3},{4,4},{3,4}};
    std::vector<Direction> directions{Direction::EAST,Direction::SOUTH,Direction::WEST,Direction::NORTH};
    for (int i=0;i<4;++i) {
        ct->get_tile(ring[i])->get_edge(directions[i])=Edge(false,EdgeType::EMPTY);
        ct->get_tile(ring[(i+1)%4])->get_edge(directions[i].get_opposite())=Edge(false,EdgeType::EMPTY);
    }
    std::vector<Position> body{{3,3},{3,4}};
    for (int turn=0;turn<12;++turn) {
        auto moves=quiet_queen_cycle(body);
        assert(moves.size()==1 && quiet_active && quiet_loop.size()==4);
        std::vector<Position> eaten;
        assert(queen_body_step(body,eaten,moves.front(),0,true));
        assert(body.size()==2 && eaten.empty());
        controller.head.position=body.front();
    }
    assert(body.front()==Position(3,3));
    // A remembered route must be abandoned when its next actual tile is blocked.
    Position next=body.front().add_dir(quiet_route.front());
    ct->get_tile(next)->dragon_part=DragonPart(next,7,Team(Team::B),Direction::WEST,false);
    assert(quiet_queen_cycle(body).empty());
    assert(!quiet_active);
    ct->get_tile(next)->dragon_part.reset();
    // Even a currently empty spawning bed cannot be used for a permanent cycle.
    ct->get_tile(next)->pearl_time=100;
    assert(quiet_queen_cycle(body).empty());
    ct->get_tile(next)->pearl_time=-1;
    // Future pearl growth must be modeled at its arrival round.
    ct->get_tile(next)->pearl_time=1;
    auto grown=body;std::vector<Position> eaten;
    assert(queen_body_step(grown,eaten,Direction::EAST,0,false,1));
    assert(grown.size()==3 && eaten.size()==1);
    // A paid second step may reuse a tail square vacated by the first step.
    ct->get_tile(next)->pearl_time=-1;
    std::vector<Position> paid{{3,3},{3,4},{4,4}};eaten.clear();
    assert(queen_body_step(paid,eaten,Direction::EAST,0,true));
    assert(queen_body_step(paid,eaten,Direction::SOUTH,1,true));
    assert(paid.size()==2 && paid.front()==Position(4,4));
    // Food on the first step retains that tail, so the same route is blocked.
    ct->get_tile(next)->pearl=true;paid={{3,3},{3,4},{4,4}};eaten.clear();
    assert(queen_body_step(paid,eaten,Direction::EAST,0,true));
    assert(!queen_body_step(paid,eaten,Direction::SOUTH,1,true));
    ct->get_tile(next)->pearl=false;
    // Entering the existing tail in the same step is still a collision.
    eaten.clear();auto unchanged=body;
    assert(!queen_body_step(unchanged,eaten,Direction::SOUTH,0,true));
    // Recover off-screen body segments only from a contiguous verified history.
    std::vector<Tile> partial;
    partial.emplace_back(Position(3,3),DragonPart(Position(3,3),0,Team(Team::A),Direction::EAST,true),-1);
    partial.emplace_back(Position(2,3),DragonPart(Position(2,3),0,Team(Team::A),Direction::EAST,false),-1);
    Controller remembered(0,Team(Team::A),Direction::EAST,Vision(std::move(partial)),64);
    remembered.head.position=Position(3,3);remembered.length=4;ct=&remembered;
    history={{1,2},{1,3},{2,3},{3,3}};
    std::vector<Position> expected{{3,3},{2,3},{1,3},{1,2}};
    assert(visible_queen_body()==expected);
    ct->get_tile(Position(2,3))->dragon_part.reset();
    assert(visible_queen_body().empty());
    dynamic_queen_map=false;
    assert(dynamic_queen_escape(Direction::EAST).empty());
}
