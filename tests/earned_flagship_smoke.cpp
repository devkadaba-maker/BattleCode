#define EARNED_FLAGSHIP_LENGTH 20
#define main battlecode_bot_main
#include "../cpp_bot/main.cpp"
#undef main

#include <cassert>

int main() {
    assert(!earned_flagship(16));
    assert(!earned_flagship(19));
    assert(earned_flagship(20));
    assert(earned_flagship(24));
}
