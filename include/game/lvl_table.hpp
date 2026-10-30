#pragma once

#include <cstddef>
#include <cstdint>

struct alignas(16) LvlTableVector {
    float lane[4];
};

struct LvlTableTransform {
    LvlTableVector row[4];
};

// Partial view of the object consumed by 0x82337008; field meanings are inferred.
// Keep this separate from the incomplete lvlTable virtual-class declaration.
struct LvlTableMotionView {
    uint8_t _pad00[0x50];
    LvlTableVector linearResponse;       // +0x50
    LvlTableVector slidingResponse;      // +0x60
    LvlTableVector threshold;            // +0x70
    uint8_t _pad80[0xC0];
    const LvlTableTransform* transforms; // +0x140
    uint8_t _pad144[4];
    const uint32_t* transformIndices;    // +0x148
    uint8_t _pad14C[4];
    uint32_t activeTransform;            // +0x150
    uint8_t _pad154[0xC];
    LvlTableVector motionOffset;         // +0x160
};

static_assert(sizeof(LvlTableVector) == 16);
static_assert(sizeof(LvlTableTransform) == 64);
#if UINTPTR_MAX == UINT32_MAX
static_assert(offsetof(LvlTableMotionView, transforms) == 0x140);
static_assert(offsetof(LvlTableMotionView, transformIndices) == 0x148);
static_assert(offsetof(LvlTableMotionView, activeTransform) == 0x150);
static_assert(offsetof(LvlTableMotionView, motionOffset) == 0x160);
#endif

// Original internal ABI: r3=self, r4=position, low16(r5)=mode,
// v1=direction, v2=step, v3=origin. A recomp bridge must marshal the vector
// registers into these explicit references; this is a portable C++ entry point.
// position is rounded down to a 16-byte boundary, as with lvx/stvx.
void lvlTable_7008_2h(const LvlTableMotionView* self, LvlTableVector* position, uint32_t mode,
                      const LvlTableVector& direction, const LvlTableVector& step, const LvlTableVector& origin);
