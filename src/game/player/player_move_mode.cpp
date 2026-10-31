// Outer-player movement mode transitions, recovered from .text.s.
#include <cstdint>

struct pongPlayer;
extern "C" void* g_input_obj_ptr; // @ 0x825EAB28
extern "C" void* g_rendererState; // @ 0x8260641C
extern "C" void pongPlayer_7C78_g(pongPlayer*, uint8_t); // @ 0x820C7C78
extern bool pongPlayer_CheckServeInput(pongPlayer*); // @ 0x82195B60
extern void pg_6CF8(void*, int32_t); // @ 0x820C6CF8
extern void pongPlayer_BBE0_g(void*, uint8_t); // @ 0x8218BBE0

namespace {
template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}
}

// @ 0x82195C00 | size: 0x14C
void pongPlayer_5C00_g(void* player, int32_t mode) {
    if (mode != 1 && (at<uint8_t>(player, 0x18B8)
                     || at<uint8_t>(at<void*>(player, 0x1C4), 0xC5))) {
        at<uint8_t>(player, 0x18B8) = 0;
        pongPlayer_7C78_g(static_cast<pongPlayer*>(at<void*>(player, 0x1C4)), 0);
    }

    if (at<int32_t>(player, 0x1CC) != mode) {
        const int32_t slot = at<int32_t>(player, 0x1D0);
        if (at<int32_t>(g_input_obj_ptr, (slot + 14) * 4) == 0
            || pongPlayer_CheckServeInput(static_cast<pongPlayer*>(player))) {
            void* action = at<void*>(player, 0x1F0);
            at<uint8_t>(action, 0x4E3) = 0;
            at<float>(action, 0x4E4) = 0.0f;
            at<uint8_t>(action, 0x3D) = 0;
            at<float>(action, 0x4E8) = 0.0f;
            at<uint8_t>(action, 0x4E2) = 0;
        }
    }

    at<int32_t>(player, 0x1CC) = mode;
    pg_6CF8(at<void*>(player, 0x1C4), mode);
    void* slots = at<void*>(g_rendererState, 0x30);
    const int32_t slot = at<int32_t>(player, 0x1D0);
    at<int32_t>(slots, (slot + 0x81) * 4) = at<int32_t>(player, 0x1CC);
    const bool enable = mode != 0 && mode != 4 && mode != 3 && mode != 2 && mode != 7;
    pongPlayer_BBE0_g(player, enable);
}
