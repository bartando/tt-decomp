#include "locomotion.hpp"
#include "../game/creature/pong_creature.hpp"
#include <cstdint>

extern const float g_floatOne;   // @ 0x8202D108
extern const float g_floatZero;  // @ 0x8202D110

namespace {
template<class T> T& timingField(void* object, uint32_t offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}
}

// The zero phase denotes the end of a cycle for this envelope calculation.
// LocomotionStateAnim::CalculateBlendFactor @ 0x820C1910 | size: 0x68
float LocomotionStateAnim::CalculateBlendFactor(void* timingData) {
    float phase = timingField<float>(timingData, 0x14);
    const float zero = g_floatZero, one = g_floatOne;
    if (phase == zero) phase = one;
    const float blendOut = timingField<float>(timingData, 0x0C);
    float width = timingField<float>(timingData, 0x08);
    if (phase >= one - blendOut) {
        width = blendOut;
        phase = one - phase;
    }
    if (phase >= width) return one;
    // The original divides on unordered as well as positive comparisons.
    if (!(phase <= zero)) return phase / width;
    return zero;
}

// r5 is unused. The frame is forwarded in r4 and r5 to the clip evaluator.
// LocomotionStateAnim_2858 @ 0x820C2858 | size: 0x54
float LocomotionStateAnim_2858(void* entry, void* frame, uint32_t /*unusedR5*/) {
    void* clip = timingField<void*>(entry, 0x1C);
    const float time = timingField<float>(clip, 0x0C) * timingField<float>(entry, 0x14);
    LocomotionStateAnim_88E0_g(clip, frame, frame, 0, 1, time);
    LocomotionStateAnim_28B0_w(entry);
    return timingField<float>(entry, 0x14);
}
