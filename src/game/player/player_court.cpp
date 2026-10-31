#include "game/player_court.hpp"

extern "C" void* g_pTableDims; // @ 0x8271A304
extern "C" float g_phCapsuleShapeK; // @ 0x825C8080
extern "C" float g_playerCourtGridScale; // @ 0x825C806C
extern "C" uint8_t g_mirrorBuffer[32]; // @ 0x82606720
void pongPlayer_InterpolateCourtGridPosition(float*, uint32_t, float*, float*, float*, float*); // @ 0x8219E590

namespace {
float negateFloatWord(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, sizeof bits);
    bits ^= 0x80000000u;
    __builtin_memcpy(&value, &bits, sizeof value);
    return value;
}
}

// Select one of three width/depth profiles, preserving scalar store order
// when an output overlaps the live table. Only xyz are written.
// @ 0x821EFD20 | size: 0x1A4
void* pongPlayer_GetCourtBounds(void* object, uint32_t side, void* lower, void* upper,
                                uint32_t variant, uint32_t useProfiles) {
    auto* table = static_cast<float*>(object);
    auto* lo = static_cast<float*>(lower);
    auto* hi = static_cast<float*>(upper);
    const bool flipped = static_cast<uint8_t>(side) != 0;
    float center = table[6] * g_phCapsuleShapeK;
    if (flipped) center = negateFloatWord(center);
    const float halfLength = table[6] * 0.5f;
    const unsigned profile = static_cast<uint8_t>(useProfiles) == 0 ? 8
                             : (static_cast<uint8_t>(variant) != 0 ? 14 : 11);
    hi[0] = table[profile] * table[4];
    // Keep fneg after the rounded multiply, including the NaN sign bit.
    volatile float positiveWidth = table[profile] * table[4];
    lo[0] = negateFloatWord(positiveWidth);
    hi[1] = table[5];
    lo[1] = table[5];
    const unsigned highDepth = profile + (flipped ? 1 : 2);
    const unsigned lowDepth = profile + (flipped ? 2 : 1);
    hi[2] = __builtin_fmaf(table[highDepth], halfLength, center);
    lo[2] = -__builtin_fmaf(table[lowDepth], halfLength, -center);
    return object;
}

// Resolve a grid cell's position. The bounds callback can change its input,
// so read the interpolation factors and side after that callback.
// @ 0x8219E7B0 | size: 0x7C
extern "C" void* pongPlayer_E7B0_g(void* object) {
    auto* target = static_cast<uint8_t*>(object);
    alignas(16) float lower[4], upper[4];
    pongPlayer_GetCourtBounds(g_pTableDims, target[0], lower, upper, target[1], 1);
    float factors[2];
    __builtin_memcpy(factors, target + 4, sizeof factors);
    auto* result = reinterpret_cast<float*>(target + 0x10);
    pongPlayer_InterpolateCourtGridPosition(factors, target[0], result, lower, upper,
                                           reinterpret_cast<float*>(g_mirrorBuffer));
    return result;
}

// Build both 3x3 grids, each with four corners per cell. Temporary fourth
// lanes are padding in the original; initialize them for defined native reads.
// @ 0x8219E008 | size: 0x2BC
void pongPlayer_E008_g(void* object, int, int, int side) {
    auto* target = static_cast<uint8_t*>(object);
    alignas(16) float lower[4], upper[4];
    pongPlayer_GetCourtBounds(g_pTableDims, static_cast<uint32_t>(side), lower, upper,
                              target[0x3B0], 1);
    const float scale = g_playerCourtGridScale;
    constexpr float radius = 1.0f / 6.0f;
    alignas(16) float zeroOffset[4] = {};
    for (int row = 0; row < 3; ++row) {
        const float rowCenter = ((float(row) + float(row + 1)) * scale) * 0.5f;
        for (int column = 0; column < 3; ++column) {
            const float columnCenter = ((float(column) + float(column + 1)) * scale) * 0.5f;
            auto* cell = target + 0x3D0 + (row * 3 + column) * 0x60;
            __builtin_memcpy(cell + 8, &rowCenter, 4);
            __builtin_memcpy(cell + 4, &columnCenter, 4);
            __builtin_memcpy(cell + 0x368, &rowCenter, 4);
            __builtin_memcpy(cell + 0x364, &columnCenter, 4);
            alignas(16) float first[4] = {}, second[4] = {};
            for (int corner = 0; corner < 4; ++corner) {
                float factors[2] = {
                    corner == 0 || corner == 3 ? columnCenter - radius : columnCenter + radius,
                    corner < 2 ? rowCenter - radius : rowCenter + radius
                };
                pongPlayer_InterpolateCourtGridPosition(factors, static_cast<uint32_t>(side), first,
                    lower, upper, reinterpret_cast<float*>(target + 0x360));
                pongPlayer_InterpolateCourtGridPosition(factors, static_cast<uint32_t>(side), second,
                    lower, upper, zeroOffset);
                __builtin_memcpy(cell + 0x20 + corner * 16, first, 16);
                __builtin_memcpy(cell + 0x380 + corner * 16, second, 16);
            }
            cell[0] = static_cast<uint8_t>(side);
            cell[1] = target[0x3B0];
            __builtin_memcpy(g_mirrorBuffer, target + 0x360, 16);
            cell[0x360] = static_cast<uint8_t>(side);
            cell[0x361] = target[0x3B0];
            __builtin_memcpy(g_mirrorBuffer, target + 0x360, 16);
        }
    }
}
