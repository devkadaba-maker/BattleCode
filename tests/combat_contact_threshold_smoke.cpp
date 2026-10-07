#define COMBAT_CONTACT_THRESHOLD 3
#define main battlecode_bot_main
#include "../cpp_bot/main.cpp"
#undef main

#include <cassert>

int main() {
    assert(strategy_mode(40, std::nullopt, 40) == Mode::COLLECT);
    assert(strategy_mode(40, 1, 40) == Mode::COLLECT);
    assert(strategy_mode(40, 2, 40) == Mode::COLLECT);
    assert(strategy_mode(2, 3, 40) == Mode::COLLECT);
    assert(strategy_mode(3, 3, 40) == Mode::BALANCED);
    assert(strategy_mode(4, 3, 40) == Mode::PRESSURE);
    assert(strategy_mode(40, 3, 40) == Mode::HUNT);
}
