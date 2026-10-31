// Swing clip activation and the selected clip's locomotion blend marker.
#include <cstdint>
#include "game/game_message.hpp"

struct pongAnimState;
extern uint32_t util_CDF0(void*, const void*, uint32_t); // @ 0x8224CDF0

namespace {
template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}

void* selectedRecord(void* state) {
    return at<void**>(state, 4)[at<uint32_t>(state, 0x194)];
}
}

// Keep the complete clip-start result: only its low byte gates the side effects.
// @ 0x820DC7A0 | size: 0x140
uint32_t pg_C7A0_g(pongAnimState* animation, float inputTime) {
    void* state = animation;
    uint32_t result = 0;
    if (at<float>(state, 0x19C) <= 0.0f && !(at<uint16_t>(state, 0x5A) & 1)) {
        void* clip = at<void*>(selectedRecord(state), 0x10);
        result = util_CDF0(static_cast<uint8_t*>(state) + 0x10, clip, 0);
        if (static_cast<uint8_t>(result) && inputTime > 0.0f) {
            // Starting the clip can change the selected record; reload it.
            clip = at<void*>(selectedRecord(state), 0x10);
            const float duration = at<float>(clip, 0x0C);
            const float ratio = duration > 0.0f ? inputTime / duration : 0.0f;
            const double nonnegative = ratio >= 0.0f ? double(ratio) : 0.0;
            const float phase = nonnegative - 1.0 >= 0.0 ? 1.0f : float(nonnegative);
            at<float>(state, 0x60) = phase;
            at<float>(state, 0x64) = phase;
        }
    }
    if (static_cast<uint8_t>(result)) {
        const uint32_t shift = at<uint32_t>(state, 0x198) & 63u;
        const uint32_t mask = shift < 32 ? 1u << shift : 0;
        PostGameMessage(0x1011, static_cast<uint8_t>(mask), 0, nullptr);
    }
    return result;
}

// @ 0x820DC8E0 | size: 0x54
float game_C8E0_h(void* state) {
    void* record = selectedRecord(state);
    const float duration = at<float>(at<void*>(record, 0x10), 0x0C);
    if (!(duration > 0.0f)) return 0.0f;
    const float frames = static_cast<float>(at<int32_t>(record, 0x38));
    const float seconds = frames * 0.03333333507180214f;
    return seconds / duration;
}
