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

// Type-13 bound consumed by 0x823389E8. Descriptive field names are inferred
// from the endpoint tests and tapered-surface normal, not recovered symbols.
struct ClothTaperedCapsuleBoundView {
    uint8_t _pad00[8];
    float broadRadius;                     // +0x08
    uint8_t _pad0C[0x34];
    LvlTableVector center;                 // +0x40
    uint8_t _pad50[0x20];
    LvlTableVector lowerRadius;            // +0x70
    LvlTableVector upperRadius;            // +0x80
    LvlTableVector upperProjection;        // +0x90
    LvlTableVector slope;                  // +0xA0
    LvlTableVector radialScale;            // +0xB0
    LvlTableVector axisStart;              // +0xC0
    uint8_t _padD0[0x10];
    LvlTableVector axisDirection;          // +0xE0
};
static_assert(offsetof(ClothTaperedCapsuleBoundView, broadRadius) == 0x08);
static_assert(offsetof(ClothTaperedCapsuleBoundView, center) == 0x40);
static_assert(offsetof(ClothTaperedCapsuleBoundView, lowerRadius) == 0x70);
static_assert(offsetof(ClothTaperedCapsuleBoundView, upperRadius) == 0x80);
static_assert(offsetof(ClothTaperedCapsuleBoundView, upperProjection) == 0x90);
static_assert(offsetof(ClothTaperedCapsuleBoundView, slope) == 0xA0);
static_assert(offsetof(ClothTaperedCapsuleBoundView, radialScale) == 0xB0);
static_assert(offsetof(ClothTaperedCapsuleBoundView, axisStart) == 0xC0);
static_assert(offsetof(ClothTaperedCapsuleBoundView, axisDirection) == 0xE0);

// Same ABI, controller layout, padding and VMX callee bridges as capsule above.
void clothCollideTaperedCapsule(const ClothCapsuleCollisionView* self,
                                const ClothTaperedCapsuleBoundView* bound, uint32_t group,
                                const LvlTableVector* reduction, const LvlTableVector* expansion, uint32_t mode);

// Packed 16-byte cloth distance constraint. Names are inferred from 0x82340900.
struct ClothDistanceConstraint {
    uint16_t firstParticle;
    uint16_t secondParticle;
    float restLengthSq;
    float firstWeight;
    float compressionScale;
};
static_assert(sizeof(ClothDistanceConstraint) == 16);
static_assert(offsetof(ClothDistanceConstraint, restLengthSq) == 4);
static_assert(offsetof(ClothDistanceConstraint, firstWeight) == 8);
static_assert(offsetof(ClothDistanceConstraint, compressionScale) == 12);

// r3=count, r4=positions, r5=constraints, f1=relaxation. Positive counts consume
// constraints rounded UP to eight; all endpoints in a batch are read before any
// are written. Constraints are 16-byte aligned; position addresses round down.
// Only xyz are meaningful: the original's w arithmetic uses uninitialized stack
// scratch. This portable lift retains particle w; no extra ABI argument is needed.
void clothSolveDistanceConstraints(int32_t count, LvlTableVector* positions,
                                   const ClothDistanceConstraint* constraints, float relaxation);

// Triangle-mesh collision views inferred from the type-3/type-12 bound dispatch.
// Face indices are cached per particle; 0xFFFF is the absent-face sentinel.
struct ClothMeshFace {
    LvlTableVector normal;                 // +0x00
    uint16_t vertices[3];                  // +0x10
    uint8_t _pad16[2];
    uint16_t neighbours[3];                // +0x18
    uint8_t _pad1E[2];
};

struct ClothMeshBoundView {
    uint8_t _pad00[0x74];
    const LvlTableVector* vertices;        // +0x74
    uint8_t _pad78[4];
    const ClothMeshFace* faces;            // +0x7C
};

struct ClothMeshCollisionView {
    uint8_t _pad00[8];
    int32_t firstMovableParticle;          // +0x08
    uint8_t _pad0C[0x10];
    LvlTableVector* positions;             // +0x1C
    uint16_t particleCount;                // +0x20
    uint8_t _pad22[2];
    const LvlTableVector* previousPositions; // +0x24
    uint8_t _pad28[4];
    uint16_t* const* cachedFaces;          // +0x2C, first cache is used
};

static_assert(sizeof(ClothMeshFace) == 0x20);
static_assert(offsetof(ClothMeshFace, vertices) == 0x10);
static_assert(offsetof(ClothMeshFace, neighbours) == 0x18);
#if UINTPTR_MAX == UINT32_MAX
static_assert(offsetof(ClothMeshBoundView, vertices) == 0x74);
static_assert(offsetof(ClothMeshBoundView, faces) == 0x7C);
static_assert(offsetof(ClothMeshCollisionView, firstMovableParticle) == 0x08);
static_assert(offsetof(ClothMeshCollisionView, positions) == 0x1C);
static_assert(offsetof(ClothMeshCollisionView, particleCount) == 0x20);
static_assert(offsetof(ClothMeshCollisionView, previousPositions) == 0x24);
static_assert(offsetof(ClothMeshCollisionView, cachedFaces) == 0x2C);
#endif

// @ 0x82339240, formerly pongCreatureInst_9240_2hr (inferred name).
// Ordinary pointer ABI: r3=self, r4=bound, r5=reduction, r6=expansion, r7=mode.
// The response callee needs the internal VMX bridge documented above. All vector
// loads round their address down to 16 bytes, including unaligned array bases.
void clothCollideMesh(const ClothMeshCollisionView* self, const ClothMeshBoundView* bound,
                      const LvlTableVector* reduction, const LvlTableVector* expansion, uint32_t mode);

// Edge-collision views inferred from 0x82338D28. A type-9 composite supplies
// type-1 capsule and type-13 tapered-capsule children through this pointer chain.
struct ClothEdgeBound {
    uint8_t _pad00[4];
    uint8_t type;                           // +0x04
    uint8_t _pad05[0x6B];
    const ClothEdgeBound* const* children;   // +0x70, composite only
};

struct ClothEdgeBoundOwner {
    uint8_t _pad00[0xC];
    const ClothEdgeBound* bound;             // +0x0C
};

struct ClothEdgeBoundInstance {
    uint8_t _pad00[4];
    const ClothEdgeBoundOwner* owner;        // +0x04
};

struct ClothEdge {
    uint32_t firstParticle;
    uint32_t secondParticle;
};

struct ClothEdgeCollisionRange {
    uint32_t boundIndex;
    int32_t firstEdge;
    int32_t endEdge;                         // exclusive, signed comparison
};

struct ClothEdgeCollisionView {
    const ClothEdgeBoundInstance* instance;  // +0x00
    uint8_t _pad04[8];
    const ClothEdge* edges;                  // +0x0C
    uint8_t _pad10[0xC];
    LvlTableVector* positions;               // +0x1C
    uint8_t _pad20[0x60];
    float margin;                           // +0x80, splatted to all four lanes
    uint8_t _pad84[0x8C];
    const ClothEdgeCollisionRange* ranges;   // +0x110
    uint16_t rangeWordCount;                 // +0x114, rounded UP to triplets
    uint8_t _pad116[2];
    const uint32_t* edgeIndices;             // +0x118
};

static_assert(sizeof(ClothEdge) == 8);
static_assert(sizeof(ClothEdgeCollisionRange) == 12);
#if UINTPTR_MAX == UINT32_MAX
static_assert(offsetof(ClothEdgeBound, children) == 0x70);
static_assert(offsetof(ClothEdgeBoundOwner, bound) == 0x0C);
static_assert(offsetof(ClothEdgeBoundInstance, owner) == 4);
static_assert(offsetof(ClothEdgeCollisionView, edges) == 0x0C);
static_assert(offsetof(ClothEdgeCollisionView, positions) == 0x1C);
static_assert(offsetof(ClothEdgeCollisionView, margin) == 0x80);
static_assert(offsetof(ClothEdgeCollisionView, ranges) == 0x110);
static_assert(offsetof(ClothEdgeCollisionView, rangeWordCount) == 0x114);
static_assert(offsetof(ClothEdgeCollisionView, edgeIndices) == 0x118);
#endif

// Ordinary r3=self ABI. Vector addresses round down as with lvx/stvx. Nonempty
// ranges need a capsule child, or values retained from a preceding capsule range;
// other first-child types read uninitialized scratch in the original.
void clothCollideEdges(const ClothEdgeCollisionView* self); // @ 0x82338D28
