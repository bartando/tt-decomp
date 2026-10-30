#pragma once
#include <cstdint>

struct ShaderVector {
    float lane[4];
};

// Packed handles: descriptor index in bits 18..31, dirty index in bits 1..17.
struct ShaderTable {
    uint8_t dirtyBits[0x100];
    uint32_t* entries;             // +0x100 (guest)
    uint32_t _104;
    ShaderVector* values;          // +0x108 (guest)
};

void grmShaderParameter_SetFloatArray(ShaderTable* table, uint32_t handle,
                                     const float* values, uint32_t count); // @ 0x82159908
