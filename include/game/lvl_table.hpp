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

// Original internal ABI: r3=count, r4=points, r5=indices, r6=output,
// v1=distanceLimitSq, v2=origin. Marshal vectors into the explicit references.
// For count > 0, indices/output need room for count rounded UP to 32.
// points is rounded down to 16-byte alignment; output may equal indices.
uint32_t lvlTable_7D28_2h(int32_t count, const LvlTableVector* points, const uint32_t* indices,
                        uint32_t* output, const LvlTableVector& distanceLimitSq, const LvlTableVector& origin);

// Partial cloth-controller view consumed by 0x823D85B8; names are inferred.
struct LvlTableConstraintView {
    uint8_t _pad00[0xC];
    const uint32_t* particleIndices;      // +0x0C
    uint8_t _pad10[0x20];
    const LvlTableVector* responseBase;   // +0x30
    const LvlTableVector* restLength;     // +0x34
    const LvlTableVector* responseScale;  // +0x38
};

#if UINTPTR_MAX == UINT32_MAX
static_assert(offsetof(LvlTableConstraintView, particleIndices) == 0x0C);
static_assert(offsetof(LvlTableConstraintView, responseBase) == 0x30);
static_assert(offsetof(LvlTableConstraintView, restLength) == 0x34);
static_assert(offsetof(LvlTableConstraintView, responseScale) == 0x38);
#endif

// Original internal ABI: r3=self, r4=constraint, r5=positions, v1=anchor.
// Marshal v1 into the explicit reference (r6 in the portable entry). All vector
// array bases are rounded down to 16 bytes, matching lvx/stvx addressing.
void lvlTable_85B8_2hr(const LvlTableConstraintView* self, uint32_t constraint,
                       LvlTableVector* positions, const LvlTableVector& anchor);

// Partial views for cloth/capsule collision; these names are inferred from the
// type-1 bound dispatch and projection onto a finite axis, not original symbols.
struct ClothParticleGroup {
    const uint32_t* indices;
    uint16_t count;
    uint16_t capacity;
};

struct ClothCapsuleCollisionView {
    uint8_t _pad00[8];
    int32_t firstMovableParticle;          // +0x08, signed comparison
    uint8_t _pad0C[0x10];
    LvlTableVector* positions;              // +0x1C
    uint8_t _pad20[4];
    const LvlTableVector* previousPositions; // +0x24
    uint8_t _pad28[0xE0];
    const ClothParticleGroup* groups;       // +0x108
};

struct ClothCapsuleBoundView {
    uint8_t _pad00[8];
    float broadRadius;                     // +0x08
    uint8_t _pad0C[0x34];
    LvlTableVector center;                 // +0x40
    uint8_t _pad50[0x20];
    LvlTableVector radius;                 // +0x70
    LvlTableVector axisLength;             // +0x80
    LvlTableVector axisStart;              // +0x90
    uint8_t _padA0[0x10];
    LvlTableVector axisDirection;          // +0xB0
};

#if UINTPTR_MAX == UINT32_MAX
static_assert(sizeof(ClothParticleGroup) == 8);
static_assert(offsetof(ClothCapsuleCollisionView, firstMovableParticle) == 0x08);
static_assert(offsetof(ClothCapsuleCollisionView, positions) == 0x1C);
static_assert(offsetof(ClothCapsuleCollisionView, previousPositions) == 0x24);
static_assert(offsetof(ClothCapsuleCollisionView, groups) == 0x108);
#endif
static_assert(offsetof(ClothCapsuleBoundView, broadRadius) == 0x08);
static_assert(offsetof(ClothCapsuleBoundView, center) == 0x40);
static_assert(offsetof(ClothCapsuleBoundView, radius) == 0x70);
static_assert(offsetof(ClothCapsuleBoundView, axisLength) == 0x80);
static_assert(offsetof(ClothCapsuleBoundView, axisStart) == 0x90);
static_assert(offsetof(ClothCapsuleBoundView, axisDirection) == 0xB0);

// Original ABI: r3=self, r4=bound, r5=group, r6=reduction, r7=expansion,
// r8=mode. The entry uses ordinary pointers; its two callees need the VMX
// bridges documented above. Vector addresses are rounded down as by lvx/stvx.
// Group indices need room for count rounded up to 32, including padding entries.
void clothCollideCapsule(const ClothCapsuleCollisionView* self, const ClothCapsuleBoundView* bound,
                         uint32_t group, const LvlTableVector* reduction,
                         const LvlTableVector* expansion, uint32_t mode);
