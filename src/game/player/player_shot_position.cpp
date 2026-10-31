#include "game/player_shot_position.hpp"
#include "game/player_court.hpp"
#include "rage/ptr32.hpp"
#include "rage/vmx_float.hpp"

extern "C" void* g_pTableDims; // @ 0x8271A304
extern "C" void* g_ppBallInst; // @ 0x8271A2F4

namespace {
void addVmxRows(float* output, const float* first, const float* second) {
    for (unsigned lane = 0; lane < 4; ++lane)
        output[lane] = rage::vmxAddFloat(first[lane], second[lane]);
}
}

// Read the cached point unless forced, otherwise map normalized shot aim
// through the court bounds and add the current ball radius to table height.
// @ 0x821D6470 | size: 0x13C
void* pongPlayer_ComputeTargetPosition(void* output, void* object, uint32_t force) {
    const auto* entry = static_cast<const uint8_t*>(object);
    alignas(16) float result[4];
    if (entry[0xD8] != 0 && static_cast<uint8_t>(force) == 0) {
        __builtin_memcpy(result, entry + 0x120, sizeof result);
    } else {
        alignas(16) float lower[4], upper[4];
        const auto* table = static_cast<const float*>(pongPlayer_GetCourtBounds(
            g_pTableDims, entry[0xD6], lower, upper, 0, 0));
        const float height = table[5];
        void* ball = rage::load_ptr32<void>(g_ppBallInst, 0);
        float radius = 0.0f;
        if (ball != nullptr) {
            void* body = rage::load_ptr32<void>(ball, 4);
            const auto* shape = rage::load_ptr32<float>(body, 0x0C);
            radius = shape[2];
        }
        float factors[2];
        __builtin_memcpy(factors, entry + 0x100, sizeof factors);
        const bool flipped = entry[0xD6] != 0;
        const float baseX = flipped ? upper[0] : lower[0];
        const float baseZ = flipped ? upper[2] : lower[2];
        const float deltaX = flipped ? lower[0] - upper[0] : upper[0] - lower[0];
        const float deltaZ = flipped ? lower[2] - upper[2] : upper[2] - lower[2];
        const float x = deltaX * (factors[0] + 1.0f);
        const float z = deltaZ * (factors[1] + 1.0f);
        result[1] = height + radius;
        result[0] = __builtin_fmaf(x, 0.5f, baseX);
        result[2] = __builtin_fmaf(z, 0.5f, baseZ);
        result[3] = 0.0f; // The original recomputation leaves this padding lane undefined.
    }
    __builtin_memcpy(output, result, sizeof result);
    return output;
}

// @ 0x821D62A8 | size: 0x60
void playerShotEntry_UpdatePositionWithOffsets(void* object, uint32_t force) {
    auto* entry = static_cast<uint8_t*>(object);
    alignas(16) float point[4], first[4], second[4], partial[4], result[4];
    pongPlayer_ComputeTargetPosition(point, entry, force);
    __builtin_memcpy(first, entry + 0xE0, sizeof first);
    __builtin_memcpy(second, entry + 0xF0, sizeof second);
    addVmxRows(partial, point, first);
    addVmxRows(result, partial, second);
    __builtin_memcpy(entry + 0x20, result, sizeof result);
}

// @ 0x821D6308 | size: 0x54
void playerShotEntry_UpdatePositionWithOffset(void* object) {
    auto* entry = static_cast<uint8_t*>(object);
    alignas(16) float point[4], offset[4], result[4];
    pongPlayer_ComputeTargetPosition(point, entry, 0);
    __builtin_memcpy(offset, entry + 0xE0, sizeof offset);
    addVmxRows(result, point, offset);
    __builtin_memcpy(entry + 0x20, result, sizeof result);
}
