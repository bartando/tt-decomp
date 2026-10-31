#include "crt/host_format.h"
#include <cstdint>
#include <cstring>

namespace {
struct RoundRobinState {
    uint8_t matches[28][30];
    uint8_t players[8][10];
    int32_t playerCount;             // +0x398
    int32_t field39C;
    int32_t field3A0;
    int32_t field3A4;
    uint8_t field3A8;
    uint8_t padding3A9[3];
    int32_t field3AC;
};
static_assert(__builtin_offsetof(RoundRobinState, playerCount) == 0x398, "round-robin layout");

void ClearPlayer(uint8_t* player) {
    player[1] = 0xFF;
    player[2] = 0xFF;
    std::memset(player + 3, 0, 6);
    player[9] &= 0x7F;
}
}

// @ 0x822110F8 | size: 0x64
uint8_t* PongNetRoundRobinCoordinator_ResetMatch(void* entry) {
    auto* bytes = static_cast<uint8_t*>(entry);
    bytes[5] = 0xFF;
    bytes[6] = 0xFF;
    std::memset(bytes + 7, 0, 20);
    bytes[27] = 1;
    bytes[28] = 1;
    bytes[29] &= 0x3F;
    return bytes;
}

// @ 0x822100E0 | size: 0x88
void PongNetRoundRobinCoordinator_00E0_g(void* context) {
    auto* state = static_cast<RoundRobinState*>(context);
    for (int i = 7; i >= 0; --i) {
        ClearPlayer(state->players[i]);
        state->players[i][0] = 0xFF;
    }
    for (int i = 27; i >= 0; --i) {
        auto* entry = PongNetRoundRobinCoordinator_ResetMatch(state->matches[i]);
        entry[0] = 0;
        entry[4] = 0xFF;
    }
}

// @ 0x8220FC20 | size: 0x4BC
void PongNetRoundRobinCoordinator_FC20_w(void* context) {
    auto* state = static_cast<RoundRobinState*>(context);
    for (auto& entry : state->matches) PongNetRoundRobinCoordinator_ResetMatch(entry);
    for (auto& player : state->players) ClearPlayer(player);
    state->playerCount = 4;
    state->field39C = -1;
    state->field3A0 = -1;
    state->field3A4 = -1;
    state->field3AC = 9;
    int index = 0;
    for (int round = 0; round < 7; ++round) {
        for (int match = 0; match < 4; ++match, ++index) {
            char name[8];
            _snprintf(name, sizeof name, "%d-%d", round, match);
            auto* entry = PongNetRoundRobinCoordinator_ResetMatch(state->matches[index]);
            int length = 0;
            while (length < 3 && name[length]) {
                entry[length] = static_cast<uint8_t>(name[length]);
                ++length;
            }
            entry[length] = 0;
            entry[4] = static_cast<uint8_t>(index);
        }
    }
    for (int i = 0; i < 8; ++i) {
        ClearPlayer(state->players[i]);
        state->players[i][0] = static_cast<uint8_t>(i);
    }
}
