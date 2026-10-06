#define LATE_HARVEST_MODE 2
#define LATE_HARVEST_ROUND 400
#define main battlecode_bot_main
#include "../cpp_bot/main.cpp"
#undef main

#include <cassert>

int main() {
    Game scenario(32, 32, 64);
    scenario.round_num = 399;
    assert(late_harvest_weights(scenario, false, {2, 3}) == std::make_pair(2, 3));

    scenario.round_num = 400;
    assert(late_harvest_weights(scenario, false, {2, 3}) == std::make_pair(3, 0));
    assert(late_harvest_weights(scenario, false, {4, 3}) == std::make_pair(4, 0));
    assert(late_harvest_weights(scenario, true, {8, 0}) == std::make_pair(8, 0));
}
