// Animation resets used when the inner player state changes movement mode.
#include <cstdint>
#include <cstring>

extern "C" uint8_t g_swingInFlightFlag; // @ 0x8260633C
extern "C" uint32_t g_swingCountFlag; // @ 0x82606340
extern void crAnimBlenderState_Init(void*); // @ 0x8224C810

namespace {
struct ModeLocomotion {
    virtual void Reserved0() = 0;
    virtual void Reserved1() = 0;
    virtual void Reserved2() = 0;
    virtual void Start(uint32_t, const void*, uint32_t) = 0;
};
template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}

void clearSwingTiming(void* timing) {
    const unsigned zeroFields[] = {0x0C, 0x10, 0x14, 0x20, 0x24,
                                   0x40, 0x44, 0x48, 0x50, 0x54, 0x58};
    for (unsigned offset : zeroFields) at<float>(timing, offset) = 0.0f;
    at<float>(timing, 0x18) = 1.0f;
    at<float>(timing, 0x1C) = 1.0f;
    at<uint8_t>(timing, 0x8D) = 0;
    g_swingInFlightFlag = 0;
    g_swingCountFlag = 0;
}
}

// @ 0x820CE2B8 | size: 0xC8
void game_E2B8(void* state) {
    at<uint8_t>(state, 0x13) = 1;
    at<ModeLocomotion*>(state, 0x94)->Start(0, nullptr, 0);
    void* phase = at<void*>(state, 0x88);
    crAnimBlenderState_Init(static_cast<uint8_t*>(phase) + 0x10);
    at<float>(phase, 0x19C) = 0.0f;
    clearSwingTiming(at<void*>(state, 0x7C));
}
