#include "../../physics/archetype_refs.hpp"
#include "rage/ptr32.hpp"
#include "../../physics/composite_bounds.hpp"
#include "game/player_manager_state.hpp"
#include <cstddef>
#include "../../anim/look_at_controller.hpp"
#include "../../anim/locomotion_heading.hpp"
#include "rage/mat33.hpp"


/**
 * pongMover — Movement and positioning system for creatures
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 * 
 * Handles creature positioning, matrix calculations, and movement state.
 */

#include "pong_creature.hpp"
#include "../player/pong_player.hpp"
#include "../../anim/locomotion.hpp"
#include "../../anim/animation_channel.hpp"
#include "globals.h"
#include "rage/mat33.hpp"
#include "game/pong_strings.hpp"
#include "rage/mat33.hpp"
#include "../player/pong_gameplay_queries.hpp"
#include <cstring>

// ── Vtable dispatch helpers ─────────────────────────────────────────────────
// VTABLE(obj)       — dereference vtable pointer from object
// VCALL(obj, slot)  — fetch function pointer at vtable[slot]
#define VTABLE(obj)          (*(void***)(obj))
#define VCALL(obj, slot, T)  ((T)(VTABLE(obj)[(slot)]))

// External dependencies
extern void rage_free(void* ptr);
extern void rage_DebugLog(const char* msg, ...);
extern void rage_DebugLogNop(const char* msg, ...);  // @ 0x8240E6D0 — debug logger (no-op in retail)
extern "C" int _stricmp(const char* s1, const char* s2);

// Forward declarations
bool IsMatrixIdentity(const float* matrix);  // @ 0x820C3C70 - Matrix identity check

// XML callback node — passed to pongCreatureInst attribute-read handlers
struct xmlCallbackNode {
    void**  vtable;   // +0x00
    void*   dataObj;  // +0x04  the data reader sub-object (has read vtable)
};

// Animation sub-data block at animData+16, used by UpdateAnimationState
struct AnimSubData {
    uint8_t  _pad00[12];           // +0x00
    uint8_t  m_bRandomize;         // +0x0C  should-randomize flag
    uint8_t  _pad0D[3];
    float    m_blendRange;         // +0x10  blend range / fixed time value
    uint8_t  _pad14[12];
    uint8_t  m_simpleAnimData[16]; // +0x20  Euler angles (passed to mat33FromEuler)
    uint8_t  m_bUseCapsule;        // +0x30  capsule collision flag
    uint8_t  m_bCapsuleEnabled;    // +0x31  capsule enabled flag
    uint8_t  _pad32[14];
    float    m_capsuleStart[4];    // +0x40  capsule start position (16 bytes)
    float    m_minTime;            // +0x50  min time / capsule end X
    float    m_maxTime;            // +0x54  max time / capsule end Y
};

// LocomotionStateAnim helper functions

// Ref-counting helpers
extern "C" void rage_AddRef(void* obj);
extern "C" void rage_Release(void* obj);

// Creature lifecycle helpers
extern "C" void pongCreature_BaseDtor(void* obj);  // @ 0x820C53E8
extern "C" void pongCreature_Fixup(void* obj, void* relocator);
extern "C" void pongCreatureInst_Cleanup(void* obj);  // @ 0x822C8FD0
extern "C" void LocomotionStateAnim_InitCapsuleImpl(void* obj, float radius, const void* center);
extern "C" void* LocomotionState_FindFirstActive(void* list);
extern "C" void* LocomotionStateAnim_FindAnim(void* obj);
extern "C" void LocomotionStateAnim_ComputeOffset(void* obj, void* outVec);
extern "C" void LocomotionStateAnim_ProcessNode(void* obj, void* node);
extern "C" void LocomotionStateAnim_AccumNode(void* obj, void* node);
extern "C" void LocomotionStateAnim_GrowArray(void* obj);
extern "C" void LocomotionStateMf_ScaleWeights(void* obj);
extern "C" void LocomotionStateMf_BlendPoses(void* obj);
extern "C" void LocomotionStateMf_UpdateTransforms(void* obj);
extern "C" void LocomotionStateMf_ApplyConstraints(void* obj);
extern "C" void LocomotionStateMf_Finish(void* obj);

// Global data @ 0x825CB800 and 0x82619BE0
extern const float g_identityMatrixRef[16];      // @ 0x825CB800 - Reference identity matrix (64 bytes)
extern const uint32_t g_vectorComparisonMask[4]; // @ 0x82619BE0 - SIMD comparison mask (16 bytes)

// Global zero constant @ 0x8202D110
static const float g_zero = 0.0f;

/**
 * pongMover::pongMover @ 0x820CB5F0 | size: 0x90
 * 
 * Constructor - initializes mover with default values.
 * Sets up position, velocity, and state flags.
 */
pongMover::pongMover(void* creaturePool) {
    // Set vtable pointer
    vtable = (void**)0x8202807C;  // pongMover vtable @ 0x820280DC - 0x60

    // Zero twelve motion floats at +0x10..+0x3C
    m_posX  = m_posY  = m_posZ  = 0.0f;
    m_unk1C = m_unk20 = m_unk24 = 0.0f;
    m_unk28 = m_unk2C = m_unk30 = 0.0f;
    m_unk34 = m_unk38 = m_unk3C = 0.0f;

    // Mark slot active (+0x40 = 1)
    m_flags = 1;

    // Zero tail fields
    m_velocityContext = nullptr;
    m_velocityOverride = nullptr;

    // If creature pointer is already set (placement-new on pre-allocated memory),
    // adjust it relative to the pool base: m_pCreature += pool[idx+2]
    if (m_pCreature) {
        uint32_t* pool   = (uint32_t*)creaturePool;
        uint32_t basePtr = pool[1];         // pool+4
        uint32_t stride  = pool[76 / 4];    // pool+76
        // twllei: stride must be > 0 (binary traps on divide-by-zero)
        uint32_t idx = ((uint32_t)(uintptr_t)m_pCreature - basePtr) / stride;
        m_pCreature = (void*)(uintptr_t)(pool[idx + 2] + (uint32_t)(uintptr_t)m_pCreature);
    }
}

/**
 * pongMover::~pongMover @ 0x820C9EF8 | size: 0x48
 * 
 * Destructor - cleans up mover resources.
 */
pongMover::~pongMover() {
    // Restore vtable to base class
    vtable = (void**)0x8202807C;
    
    // Note: Actual cleanup handled by flags parameter
    // If flags & 1, the calling code will free(this)
}

/**
 * pongMover::Reset @ 0x820C9F40 | size: 0x13C
 * 
 * Resets mover state to initial position and orientation.
 * Calculates the rest matrix, optionally teleports the creature, then clears motion.
 */
extern "C" void* g_sceneRenderObj; // @ 0x82606430

void pongMover::Reset(bool alternate) {
    alignas(16) float initMatrix[16];
    CalcInitMatrix(initMatrix, this, alternate);
    const auto* table = static_cast<const uint32_t*>(g_sceneRenderObj);
    const uint32_t index = table[m_creatureIndex + 0x21];
    if (!m_pCreature) {
        rage_DebugLogNop("WTF");
    } else if (table[index + 0x1D] != 0) {
        static_cast<pongCreature*>(m_pCreature)->RequestTeleport(
            "pongMover::Reset", reinterpret_cast<const pongCreatureMatrix*>(initMatrix),
            false, true, false);
    }
    m_posX = initMatrix[12];
    m_posY = initMatrix[14];
    m_posZ = m_unk1C = m_unk20 = m_unk24 = 0.0f;
    m_unk28 = m_unk2C = m_unk30 = m_unk34 = m_unk38 = m_unk3C = 0.0f;
    m_flags &= 0xF9;
    m_unk48 = m_unk4C = m_unk50 = m_unk54 = 0.0f;
    memset(m_unk60, 0, sizeof(m_unk60));
    m_bIsMoving = 1;
    m_moveTimer = m_targetTimer = 0.0f;
    m_bHasTarget = m_bTargetReached = m_bPathBlocked = 0;
    memset(m_pathData, 0, sizeof(m_pathData));
}

// These movement helpers still have capsule/pg auto-names in the symbol map.
extern float pongMover_GetBlendWeight(pongMover* mover); // @ 0x820CB598
extern float pongMover_GetInputSpeed(pongMover* mover); // @ 0x820CB4D0
extern float* pongMover_ComputeLocalVelocity(float* out, pongMover* mover); // @ 0x820CA640
extern float* pongMover_ComputeRemoteVelocity(float* out, pongMover* mover); // @ 0x820CA790
extern void pongMover_UpdateMovementState(pongMover* mover); // @ 0x820CA390
extern void pongMover_AdjustVelocity(pongMover* mover, float* x, float* z); // @ 0x820CA488

extern "C" {
extern float g_kTransitionStep; // @ 0x825CAEC0
extern void** g_pInputArrayTable; // @ 0x825EAB28
extern uint8_t lbl_82606326; // @ 0x82606326 — enable velocity adjustment
extern float lbl_825C9D64; // @ 0x825C9D64 — stationary speed/timer threshold
}

extern "C" float g_moverStartDelay; // @ 0x825C9D60
extern "C" const float g_moverStopDelay; // @ 0x820290F0
extern "C" void* g_gameDataMgr; // @ 0x8271A2E4
extern void* pongMatch_GetCharacterForSlot(void* match, uint32_t playerSlot); // @ 0x821C9C00

// These were misidentified as capsule flags/radius in two physics lifts.
// pongMover_GetBlendWeight (was phBoundCapsule_B598_g) @ 0x820CB598 | size: 0x58
float pongMover_GetBlendWeight(pongMover* mover) {
    return (mover->m_flags & 0x12) ? 1.0f : mover->m_unk1C;
}

// pongMover_GetInputSpeed (was pg_B4D0_g) @ 0x820CB4D0 | size: 0xC8
// Defined in its owning module; do not duplicate the export here.


// pongMover_UpdateMovementState (was game_A390) @ 0x820CA390 | size: 0xF4
void pongMover_UpdateMovementState(pongMover* mover) {
    if (__builtin_fabsf(mover->m_unk20) == 0.0f &&
        __builtin_fabsf(mover->m_unk24) == 0.0f) {
        if (!mover->m_bIsMoving) {
            mover->m_targetTimer += g_kTransitionStep;
            if (mover->m_targetTimer > g_moverStopDelay) {
                mover->m_moveTimer = 0.0f;
                mover->m_unk28 = 0.0f;
                mover->m_unk2C = 0.0f;
                mover->m_targetTimer = 0.0f;
                mover->m_bIsMoving = 1;
            }
        } else {
            mover->m_bHasTarget = 0;
        }
        return;
    }
    bool reset = mover->m_unk28 * mover->m_unk20 < 0.0f ||
                 mover->m_unk2C * mover->m_unk24 < 0.0f;
    if (!reset && mover->m_bIsMoving) {
        mover->m_moveTimer += g_kTransitionStep;
        reset = mover->m_moveTimer >= g_moverStartDelay;
    }
    if (reset) {
        mover->m_bHasTarget = 0;
        mover->m_bIsMoving = 0;
    }
    mover->m_targetTimer = 0.0f;
}

// The movement rate used by court-boundary braking. The interpolation's
// identical endpoints are intentional: retain its rounding and NaN behavior.
// pongMover_GetMovementRate (was game_B368) @ 0x820CB368 | size: 0x164
float pongMover_GetMovementRate(pongMover* mover) {
    const auto movementData = []() {
        return *reinterpret_cast<const uint8_t* const*>(
            static_cast<const uint8_t*>(g_gameDataMgr) + 0x14);
    };
    auto* match = reinterpret_cast<uint8_t*>(g_pInputArrayTable);
    const uint32_t index = mover->m_creatureIndex;
    const bool special = match[uint32_t(index * 36 + 0xC4)] != 0;
    if (mover->m_bHasTarget) {
        const float elapsed = mover->m_moveTimer * 0.5714285969734192f;
        const double nonnegative = elapsed >= 0.0f ? elapsed : 0.0;
        const float fraction = static_cast<float>(nonnegative - 1.0 >= 0.0 ? 1.0 : nonnegative);
        const float rate = *reinterpret_cast<const float*>(movementData() + 0x5C);
        const float delta = rate - rate;
        if (special)
            return __builtin_fmaf(delta, fraction, rate);
        const auto* character = static_cast<const uint8_t*>(
            pongMatch_GetCharacterForSlot(match, index));
        const auto* movement = *reinterpret_cast<const uint8_t* const*>(character + 0x28);
        return __builtin_fmaf(delta, fraction, rate) *
               *reinterpret_cast<const float*>(movement + 0x6C);
    }
    if (special)
        return *reinterpret_cast<const float*>(movementData() + 0x60);
    const auto* character = static_cast<const uint8_t*>(
        pongMatch_GetCharacterForSlot(match, index));
    const auto* movement = *reinterpret_cast<const uint8_t* const*>(character + 0x28);
    const float scale = *reinterpret_cast<const float*>(movement + 0x6C);
    return scale * *reinterpret_cast<const float*>(movementData() + 0x60);
}

extern double crt_sqrt(double value); // @ 0x824301D0

// Limit each velocity component to the stopping speed before its court edge.
// pongMover_AdjustVelocity (was phBoundCapsule_A488_g) @ 0x820CA488 | size: 0x1B4
void pongMover_AdjustVelocity(pongMover* mover, float* x, float* z) {
    alignas(16) float lower[4], upper[4], position[4];
    pongMatchSettings_GetCourtBounds(g_pInputArrayTable, mover->m_creatureIndex, lower, upper);
    const auto* creature = static_cast<const uint8_t*>(mover->m_pCreature);
    const auto* instance = *reinterpret_cast<const uint8_t* const*>(creature + 0xA4);
    memcpy(position, instance + 0x40, sizeof(position));
    const float rate = pongMover_GetMovementRate(mover);
    const auto adjust = [rate](float* velocity, float coordinate, float low, float high) {
        if (*velocity < 0.0f) {
            const float distance = __builtin_fabsf(coordinate - low);
            const float limit = -static_cast<float>(crt_sqrt((distance * rate) * 2.0f));
            const float delta = *velocity - limit;
            const float bounded = delta >= 0.0f ? *velocity : limit;
            *velocity = bounded >= 0.0f ? 0.0f : bounded;
        } else if (*velocity > 0.0f) {
            const float distance = __builtin_fabsf(coordinate - high);
            const float limit = static_cast<float>(crt_sqrt((distance * rate) * 2.0f));
            const double nonnegative = *velocity >= 0.0f ? *velocity : 0.0;
            *velocity = static_cast<float>(nonnegative - limit >= 0.0 ? limit : nonnegative);
        }
    };
    adjust(x, position[0], lower[0], upper[0]);
    adjust(z, position[2], lower[2], upper[2]);
}

namespace {
float moverFlushVmx(float value) {
    uint32_t bits;
    memcpy(&bits, &value, sizeof(bits));
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
        memcpy(&value, &bits, sizeof(value));
    }
    return value;
}

// The VMX normalization used by both target-velocity paths. Dot xyz, refine
// the reciprocal square root once, and scale all four lanes (including w).
void moverNormalize(float* vector) {
    double dot = 0.0;
    for (unsigned lane = 0; lane < 3; ++lane) {
        const float value = moverFlushVmx(vector[lane]);
        dot += static_cast<double>(value) * value;
    }
    const float length2 = moverFlushVmx(static_cast<float>(dot));
    float reciprocal = moverFlushVmx(static_cast<float>(
        1.0 / __builtin_sqrt(static_cast<double>(length2))));
    if (reciprocal == __builtin_inff()) reciprocal = 0.0f;
    const float squared = moverFlushVmx(reciprocal * reciprocal);
    const float product = moverFlushVmx(length2 * squared);
    for (unsigned lane = 0; lane < 4; ++lane) {
        const float half = lane < 3 ? 0.5f : 0.0f;
        const float one = lane < 3 ? 1.0f : 0.0f;
        const float halfReciprocal = moverFlushVmx(half * reciprocal);
        const float error = -moverFlushVmx(product - one);
        const float correction = moverFlushVmx(error * halfReciprocal);
        const float scale = moverFlushVmx(correction + reciprocal);
        vector[lane] = moverFlushVmx(moverFlushVmx(vector[lane]) * scale);
    }
}
}

// Select a target speed from travel time and separation, then apply the
// normalized direction. This helper was labelled as a capsule operation.
// pongMover_ComputeTargetVelocity (was phBoundCapsule_A9A0_g) @ 0x820CA9A0 | size: 0x1A4
float* pongMover_ComputeTargetVelocity(float* out, pongMover* mover,
                                     const float* origin, const float* target) {
    alignas(16) float direction[4];
    for (unsigned lane = 0; lane < 4; ++lane)
        direction[lane] = moverFlushVmx(moverFlushVmx(target[lane]) - moverFlushVmx(origin[lane]));
    const float separationX = __builtin_fabsf(target[0] - origin[0]);
    out[0] = out[1] = out[2] = 0.0f;
    const float x2 = direction[0] * direction[0];
    const float distance = static_cast<float>(crt_sqrt(__builtin_fmaf(direction[2], direction[2], x2)));
    const float requiredSpeed = distance / mover->m_posZ;
    moverNormalize(direction);
    float weight = 0.0f;
    if (requiredSpeed > pongMover_GetInputSpeed(mover)) {
        weight = 1.0f;
    } else {
        const float amount = separationX > 0.0f ? separationX * 1.4492753744125366f
                                                : distance * 0.7246376872062683f;
        const double raised = amount >= 0.0f ? amount : 0.0;
        const float clamped = static_cast<float>(raised - 1.0 >= 0.0 ? 1.0 : raised);
        weight = clamped * clamped;
    }
    const float speed = __builtin_fabsf(pongMover_GetInputSpeed(mover)) * weight;
    for (unsigned lane = 0; lane < 4; ++lane)
        out[lane] = moverFlushVmx(moverFlushVmx(direction[lane]) * moverFlushVmx(speed));
    return out;
}

// pongMover_ComputeLocalVelocity (was phBoundCapsule_A640_g) @ 0x820CA640 | size: 0x14C
float* pongMover_ComputeLocalVelocity(float* out, pongMover* mover) {
    const auto* creature = static_cast<const uint8_t*>(mover->m_pCreature);
    out[0] = mover->m_unk30;
    out[1] = 0.0f;
    out[2] = mover->m_unk34;
    const auto* instance = *reinterpret_cast<const uint8_t* const*>(creature + 0xA4);
    alignas(16) float position[4];
    memcpy(position, instance + 0x40, sizeof(position));
    if (!(pongMover_GetBlendWeight(mover) <= 0.0f)) {
        const float x = mover->m_posX - position[0];
        const float z = mover->m_posY - position[2];
        const float x2 = x * x;
        const float distance = static_cast<float>(crt_sqrt(__builtin_fmaf(z, z, x2)));
        if (distance <= mover->m_unk50) {
            memset(out, 0, 16);
            mover->m_flags |= 8;
            return out;
        }
        alignas(16) float target[4] = {mover->m_posX, position[1], mover->m_posY, 0.0f};
        alignas(16) float velocity[4];
        pongMover_ComputeTargetVelocity(velocity, mover, position, target);
        const float limit = mover->m_unk48;
        const auto clamp = [limit](float value) {
            const float delta = value - -limit;
            const float raised = delta >= 0.0f ? value : -limit;
            return double(raised) - limit >= 0.0 ? limit : raised;
        };
        out[0] = clamp(velocity[0]);
        out[2] = clamp(velocity[2]);
    }
    return out;
}

extern const uint8_t g_hudShell_UpdateBlock[0x60]; // @ 0x825CAEB8

// pongMover_ComputeRemoteVelocity (was phBoundCapsule_A790_g) @ 0x820CA790 | size: 0x20C
float* pongMover_ComputeRemoteVelocity(float* out, pongMover* mover) {
    out[0] = out[1] = out[2] = 0.0f;
    if (!(pongMover_GetBlendWeight(mover) > 0.0f)) return out;
    const auto* creature = static_cast<const uint8_t*>(mover->m_pCreature);
    const auto* instance = *reinterpret_cast<const uint8_t* const*>(creature + 0xA4);
    const int32_t type = *reinterpret_cast<const int32_t*>(creature + 0xC8);
    alignas(16) float position[4];
    memcpy(position, instance + 0x40, sizeof(position));
    // The original never initializes scratch w. Give that padding lane a
    // defined value; only xyz participates in distance/arrival decisions.
    alignas(16) float direction[4] = {mover->m_posX, position[1], mover->m_posY, 0.0f};
    for (unsigned lane = 0; lane < 4; ++lane)
        direction[lane] = moverFlushVmx(moverFlushVmx(direction[lane]) - moverFlushVmx(position[lane]));
    const float x2 = direction[0] * direction[0];
    const float distance2 = __builtin_fmaf(direction[2], direction[2], x2);
    const float threshold = type == 2 && !(mover->m_flags & 0x20) ? mover->m_unk54 : 1e-6f;
    if (!(distance2 > threshold)) {
        mover->m_flags |= 8;
        return out;
    }
    if (mover->m_velocityOverride) {
        alignas(16) float scratch[4];
        const float* result = mover->m_velocityOverride(scratch, mover->m_velocityContext, mover->m_unk48);
        memcpy(out, result, 16);
        return out;
    }
    const float distance = static_cast<float>(crt_sqrt(distance2));
    float frameRate;
    memcpy(&frameRate, g_hudShell_UpdateBlock + 0x0C, sizeof(frameRate));
    float speed = distance * frameRate;
    if (speed > mover->m_unk48) speed = mover->m_unk48;
    moverNormalize(direction);
    for (unsigned lane = 0; lane < 4; ++lane)
        out[lane] = moverFlushVmx(moverFlushVmx(direction[lane]) * moverFlushVmx(speed));
    return out;
}

// Blend input and local/remote movement, mirror it for the court side, and
// advance the stationary latch. +0x60 caches the creature's translation.
// pongMover::UpdateVelocity (was phBoundCapsule_A080_g) @ 0x820CA080 | size: 0x30C
void pongMover::UpdateVelocity() {
    const auto* creature = static_cast<const uint8_t*>(m_pCreature);
    const auto* instance = *reinterpret_cast<const uint8_t* const*>(creature + 0xA4);
    memcpy(m_unk60, instance + 0x40, sizeof(m_unk60));
    const float dt = g_kTransitionStep;
    if (m_flags & 2) {
        m_posZ -= dt;
        if (m_posZ <= 0.0f) m_flags &= 0xFD;
    }
    const float inputWeight = 1.0f - pongMover_GetBlendWeight(this);
    const double speed = pongMover_GetInputSpeed(this);
    const double limit = m_unk48;
    const float lowerDelta = static_cast<float>(speed - -limit);
    const double lower = lowerDelta >= 0.0f ? speed : -limit;
    const float clamped = static_cast<float>(lower - limit >= 0.0 ? limit : lower);
    // VMX multiply and add round separately and flush denormals at each step.
    const auto flush = [](float value) {
        uint32_t bits;
        memcpy(&bits, &value, sizeof(bits));
        if ((bits & 0x7F800000u) == 0) {
            bits &= 0x80000000u;
            memcpy(&value, &bits, sizeof(value));
        }
        return value;
    };
    const auto blend = [&flush](float value, float weight, float sum) {
        const float product = flush(flush(value) * flush(weight));
        return flush(product + flush(sum));
    };
    float x = blend(m_unk20 * clamped, inputWeight, 0.0f);
    float z = blend(m_unk24 * clamped, inputWeight, 0.0f);
    const bool remote = (m_flags & 0x10) != 0;
    const float movementWeight = pongMover_GetBlendWeight(this);
    alignas(16) float scratch[4] = {};
    const float* velocity = remote ? pongMover_ComputeRemoteVelocity(scratch, this)
                                   : pongMover_ComputeLocalVelocity(scratch, this);
    x = blend(velocity[0], movementWeight, x);
    z = blend(velocity[2], movementWeight, z);
    pongMover_UpdateMovementState(this);
    m_unk30 = x;
    m_unk34 = z;
    if (lbl_82606326)
        pongMover_AdjustVelocity(this, &m_unk30, &m_unk34);
    const float threshold = lbl_825C9D64;
    const float z2 = m_unk34 * m_unk34;
    const float length2 = __builtin_fmaf(m_unk30, m_unk30, z2);
    if (m_bIsMoving && length2 <= threshold)
        m_bHasTarget = (__builtin_fabsf(m_unk20) != 0.0f || __builtin_fabsf(m_unk24) != 0.0f);
    creature = static_cast<const uint8_t*>(m_pCreature);
    const uint32_t offset = *reinterpret_cast<const uint32_t*>(creature + 0xCC);
    const auto* players = reinterpret_cast<const uint8_t*>(g_pInputArrayTable);
    const bool forward = players[offset + 0x40] != 0;
    m_unk38 = forward ? m_unk30 : -m_unk30;
    m_unk3C = forward ? m_unk34 : -m_unk34;
    if (m_bTargetReached && m_unk30 == 0.0f && m_unk34 == 0.0f &&
        m_unk38 == 0.0f && m_unk3C == 0.0f) {
        float timer;
        memcpy(&timer, _unk80, sizeof(timer));
        timer += g_kTransitionStep;
        memcpy(_unk80, &timer, sizeof(timer));
        if (timer > threshold) {
            timer = 0.0f;
            memcpy(_unk80, &timer, sizeof(timer));
            m_bTargetReached = 0;
        }
    }
}

/**
 * pongMover::CalcInitMatrix @ 0x820CAC78 | size: 0x29C
 * 
 * Calculates initial transformation matrix for the mover.
 * Uses creature position, orientation, and player data.
 */
extern "C" void* g_input_obj_ptr; // @ 0x825EAB28
extern "C" uint8_t g_playerModeTransitionFlag; // @ 0x82606327
extern "C" uint8_t g_playerModeTransform[64]; // @ 0x82606910
extern "C" const float lbl_82606750[4]; // @ 0x82606750
extern "C" float g_phCapsuleShapeK; // @ 0x825C8080
extern "C" void pongMatchSettings_GetCourtBounds(void*, int, void*, void*); // @ 0x821C9CD0
extern void* pongMatch_GetCharacterForSlot(void*, uint32_t); // @ 0x821C9C00

namespace {
template<class T> T& moverAt(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}
float flushMoverVmx(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, sizeof bits);
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
        __builtin_memcpy(&value, &bits, sizeof value);
    }
    return value;
}
void mirrorMoverMatrix(float* outMatrix) {
    for (unsigned row = 0; row < 16; row += 8)
        for (unsigned lane = 0; lane < 4; ++lane)
            outMatrix[row + lane] = flushMoverVmx(
                flushMoverVmx(lbl_82606750[lane]) - flushMoverVmx(outMatrix[row + lane]));
}
}

float* pongMover::CalcInitMatrix(float* outMatrix, pongMover* mover, uint32_t alternate) {
    memcpy(outMatrix, g_identityMatrixRef, 64);
    if ((mover->m_flags & 0x10) && !IsMatrixIdentity(mover->m_remoteRestMatrix)) {
        rage_DebugLogNop("pongMover::CalcInitMatrix() - setting rest mtx to remote rest mtx [%f,%f,%f]",
                         double(mover->m_remoteRestMatrix[12]),
                         double(mover->m_remoteRestMatrix[13]),
                         double(mover->m_remoteRestMatrix[14]));
        memcpy(outMatrix, mover->m_remoteRestMatrix, 64);
        void* settings = g_input_obj_ptr;
        const uint32_t slot = mover->m_creatureIndex;
        void* character = pongMatch_GetCharacterForSlot(settings, slot);
        const uint8_t mirror = moverAt<uint8_t>(moverAt<void*>(character, 0x2C), 0x104);
        if (moverAt<uint8_t>(settings, slot + 0x40) != mirror)
            mirrorMoverMatrix(outMatrix);
        return outMatrix;
    }
    if (static_cast<uint8_t>(alternate) && g_playerModeTransitionFlag) {
        memcpy(outMatrix, g_playerModeTransform, 64);
        return outMatrix;
    }
    void* settings = g_input_obj_ptr;
    alignas(16) float lower[4], upper[4];
    pongMatchSettings_GetCourtBounds(settings, mover->m_creatureIndex, lower, upper);
    void* character = pongMatch_GetCharacterForSlot(settings, mover->m_creatureIndex);
    outMatrix[13] = moverAt<float>(moverAt<void*>(character, 0x2C), 0xFC);
    const uint8_t side = moverAt<uint8_t>(settings, mover->m_creatureIndex + 0x40);
    outMatrix[14] = side ? lower[2] : upper[2];
    if (static_cast<uint8_t>(alternate))
        outMatrix[12] = side ? -0.25f : g_phCapsuleShapeK;
    character = pongMatch_GetCharacterForSlot(settings, mover->m_creatureIndex);
    if (side != moverAt<uint8_t>(moverAt<void*>(character, 0x2C), 0x104))
        mirrorMoverMatrix(outMatrix);
    return outMatrix;
}


////////////////////////////////////////////////////////////////////////////////
// Matrix Comparison Utilities
////////////////////////////////////////////////////////////////////////////////

/**
 * IsMatrixIdentity @ 0x820C3C70 | size: 0xD4
 * 
 * Checks if a 4x4 transformation matrix is the identity matrix.
 * 
 * Uses SIMD-style comparison with masking to allow ignoring specific
 * components (e.g., translation values) during the check.
 * 
 * @param matrix Pointer to 64-byte (4x4) matrix to check
 * @return true if matrix matches identity (after masking), false otherwise
 */
bool IsMatrixIdentity(const float* matrix) {
    const uint32_t* matrixBits = (const uint32_t*)matrix;
    const uint32_t* refBits = (const uint32_t*)g_identityMatrixRef;
    const uint32_t* mask = g_vectorComparisonMask;
    
    // Compare all 16 floats (4 vectors of 4 floats each)
    // Apply mask to both matrices before comparison
    for (int i = 0; i < 16; i++) {
        uint32_t maskedMatrix = matrixBits[i] & mask[i % 4];
        uint32_t maskedRef = refBits[i] & mask[i % 4];
        
        if (maskedMatrix != maskedRef) {
            return false;  // Mismatch found
        }
    }
    
    return true;  // All components match
}

// Alias for compatibility with existing code
uint8_t game_3C70(const float* matrix) {
    return IsMatrixIdentity(matrix) ? 1 : 0;
}

/**
 * pongBlendLookAtDriver::CalculateBlendFactor @ 0x820D0CA0 | size: 0x2C
 * [vtable slot 18]
 *
 * Calculates a blend factor for look-at animation based on the difference
 * between the current look-at angle and a reference angle.
 *
 * Formula: abs(currentAngle - refAngle) * multiplier * blendWeight
 *
 * @return Blend factor (float in f1)
 */
float pongBlendLookAtDriver::CalculateBlendFactor() {
    // Load current look-at angle from +224
    float currentAngle = this->field_0x00e0;  // pongBlendLookAtDriver +0xE0

    // Load blend weight from +0x10
    float blendWeight = this->field_0x0010;
    
    // Load reference angle from global @ 0x8202D10C
    extern const float g_lookAtRefAngle;  // @ 0x8202D10C
    float refAngle = g_lookAtRefAngle;
    
    // Calculate angle difference
    float angleDiff = currentAngle - refAngle;
    
    // Take absolute value
    float absAngleDiff = (angleDiff < 0.0f) ? -angleDiff : angleDiff;
    
    // Load multiplier from global @ 0x8202D184
    extern const float g_lookAtMultiplier;  // @ 0x8202D184
    float multiplier = g_lookAtMultiplier;
    
    // Calculate final blend factor
    float blendFactor = absAngleDiff * multiplier * blendWeight;
    
    return blendFactor;
}


////////////////////////////////////////////////////////////////////////////////
// LocomotionStateAnim - Animation State Management
////////////////////////////////////////////////////////////////////////////////

/**
 * LocomotionStateAnim::FindAnimationByID @ 0x8224BEF8 | size: 0x9C
 * Binary-search the frame's sorted channel pointers. r4 supplies the type
 * byte and r5 the uint16 ID; upper argument bits are discarded.
 */
void* LocomotionStateAnim::FindAnimationByID(uint32_t type, uint32_t id) {
    auto* bytes = reinterpret_cast<uint8_t*>(this);
    const unsigned animCount = *reinterpret_cast<uint16_t*>(bytes + 12);
    if (animCount == 0)
        return nullptr;

    auto* animArray = *reinterpret_cast<void***>(bytes + 8);
    const uint32_t searchKey = ((type & 0xFF) << 16) | (id & 0xFFFF);
    int low = 0;
    int high = static_cast<int>(animCount) - 1;
    while (low <= high) {
        const int mid = (low + high) / 2;
        void* entry = animArray[mid];
        auto* channel = static_cast<uint8_t*>(entry);
        const uint32_t entryKey = (uint32_t(channel[5]) << 16)
            | *reinterpret_cast<uint16_t*>(channel + 6);
        if (entryKey == searchKey)
            return entry;
        if (entryKey > searchKey)
            high = mid - 1;
        else
            low = mid + 1;
    }
    return nullptr;
}

// Find both type channels with ID zero, then write translation and rotation.
// Keep the unused integer slot so param remains in r7; IDs arrive as full words.
// LocomotionStateAnim::SetupAnimationPair @ 0x8224C418 | size: 0x90
bool LocomotionStateAnim::SetupAnimationPair(uint32_t animID1, uint32_t animID2,
                                            void* unusedR6, const void* param) {
    (void)unusedR6;
    auto* first = static_cast<AnimationChannel*>(FindAnimationByID(animID1, 0));
    auto* second = static_cast<AnimationChannel*>(FindAnimationByID(animID2, 0));
    if (!first || !second)
        return false;
    first->SetVector(reinterpret_cast<const float*>(static_cast<const uint8_t*>(param) + 16));
    second->SetQuaternion(static_cast<const float*>(param));
    return true;
}

// Translation uses VMX alignment; quaternion stores use the exact output.
// LocomotionStateAnim_C358_g @ 0x8224C358 | size: 0xBC
bool LocomotionStateAnim_C358_g(void* self, uint32_t firstType, uint32_t secondType,
                               uint32_t /*unusedR6*/, float* out) {
    auto* list = static_cast<LocomotionStateAnim*>(self);
    auto* first = static_cast<AnimationChannel*>(list->FindAnimationByID(firstType, 0));
    auto* second = static_cast<AnimationChannel*>(list->FindAnimationByID(secondType, 0));
    if (!first || !second) return false;
    const float* translation = first->GetTranslation();
    uint8_t vector[16];
    std::memcpy(vector, reinterpret_cast<const void*>(reinterpret_cast<uintptr_t>(translation) & ~uintptr_t(15)), 16);
    const uintptr_t position = (reinterpret_cast<uintptr_t>(out) + 16) & ~uintptr_t(15);
    std::memcpy(reinterpret_cast<void*>(position), vector, 16);
    const float* quaternion = second->GetQuaternion();
    for (unsigned lane = 0; lane < 4; ++lane) out[lane] = quaternion[lane];
    return true;
}

/**
 * LocomotionState::ValidateAnimationTiming @ 0x820DF220 | size: 0x6C
 * 
 * Validates that the animation timing for the given animation indices is valid (>= 0.0f).
 * If the timing is negative, it defaults both indices to 11 (idle/default animation).
 * 
 * This function ensures that the locomotion system doesn't try to use animations
 * with invalid timing data, which could cause rendering or blending issues.
 * 
 * @param animSetIndex Index into the animation set array (r4)
 * @param animIndex Index of the specific animation within the set (r5)
 * @param outTiming Output parameter to receive the validated animation timing (f1)
 */
void LocomotionState::ValidateAnimationTiming(uint32_t& animSetIndex, uint32_t& animIndex, float& outTiming) {
    // Threshold for valid timing (must be >= 0.0f)
    const float TIMING_THRESHOLD = 0.0f;
    const uint32_t DEFAULT_ANIM_INDEX = 11;  // Default/idle animation
    
    // Get animation set array pointer from offset 0 (pointer to array of pointer arrays)
    void** animSetArray = *(void***)this;
    
    // Loop until we find valid timing
    while (true) {
        // Index into animation set array (each pointer is 4 bytes, but indexed by 8)
        // This suggests the array might be storing pairs or have padding
        void** animSet = (void**)((char*)animSetArray + (animSetIndex * 8));
        
        // Get specific animation entry (28 bytes per entry)
        char* animEntry = (char*)(*animSet) + (animIndex * 28);
        
        // Get timing field at offset +24
        float timing = *(float*)(animEntry + 24);
        
        // Check if timing is valid
        if (timing >= TIMING_THRESHOLD) {
            // Valid timing found, return it
            outTiming = timing;
            return;
        }
        
        // Invalid timing - need to use default animation
        if (animIndex != DEFAULT_ANIM_INDEX) {
            // First try: set animIndex to default
            animIndex = DEFAULT_ANIM_INDEX;
        } else if (animSetIndex != DEFAULT_ANIM_INDEX) {
            // Second try: set animSetIndex to default
            animSetIndex = DEFAULT_ANIM_INDEX;
        } else {
            // Both already at default - this shouldn't happen, but exit to prevent infinite loop
            // Load the timing anyway (even if invalid)
            outTiming = timing;
            return;
        }
        
        // Loop continues with updated indices
    }
}

// 0x820DEDC0 — compose a bone transform with its parent matrix.
void pongCreatureInst_EDC0_g(void* dst, void* bone, void* parent);

// What 0x8214C8F8 reads from its skeleton. Its callers (pongCreature::UpdateReplay
// and UpdateAnimation, through LocomotionStateAnim_C8F8_g) pass a skeleton,
// pongCreature+0xAC; LocomotionStateAnim's header layout (which also gets a
// C++ vptr) doesn't describe it.
struct skeletonPoseData {
    uint8_t         _pad00[0x04];
    const uint32_t* parents;    // +0x04  parent bone index per bone
    uint8_t         _pad08[0x04];
    uint16_t        boneCount;  // +0x0C
};

struct skeletonPoseView {
    uint8_t                 _pad00[0x04];
    const skeletonPoseData* data;        // +0x04
    void*                   rootHelper;  // +0x08
    uint8_t*                bones;       // +0x0C  0x50-byte bone records
    uint8_t                 _pad10[0x04];
    uint8_t*                matrices;    // +0x14  0x40-byte bone matrices
};

/**
 * LocomotionStateAnim_C8F8_g @ 0x8214C8F8 | size: 0xD0
 *
 * Root bone: with a helper at +0x08, 0x820DEDC0(matrix 0, record 0, helper);
 * otherwise the record's leading 64 bytes become matrix 0. Every further bone
 * i goes through 0x820DEDC0(matrix i, record i, matrix of parents[i]).
 */
void LocomotionStateAnim_C8F8_g(void* skeleton) {
    const skeletonPoseView* skel = static_cast<const skeletonPoseView*>(skeleton);

    if (skel->rootHelper != nullptr)
        pongCreatureInst_EDC0_g(skel->matrices, skel->bones, skel->rootHelper);
    else {
        // The original copies four aligned vectors in order, including overlap.
        const uintptr_t sourceBase = reinterpret_cast<uintptr_t>(skel->bones);
        const uintptr_t destinationBase = reinterpret_cast<uintptr_t>(skel->matrices);
        for (unsigned row = 0; row < 4; ++row) {
            uint8_t vector[16];
            const uintptr_t source = (sourceBase + row*16) & ~uintptr_t(15);
            const uintptr_t destination = (destinationBase + row*16) & ~uintptr_t(15);
            std::memcpy(vector, reinterpret_cast<const void*>(source), 16);
            std::memcpy(reinterpret_cast<void*>(destination), vector, 16);
        }
    }

    const skeletonPoseData* data = skel->data;
    const int boneCount = data->boneCount;
    const uint32_t* parents = data->parents;
    for (int i = 1; i < boneCount; ++i) {
        pongCreatureInst_EDC0_g(skel->matrices + 0x40 * i, skel->bones + 0x50 * i,
                                skel->matrices + 0x40 * parents[i]);
    }
}

/**
 * LocomotionStateAnim::ProcessAnimationList @ 0x82380540 | size: 0xD0
 * 
 * Processes a list of animations by applying them to the locomotion state.
 * This function iterates through all animations in the provided list and
 * applies either a simple or complex animation processing function based
 * on the animation's flags.
 * 
 * The function first sets up the animation state, then determines which
 * processing method to use (simple vs complex based on bit 0 of flags),
 * and finally applies the selected method to each animation in the array.
 * 
 * @param animationList Pointer to animation list structure containing animations to process
 */
namespace {
template<class T> T& animationField(void* object, uint32_t offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}
}
extern const float g_floatZero; // @ 0x8202D110

// Evaluate the saved clip/frame, apply its channels to the destination skeleton,
// then rebuild that skeleton. C128/C288 and C8F8 are existing shared routines.
// LocomotionStateAnim::ProcessAnimationList @ 0x82380540 | size: 0xD0
void LocomotionStateAnim::ProcessAnimationList(void* animationList) {
    if (!animationList) return;
    void* container = animationField<void*>(this, 0x24);
    LocomotionStateAnim_88E0_g(animationField<void*>(container, 0), animationList,
                               animationField<void*>(container, 4), 0, 1,
                               animationField<float>(this, 8));
    void* data = animationField<void*>(animationList, 4);
    container = animationField<void*>(this, 0x24);
    void* frame = animationField<void*>(container, 4);
    const auto apply = (animationField<uint32_t>(data, 0x14) & 1)
        ? LocomotionStateAnim_C288_g : LocomotionStateAnim_C128_g;
    const uint32_t count = animationField<uint16_t>(frame, 0x0C);
    if (count) {
        const float weight = g_floatZero;
        for (uint32_t i = 0; i < count; ++i) {
            void** entries = animationField<void**>(frame, 8);
            apply(entries[i], entries, animationList, weight);
        }
    }
    LocomotionStateAnim_C8F8_g(animationList);
}

// ─────────────────────────────────────────────────────────────────────────────
// LocomotionStateAnim — Animation State Management (Batch Implementation)
// ─────────────────────────────────────────────────────────────────────────────

// External references
extern void LocomotionState_OnEnter(void* state);
extern void rage_free(void* ptr);
extern void LocomotionStateAnim_BaseDtor(void* obj);
extern void phLoader_CheckAnimExists(void* loader, const char* name, int flag);
extern int phLoader_ReadFileName(void* loader, void* outBuffer, int maxLen, int param1, int param2);
extern void phBoundCapsule_ApplyCollision(void* capsule, void* params, void* data);

// Global constants
extern const float g_floatZero;      // @ 0x8202D110
extern const float g_floatOne;       // @ 0x8202D108

// ─────────────────────────────────────────────────────────────────────────────
// LocomotionStateAnim::~LocomotionStateAnim()  [vtable slot 0 @ 0x820DFF20]
// Destructor - cleans up animation state resources
// ─────────────────────────────────────────────────────────────────────────────
LocomotionStateAnim::~LocomotionStateAnim() {
    // Call parent destructor
    LocomotionStateAnim_BaseDtor(this);
    
    // Note: The 'flags' parameter (r4) determines if memory should be freed
    // This is handled by the scalar destructor (vfn_1), not here
}

// ─────────────────────────────────────────────────────────────────────────────
// LocomotionStateAnim::Reset()  [vtable slot 2 @ 0x820E0178]
// Resets animation state to initial values
// ─────────────────────────────────────────────────────────────────────────────
void LocomotionStateAnim::Reset() {
    // Clear animation state fields
    this->field_0x003c = 0;   // m_stateFlags = 0
    this->field_0x0140 = 0;  // m_animData = null
    this->field_0x0144 = 0;  // m_animDataPtr = null
}

// ─────────────────────────────────────────────────────────────────────────────
// LocomotionStateAnim::GetAnimationProgress()  [vtable slot 10 @ 0x820E0FB0]
// Returns normalized animation progress (0.0 to 1.0)
// ─────────────────────────────────────────────────────────────────────────────
float LocomotionStateAnim::GetAnimationProgress() {
    // Get current animation data
    void* animData = (void*)this->field_0x0140;  // m_animData

    // Get animation timing values
    float currentTime = *(float*)&this->field_0x00b8;  // m_currentTime
    float duration = *(float*)&this->field_0x0028;
    float animEndTime = *(float*)((char*)animData + 12);
    
    // Calculate progress: (endTime - currentTime) / duration
    float remaining = animEndTime - currentTime;
    float progress = remaining / duration;
    
    return progress;
}

// ─────────────────────────────────────────────────────────────────────────────
// LocomotionStateAnim::GetAnimationDuration()  [vtable slot 11 @ 0x820E0FD0]
// Returns total animation duration in seconds
// ─────────────────────────────────────────────────────────────────────────────
float LocomotionStateAnim::GetAnimationDuration() {
    // Get current animation data
    void* animData = (void*)this->field_0x0140;  // m_animData

    // Get timing values
    float duration = *(float*)&this->field_0x0028;
    float animEndTime = *(float*)((char*)animData + 12);
    
    // Calculate total duration: endTime / duration
    float totalDuration = animEndTime / duration;
    
    return totalDuration;
}

// ─────────────────────────────────────────────────────────────────────────────
// LocomotionStateAnim::IsAnimationComplete()  [vtable slot 15 @ 0x820DF208]
// Returns true if animation has finished playing
// ─────────────────────────────────────────────────────────────────────────────
bool LocomotionStateAnim::IsAnimationComplete() {
    // Check completion flag at offset +0x148
    uint8_t isComplete = this->field_0x0148;  // m_isComplete
    
    // Return inverted: 0 means complete, non-zero means still playing
    // This is a cntlzw + rlwinm pattern: count leading zeros and extract bit
    return (isComplete == 0);
}

// ─────────────────────────────────────────────────────────────────────────────
// LocomotionStateAnim::Initialize()  [vtable slot 5 @ 0x820E0EE8]
// Initializes animation state with default blend vectors
// ─────────────────────────────────────────────────────────────────────────────
void LocomotionStateAnim::Initialize() {
    // Call parent initialization
    LocomotionState_OnEnter(this);
    
    // Load global constants
    const float zero = g_floatZero;   // 0.0f
    const float one = g_floatOne;     // 1.0f
    
    // Initialize first blend vector at offset +192 (12 floats)
    float* blendVec1 = (float*)((char*)this + 192);
    blendVec1[0] = one;   // X scale
    blendVec1[1] = zero;  // Y offset
    blendVec1[2] = zero;  // Z offset
    blendVec1[4] = zero;  // Rotation X
    blendVec1[5] = one;   // Rotation Y scale
    blendVec1[6] = zero;  // Rotation Z
    blendVec1[8] = zero;  // Translation X
    blendVec1[9] = zero;  // Translation Y
    blendVec1[10] = one;  // Translation Z scale
    
    // Clear 16-byte aligned buffer at +240
    uint8_t* buffer1 = (uint8_t*)((char*)this + 240);
    for (int i = 0; i < 16; i++) {
        buffer1[i] = 0;
    }
    
    // Initialize second blend vector at offset +256 (12 floats)
    float* blendVec2 = (float*)((char*)this + 256);
    blendVec2[0] = one;   // X scale
    blendVec2[1] = zero;  // Y offset
    blendVec2[2] = zero;  // Z offset
    blendVec2[4] = zero;  // Rotation X
    blendVec2[5] = one;   // Rotation Y scale
    blendVec2[6] = zero;  // Rotation Z
    blendVec2[8] = zero;  // Translation X
    blendVec2[9] = zero;  // Translation Y
    blendVec2[10] = one;  // Translation Z scale
    
    // Clear 16-byte aligned buffer at +304
    uint8_t* buffer2 = (uint8_t*)((char*)this + 304);
    for (int i = 0; i < 16; i++) {
        buffer2[i] = 0;
    }
    
    // Initialize state fields
    *(float*)&this->field_0x00b8 = zero;   // m_currentTime
    this->field_0x0144 = 0;   // m_animDataPtr = null
    this->field_0x0140 = 0;   // m_animData = null
    *(float*)&this->field_0x014c = zero;   // m_blendWeight
    this->field_0x0148 = 1;    // m_isComplete = false
}

// ─────────────────────────────────────────────────────────────────────────────
// LocomotionStateAnim::Load()  @ 0x820E0190
// Loads animation data from file
// ─────────────────────────────────────────────────────────────────────────────
bool LocomotionStateAnim::Load(void* parentState, void* fileLoader) {
    // Get animation duration from parent state via fileLoader->vfn_5()
    float duration = VCALL(fileLoader, 5, float(*)(void*))(fileLoader);
    
    // Store duration at offset +0x0C
    *(float*)&this->field_0x000c = duration;

    // Initialize animation set indices
    this->field_0x0008 = 0;
    
    // Try to load primary animation set
    const char** animNames1 = (const char**)0x825C9B90;  // Global animation name table
    int animIndex1 = 0;
    
    for (int i = 0; i < 4; i++) {
        const char* animName = animNames1[i];
        uint8_t found = 0;
        
        // Call loader to check if animation exists
        phLoader_CheckAnimExists(fileLoader, animName, 1);
        // Result in r3 (0 = not found, 1 = found)
        
        if (found == 0) {
            animIndex1++;
        } else {
            break;
        }
    }
    
    this->field_0x0008 = animIndex1;

    // Initialize alternate animation set indices
    this->field_0x0004 = 0;
    
    // Try to load alternate animation set
    const char** animNames2 = (const char**)0x825C9BA0;  // Alternate animation name table
    int animIndex2 = 0;
    
    for (int i = 0; i < 4; i++) {
        const char* animName = animNames2[i];
        uint8_t found = 0;
        
        phLoader_CheckAnimExists(fileLoader, animName, 1);
        
        if (found == 0) {
            animIndex2++;
        } else {
            break;
        }
    }
    
    this->field_0x0004 = animIndex2;
    
    // Load animation file name
    char fileNameBuffer[256];
    int result = phLoader_ReadFileName(fileLoader, fileNameBuffer, 255, 10, 1);
    
    if (result == 0) {
        // Failed to read file name
        return false;
    }
    
    // Get animation manager from parent state
    void* stateData = *(void**)((char*)parentState + 24);
    void* animManager = *(void**)((char*)stateData + 96);
    
    // Load animation from file via animManager->vfn_4()
    void* loadedAnim = VCALL(animManager, 4, void*(*)(void*, const char*))(animManager, fileNameBuffer);
    
    if (loadedAnim == nullptr) {
        // Failed to load animation
        rage_DebugLog("LocomotionStateAnim::Load - failed to load anim file '%s'", fileNameBuffer);  /* UNVERIFIED — string not found in binary */
        return false;
    }
    
    // Store loaded animation pointer
    this->vtable = (void**)loadedAnim;
    
    return true;
}

// ─────────────────────────────────────────────────────────────────────────────
// LocomotionStateAnim::UpdateAnimationState()  @ 0x82380268
// Updates animation state and handles state transitions
// ─────────────────────────────────────────────────────────────────────────────
void LocomotionStateAnim::UpdateAnimationState(void* outputState) {
    const float zero = g_floatZero;
    
    // Get animation data pointer
    void* animData = (void*)this->field_0x0024;

    if (animData == nullptr) {
        // No animation data - check if we should idle
        uint8_t flag1 = *(uint8_t*)&this->vtable;
        uint8_t flag2 = this->field_0x0001;

        if (flag1 != 0 || flag2 != 0) {
            // Clear state and return
            *(float*)&this->field_0x0008 = zero;
            this->field_0x0014 = 0;
            return;
        }
        
        // Check frame counter
        uint32_t frameCount = this->field_0x001c;
        if (frameCount != 0) {
            uint32_t currentFrame = this->field_0x0018;
            currentFrame++;
            this->field_0x0018 = currentFrame;
            
            if (currentFrame < frameCount) {
                // Still counting frames
                goto cleanup;
            }
            
            // Frame count reached - trigger state change
            uint32_t currentState = this->field_0x0004;
            if (currentState == 2) {
                // Transition to state 0
                this->field_0x0004 = 0;
            }
        }
        
    cleanup:
        *(float*)&this->field_0x0008 = zero;
        this->field_0x0014 = 0;
        return;
    }
    
    // Animation data exists - process it
    AnimSubData* animSubData = (AnimSubData*)((char*)animData + 16);

    // Check if we should randomize timing
    uint8_t shouldRandomize = animSubData->m_bRandomize;

    if (shouldRandomize != 0) {
        // Randomize animation timing using RNG
        // This uses a linear congruential generator (LCG)
        uint32_t* rngState = (uint32_t*)0x825C9A48;  // Global RNG state

        float minTime = animSubData->m_minTime;
        float maxTime = animSubData->m_maxTime;
        float timeRange = maxTime - minTime;
        
        // Generate random value: (state * 0x5CEFA7) & 0x7FFFFF
        uint64_t seed = rngState[0];
        uint64_t next = seed * 0x5CEFA7 + rngState[1];
        uint32_t randomBits = (uint32_t)(next & 0x7FFFFF);
        
        rngState[0] = (uint32_t)next;
        rngState[1] = (uint32_t)(next >> 32);
        
        // Convert to float and scale
        float randomFloat = (float)randomBits;
        float scaledRandom = timeRange * randomFloat * (1.0f / 8388608.0f);  // Divide by 2^23
        float randomTime = scaledRandom + minTime;
        
        *(float*)&this->field_0x0010 = randomTime;
        
        // Generate second random value for blend weight
        seed = rngState[0];
        next = seed * 0x5CEFA7 + rngState[1];
        randomBits = (uint32_t)(next & 0x7FFFFF);
        
        rngState[0] = (uint32_t)next;
        rngState[1] = (uint32_t)(next >> 32);
        
        float blendRange = animSubData->m_blendRange;
        randomFloat = (float)randomBits;
        float randomBlend = randomFloat * blendRange * (1.0f / 8388608.0f);
        
        *(float*)&this->field_0x000c = randomBlend;

    } else {
        // Use fixed timing
        float fixedTime = animSubData->m_blendRange;
        *(float*)&this->field_0x000c = fixedTime;
    }
    
    // Update state based on timing
    float currentTime = *(float*)&this->field_0x000c;

    if (currentTime < zero) {
        // Negative time - transition to state 2
        uint32_t state = this->field_0x0004;
        if (state != 2) {
            this->field_0x0004 = 2;
        }
    } else if (currentTime == zero) {
        // Zero time - transition to state 1
        uint32_t state = this->field_0x0004;
        if (state != 1) {
            this->field_0x0004 = 1;
        }
    } else {
        // Positive time - transition to state 0
        uint32_t state = this->field_0x0004;
        if (state != 0) {
            this->field_0x0004 = 0;
        }
    }
    
    // Check if we should use capsule collision
    uint8_t useCapsule = animSubData->m_bUseCapsule;
    uint8_t capsuleEnabled = animSubData->m_bCapsuleEnabled;

    if (useCapsule != 0 && capsuleEnabled != 0) {
        // Copy capsule data and calculate collision
        float capsuleData[4];
        float* srcCapsule = animSubData->m_capsuleStart;
        float* dstCapsule = (float*)((char*)outputState + 48);
        
        // Copy 16 bytes (4 floats)
        for (int i = 0; i < 4; i++) {
            dstCapsule[i] = srcCapsule[i];
        }
        
        // Calculate capsule collision parameters
        float* capsuleEnd = &animSubData->m_minTime;
        float capsuleDiff[4];
        for (int i = 0; i < 4; i++) {
            capsuleDiff[i] = capsuleEnd[i] - dstCapsule[i];
        }
        
        // Call capsule collision function
        phBoundCapsule_ApplyCollision(outputState, capsuleDiff, (void*)0x825C9B60);
        
    } else {
        // Use simple animation data
        void* simpleAnimData = animSubData->m_simpleAnimData;
        rage::mat33FromEuler(static_cast<float*>(outputState),
                             static_cast<const float*>(simpleAnimData));
    }
    
    // Copy final capsule data to output
    float* finalCapsule = animSubData->m_capsuleStart;
    float* outputCapsule = (float*)((char*)outputState + 48);
    for (int i = 0; i < 4; i++) {
        outputCapsule[i] = finalCapsule[i];
    }
    
    // Clear timing fields
    *(float*)&this->field_0x0008 = zero;
    this->field_0x0014 = 0;
}

// ═════════════════════════════════════════════════════════════════════════════
// pcrSwingData / pcrJunkSwingData — Swing Animation Data
// ═════════════════════════════════════════════════════════════════════════════

// External vtable pointers
extern void* g_pcrSwingDataVtable;      // @ 0x8202E9AC
extern void* g_pcrJunkSwingDataVtable;  // @ 0x8202EAF4

/**
 * pcrSwingData_ctor_B888 @ 0x820EB888 | size: 0x60
 *
 * Constructor for pcrJunkSwingData (derived from pcrSwingData).
 * Initializes swing animation data with optional frame adjustment.
 *
 * The constructor:
 * 1. Sets base class vtable (pcrSwingData)
 * 2. Zeros out state fields (+4, +8, +12)
 * 3. If frame pointer (+16) is set, adjusts it based on segment data
 * 4. Sets derived class vtable (pcrJunkSwingData)
 *
 * Structure layout (inferred):
 *   +0   vtable pointer
 *   +4   state field 1 (zeroed)
 *   +8   state field 2 (zeroed)
 *   +12  state field 3 (zeroed)
 *   +16  frame pointer (adjusted if non-null)
 *
 * @param this - Pointer to pcrJunkSwingData object being constructed
 * @param segmentData - Pointer to segment/array data structure for frame calculation
 */
void pcrSwingData_ctor_B888(void* thisPtr, void* segmentData) {
    uint8_t* obj = (uint8_t*)thisPtr;
    uint8_t* segments = (uint8_t*)segmentData;
    
    // Set base class vtable (pcrSwingData)
    *(void**)(obj + 0) = (void*)0x8202E9AC;  // g_pcrSwingDataVtable
    
    // Zero out state fields
    *(uint32_t*)(obj + 4) = 0;
    *(uint32_t*)(obj + 8) = 0;
    *(uint32_t*)(obj + 12) = 0;
    
    // Check if frame pointer is set
    uint32_t framePtr = *(uint32_t*)(obj + 16);
    
    if (framePtr != 0) {
        // Load segment metadata
        uint32_t segmentStart = *(uint32_t*)(segments + 4);
        uint32_t segmentStride = *(uint32_t*)(segments + 76);
        
        // Calculate frame offset from segment start
        uint32_t frameOffset = framePtr - segmentStart;
        
        // Compute segment index (frameOffset / segmentStride)
        // Note: Division by zero trap is present in original code
        uint32_t segmentIndex = frameOffset / segmentStride;
        
        // Compute array index: segmentIndex + 2
        uint32_t arrayIndex = segmentIndex + 2;
        
        // Load segment base offset from array
        uint32_t segmentBaseOffset = *(uint32_t*)(segments + (arrayIndex * 4));
        
        // Adjust frame pointer by adding segment base
        uint32_t adjustedFramePtr = segmentBaseOffset + framePtr;
        
        // Store adjusted frame pointer
        *(uint32_t*)(obj + 16) = adjustedFramePtr;
    }
    
    // Set derived class vtable (pcrJunkSwingData)
    *(void**)(obj + 0) = (void*)0x8202EAF4;  // g_pcrJunkSwingDataVtable
}


// ─────────────────────────────────────────────────────────────────────────────
// pongCreatureInst — Small vtable methods and utility functions
// ─────────────────────────────────────────────────────────────────────────────
//
// Slots 2, 3, 9-11, 14, 22, 30, 31 and 37 sit with the fragInst methods further
// down, where pongCreatureInstLayout is defined.

/**
 * pongCreatureInst::GetType @ 0x8210CC40 | size: 0x8  [vtable slot 1]
 *
 * Returns the creature instance type identifier. Value 3 indicates
 * a pongCreatureInst (as opposed to other phInst subtypes).
 */
int pongCreatureInst::GetType() {  // vfn_1
    return 3;
}

/**
 * pongCreatureInst::GetDefaultIndex @ 0x824FF7C8 | size: 0x8  [vtable slot 19]
 *
 * Returns -1, indicating no default creature index. Used as a sentinel
 * value when no specific creature slot is assigned.
 */
int pongCreatureInst::GetDefaultIndex() {  // vfn_19
    return -1;
}

/**
 * pongCreatureInst::ClearBoundingVector @ 0x822C90F8 | size: 0x10  [vtable slot 4]
 *
 * Zeroes a 16-byte aligned vector passed by pointer. Used to clear
 * bounding volume data (AABB min/max or collision sphere).
 */
void pongCreatureInst::ClearBoundingVector(void* outVector) {  // vfn_4
    // Original uses vxor + stvx (AltiVec zero + aligned store)
    memset(outVector, 0, 16);
}

/**
 * pongCreatureInst::GetEntityByIndex @ 0x822C9318 | size: 0x18  [vtable slot 38]
 *
 * Looks up a sub-entity by index. Follows: this->field_4 -> field_12 -> field_120,
 * then adds (index << 6) to get the entity pointer. Each entity is 64 bytes.
 */
void* pongCreatureInst::GetEntityByIndex(int index) {  // vfn_38
    void* inner = (void*)this->field_0x0004;
    void* pool = *(void**)((char*)inner + 12);
    char* base = *(char**)((char*)pool + 120);
    return base + (index << 6);
}


// ─────────────────────────────────────────────────────────────────────────────
// pongCreatureInst — Batch 2: thunks, flag checks, delegation helpers
// ─────────────────────────────────────────────────────────────────────────────

/**
 * pongCreatureInst::HasVisibilityFlag @ 0x820C5378 | size: 0x20
 *
 * Tests bit 2 of the flags byte at +431 (0x1AF). Returns true if the
 * creature has the visibility/render flag set.
 */
bool pongCreatureInst::HasVisibilityFlag() {  // 5378
    return (this->field_0x01af & 0x4) != 0;
}

/**
 * pongCreatureInst::IsNetworkActive @ 0x8211C9C8 | size: 0x20
 *
 * Returns true if the global network state pointer at 0x8271A36C is
 * non-null, indicating an active network session.
 */
bool pongCreatureInst::IsNetworkActive() {  // C9C8_w
    extern void* g_networkStatePtr;  // @ 0x8271A36C
    return g_networkStatePtr != nullptr;
}

/**
 * pongCreatureInst::IsIndexValid @ 0x8211CF90 | size: 0x20
 *
 * Compares field_12 (current index) against field_16 (max index).
 * Returns true if current >= max (i.e., index has reached capacity).
 */
bool pongCreatureInst::IsIndexValid() {  // CF90_h
    int32_t currentIdx = (int32_t)this->field_0x000c;
    int32_t maxIdx = (int32_t)this->field_0x0010;
    return currentIdx >= maxIdx;
}

/**
 * pongCreatureInst::GetCurrentWeight @ 0x8211D010 | size: 0x38
 *
 * Returns the current animation weight for the active blend entry.
 * If field_0 (pointer array) is non-null, uses indexed lookup:
 *   array[index] -> field at +124
 * Otherwise falls back to linear array at field_4:
 *   field_4 + (index * 176) + 96
 */
float pongCreatureInst::GetCurrentWeight() {  // D010_h
    void* ptrArray = (void*)this->vtable;
    int32_t index = (int32_t)this->field_0x000c;

    if (ptrArray) {
        // Indexed pointer array lookup
        void** entries = (void**)ptrArray;
        void* entry = entries[index];
        return *(float*)((char*)entry + 124);
    } else {
        // Linear array fallback (stride = 176 bytes per entry)
        char* base = (char*)this->field_0x0004;
        return *(float*)(base + index * 176 + 96);
    }
}

/**
 * pongCreatureInst::DelegateSlot9_Offset32 @ 0x82118FC0 | size: 0x1C
 *
 * Extracts the target object from arg->field_4, then tail-calls its
 * vtable slot 9 with this+32 as the data argument.
 */
void pongCreatureInst::DelegateSlot9_Offset32(void* arg) {  // 8FC0_p42
    void* target = ((xmlCallbackNode*)arg)->dataObj;
    VCALL(target, 9, void(*)(void*, void*))(target, &this->field_0x0020);
}

/**
 * pongCreatureInst::DelegateSlot9_Offset48 @ 0x82118FE0 | size: 0x1C
 *
 * Same pattern as DelegateSlot9_Offset32, with this+48.
 */
void pongCreatureInst::DelegateSlot9_Offset48(void* arg) {  // 8FE0_p42
    void* target = ((xmlCallbackNode*)arg)->dataObj;
    VCALL(target, 9, void(*)(void*, void*))(target, &this->field_0x0030);
}

/**
 * pongCreatureInst::DelegateSlot9_Offset64 @ 0x82119000 | size: 0x1C
 *
 * Same pattern as DelegateSlot9_Offset32, with this+64.
 */
void pongCreatureInst::DelegateSlot9_Offset64(void* arg) {  // 9000_p42
    void* target = ((xmlCallbackNode*)arg)->dataObj;
    VCALL(target, 9, void(*)(void*, void*))(target, &this->field_0x0040);
}

/**
 * pongCreatureInst::DelegateSlot9_Offset80 @ 0x82119020 | size: 0x1C
 *
 * Same pattern, with this+80.
 */
void pongCreatureInst::DelegateSlot9_Offset80(void* arg) {  // 9020_p42
    void* target = ((xmlCallbackNode*)arg)->dataObj;
    VCALL(target, 9, void(*)(void*, void*))(target, &this->field_0x0050);
}

/**
 * pongCreatureInst::DelegateSlot9_Offset112 @ 0x82119040 | size: 0x1C
 *
 * Same pattern, with this+112.
 */
void pongCreatureInst::DelegateSlot9_Offset112(void* arg) {  // 9040_p42
    void* target = ((xmlCallbackNode*)arg)->dataObj;
    VCALL(target, 9, void(*)(void*, void*))(target, &this->field_0x0070);
}

/**
 * pongCreatureInst::DelegateSlot9_Offset128 @ 0x82119060 | size: 0x1C
 *
 * Same pattern, with this+128.
 */
void pongCreatureInst::DelegateSlot9_Offset128(void* arg) {  // 9060_p42
    void* target = ((xmlCallbackNode*)arg)->dataObj;
    VCALL(target, 9, void(*)(void*, void*))(target, &this->field_0x0080);
}

/**
 * pongCreatureInst::DelegateSlot9_Offset144 @ 0x82119080 | size: 0x1C
 *
 * Same pattern, with this+144.
 */
void pongCreatureInst::DelegateSlot9_Offset144(void* arg) {  // 9080_p42
    void* target = ((xmlCallbackNode*)arg)->dataObj;
    VCALL(target, 9, void(*)(void*, void*))(target, &this->field_0x0090);
}

/**
 * pongCreatureInst::StoreVCallResultAtField429 @ 0x82118E70 | size: 0x40
 *
 * Extracts object from arg->field_4, calls its vtable slot 4,
 * and stores the byte result at this+429. Used for syncing
 * animation state flags from a network message.
 */
void pongCreatureInst::StoreVCallResultAtField429(void* arg) {  // 8E70_p42
    void* target = ((xmlCallbackNode*)arg)->dataObj;
    uint8_t result = VCALL(target, 4, uint8_t(*)(void*))(target);
    this->field_0x01ad = result;  // m_boneParam
}

/**
 * pongCreatureInst::StoreVCallResultAtField446 @ 0x82119180 | size: 0x40
 *
 * Same pattern as StoreVCallResultAtField429, stores at this+446.
 */
void pongCreatureInst::StoreVCallResultAtField446(void* arg) {  // 9180_p42
    void* target = ((xmlCallbackNode*)arg)->dataObj;
    uint8_t result = VCALL(target, 4, uint8_t(*)(void*))(target);
    this->field_0x01be = result;  // m_blendFlag
}

// ─────────────────────────────────────────────────────────────────────────────
// LocomotionStateAnim — Small helpers
// ─────────────────────────────────────────────────────────────────────────────

/**
 * LocomotionStateAnim_BB98 @ 0x8224BB98 | size: 0x10
 *
 * Tail-calls the channel's slot-7 blend operation, forwarding source,
 * weight and both integer arguments unchanged.
 */
void LocomotionStateAnim_BB98(void* entry, void* source, float weight,
                             uint32_t unusedR5, uint32_t flags) {  // BB98
    VCALL(entry, 7, void(*)(void*, void*, float, uint32_t, uint32_t))(
        entry, source, weight, unusedR5, flags);
}

/**
 * LocomotionStateAnim::CountActiveAnimLayers @ 0x820DBA60 | size: 0x3C
 *
 * Counts the number of active animation layers (at offsets +16, +20, +24).
 * Each non-null pointer counts as one active layer. Returns count + 1
 * (base layer is always counted) if field_24 is non-null, otherwise
 * returns just the count of the first two layers.
 */
int LocomotionStateAnim::CountActiveAnimLayers() {  // BA60_g
    int count = 0;
    if (this->field_0x0010 != 0) count++;
    if (this->field_0x0014 != 0) count++;
    if (this->field_0x0018 != 0) return count + 1;
    return count;
}


// ─────────────────────────────────────────────────────────────────────────────
// pongCreatureInst / LocomotionState — Batch 3 (39 remaining small functions)
// ─────────────────────────────────────────────────────────────────────────────

// ── VTABLE THUNKS ──────────────────────────────────────────────────────────

/**
 * pongCreatureInst vtable thunks @ 0x8211CC48-CC78 | 16B each
 *
 * Four adjacent vtable forwarding thunks. Each loads the vtable from
 * this, then tail-calls a specific slot. Used by the creature instance
 * to forward calls to its inner physics/collision object.
 */
void pongCreatureInst::ForwardVfn11() {  // CC48_p42 @ 0x8211CC48
    VCALL(this, 11, void(*)(void*))(this);
}

void pongCreatureInst::ForwardVfn12() {  // CC58_p42 @ 0x8211CC58
    VCALL(this, 12, void(*)(void*))(this);
}

void pongCreatureInst::ForwardVfn13() {  // CC68_p42 @ 0x8211CC68
    VCALL(this, 13, void(*)(void*))(this);
}

void pongCreatureInst::ForwardVfn14() {  // CC78_p33 @ 0x8211CC78
    VCALL(this, 14, void(*)(void*))(this);
}

// ── FIELD SETTERS (vcall result → store) ───────────────────────────────────

/**
 * pongCreatureInst::UpdateFlag445 @ 0x82118EB0 | size: 0x50
 *
 * Calls vtable slot 4 on the object at arg->field_4 to get a bool,
 * stores it at this+445. Used for syncing creature visibility flags.
 */
void pongCreatureInst::UpdateFlag445(void* arg) {  // 8EB0_p42
    void* target = ((xmlCallbackNode*)arg)->dataObj;
    uint8_t val = VCALL(target, 4, uint8_t(*)(void*))(target);
    this->field_0x01bd = val;  // m_boneFlag
}

/**
 * pongCreatureInst::UpdateFlag447 @ 0x82118F70 | size: 0x50
 *
 * Same pattern as UpdateFlag445, stores at this+447.
 */
void pongCreatureInst::UpdateFlag447(void* arg) {  // 8F70_p42
    void* target = ((xmlCallbackNode*)arg)->dataObj;
    uint8_t val = VCALL(target, 4, uint8_t(*)(void*))(target);
    this->field_0x01bf = val;  // m_mirrorFlag
}

/**
 * pongCreatureInst::UpdateFlagBit3 @ 0x82118F00 | size: 0x70
 *
 * Calls vtable slot 4 on arg->field_4 to get a bool. If true,
 * sets bit 3 (0x08) of the flags byte at this+431. If false, clears it.
 */
void pongCreatureInst::UpdateFlagBit3(void* arg) {  // 8F00_p42
    void* target = ((xmlCallbackNode*)arg)->dataObj;
    uint8_t val = VCALL(target, 4, uint8_t(*)(void*))(target);

    if (val) {
        this->field_0x01af |= 0x08;   // set bit 3
    } else {
        this->field_0x01af &= ~0x08;  // clear bit 3
    }
}

// ── COMPUTATION: Lookups & Searches ────────────────────────────────────────

/**
 * pongCreature::LookupHashValue @ 0x820C79F0 | size: 0x34
 *
 * Looks up a value in the creature's hash table at this+160.
 * Key from *keyPtr is shifted left 3 (×8 byte entries). The hash table
 * stores values at entry+4. Writes result to *outPtr, or 0 if not found.
 */
void pongCreature::LookupHashValue(void* outPtr, void* keyPtr) {  // 79F0_p45
    uint32_t key = *(uint32_t*)keyPtr;
    void* hashTable = (void*)this->field_0x00a0;  // m_hashTable
    char* entries = *(char**)((char*)hashTable + 8);
    char* entry = entries + (key << 3);

    if (entry) {
        *(uint32_t*)outPtr = *(uint32_t*)(entry + 4);
    } else {
        *(uint32_t*)outPtr = 0;
    }
}

/**
 * pongCreature::FindIndexByKey @ 0x820C7990 | size: 0x60
 *
 * Linear scan of an array looking for a matching key. Returns the
 * index into *outPtr, or -1 if not found. Array entries have stride 8
 * with key at entry+0.
 */
void pongCreature::FindIndexByKey(void* outPtr, void* keyPtr) {  // 7990_p45
    uint32_t searchKey = *(uint32_t*)keyPtr;
    void* arrayBase = (void*)this->field_0x00a0;  // m_hashTable
    char* entries = *(char**)((char*)arrayBase + 8);
    uint32_t count = *(uint32_t*)((char*)arrayBase + 12);

    for (uint32_t i = 0; i < count; i++) {
        uint32_t entryKey = *(uint32_t*)(entries + i * 8);
        if (entryKey == searchKey) {
            *(int32_t*)outPtr = (int32_t)i;
            return;
        }
    }
    *(int32_t*)outPtr = -1;
}

/**
 * pongCreatureInst::LookupContainer @ 0x8211CFB0 | size: 0x60
 *
 * Dual-path lookup: if field_0 (pointer array) is non-null, uses
 * indexed access: array[index]->field_4. Otherwise uses linear
 * stride: field_4 + (index * 176) + 4. Returns the uint32_t value.
 */
uint32_t pongCreatureInst::LookupContainer() {  // CFB0_h
    void* ptrArray = (void*)this->vtable;
    int32_t index = (int32_t)this->field_0x000c;

    if (ptrArray) {
        void** entries = (void**)ptrArray;
        void* entry = entries[index];
        return *(uint32_t*)((char*)entry + 4);
    } else {
        char* base = (char*)this->field_0x0004;
        return *(uint32_t*)(base + index * 176 + 4);
    }
}

/**
 * pongCreatureInst::HasMultipleActiveSlots @ 0x82127BD8 | size: 0x6C
 *
 * Iterates the bitfield at this+464 (32 bits), counting set bits.
 * Returns true if more than 1 bit is set — indicating multiple
 * active animation or physics slots.
 */
bool pongCreatureInst::HasMultipleActiveSlots() {  // 7BD8_h
    uint32_t bitfield = this->field_0x01d0;  // m_activeSlotBits
    int count = 0;
    while (bitfield) {
        count += (bitfield & 1);
        bitfield >>= 1;
        if (count > 1) return true;
    }
    return false;
}

// ── COMPUTATION: List/Array Operations ─────────────────────────────────────

/**
 * pongCreatureInst::ListInsertTail @ 0x821267E8 | size: 0x6C
 *
 * Inserts a node at the tail of a doubly-linked list. Updates prev/next
 * pointers and increments the element count at this+8.
 */
void pongCreatureInst::ListInsertTail(void* node) {  // 67E8_h
    char* listHead = (char*)this;
    void* tail = *(void**)(listHead + 4);  // current tail

    // Link new node
    *(void**)((char*)node + 0) = tail;       // node->prev = tail
    *(void**)((char*)node + 4) = nullptr;    // node->next = null

    if (tail) {
        *(void**)((char*)tail + 4) = node;   // tail->next = node
    } else {
        *(void**)(listHead + 0) = node;      // head = node (empty list)
    }
    *(void**)(listHead + 4) = node;          // tail = node

    // Increment count
    int32_t* count = (int32_t*)(listHead + 8);
    (*count)++;
}

/**
 * pongCreatureInst::ArrayRemove @ 0x822C9420 | size: 0x74
 *
 * Finds and removes an element from a pointer array by value.
 * Uses shift-left compaction to fill the gap. Decrements count at +8.
 */
void pongCreatureInst::ArrayRemove(void* element) {  // 9420_h
    void** array = (void**)this->vtable;
    int32_t count = (int32_t)this->field_0x0008;

    for (int i = 0; i < count; i++) {
        if (array[i] == element) {
            // Shift remaining elements left
            for (int j = i; j < count - 1; j++) {
                array[j] = array[j + 1];
            }
            array[count - 1] = nullptr;
            this->field_0x0008 = count - 1;
            return;
        }
    }
}

/**
 * pongCreatureInst::SetRefPtr @ 0x822C9030 | size: 0x70
 *
 * Atomically swaps a ref-counted pointer at this+4. Adds a reference
 * to the new object and releases the old one.
 */
void pongCreatureInst::SetRefPtr(void* newObj) {  // 9030_g
    void* oldObj = (void*)this->field_0x0004;
    if (newObj) rage_AddRef(newObj);
    this->field_0x0004 = (uint32_t)(uintptr_t)newObj;
    if (oldObj) rage_Release(oldObj);
}

/**
 * pongCreatureInst::SetArraySlot @ 0x8228E7B8 | size: 0x64
 *
 * Sets a ref-counted pointer in an array slot. Adds ref to new value,
 * releases old value at the specified index.
 */
void pongCreatureInst::SetArraySlot(int index, void* newObj) {  // E7B8_h
    void** array = (void**)this->vtable;
    void* oldObj = array[index];

    if (newObj) rage_AddRef(newObj);
    array[index] = newObj;
    if (oldObj) rage_Release(oldObj);
}

// ── COMPUTATION: Detach/Destroy ────────────────────────────────────────────

/**
 * pongCreature::ScalarDeletingDtor @ 0x820C5398 | size: 0x50
 *
 * Standard MSVC scalar deleting destructor. Calls the base destructor,
 * then conditionally frees memory if bit 0 of the flags parameter is set.
 */
void pongCreature::ScalarDeletingDtor(int flags) {  // vfn_0_5398_1

    pongCreature_BaseDtor(this);
    if (flags & 1) {
        rage_free(this);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// pongCreatureInst — rage::phInst / rage::fragInst slots, fragment cache
// ─────────────────────────────────────────────────────────────────────────────
//
// pongCreatureInst derives from rage::fragInst (vtable 0x82032D2C), which
// derives from rage::phInst: fragInst's destructor body (0x8211D470,
// FragInstDtor below) restores the fragInst vtable and then runs phInst's
// (0x822C8FD0). Slots 9, 10, 14, 31 and 37 are phInst's code, 11 and 22
// fragInst's; 2, 3 and 30 are pongCreatureInst's own overrides.
// The slots below work on phInst/fragInst members. The flat field_0x.. list in
// pong_creature.hpp also holds rage::fragType members (the XML tuning readers
// at 0x82118E70..0x82119180 and fragType's constructor at 0x8211BB30 write
// +0x20..+0x1BF), so these methods read the object through
// pongCreatureInstLayout, which only holds members these functions and
// fragInst's resource constructor (0x8211D3B8) prove.

struct fragType;  // rage::fragType (vtable 0x82032CA4), opaque here

namespace rage {
struct phInstBehavior;  // vtable 0x82065080
struct phRope;          // vtable 0x820650B0, derives from phInstBehavior
}

// Chained hash map from a 32-bit key to a 16-bit use count. The fragment
// cache pool keeps one (pool+0x1C) counting the cached instances per fragInst
// cache key: ph_A808 (0x8212A808) inserts the key or bumps its count when it
// sets up an entry.
struct CacheKeyCount {
    uint32_t key;    // +0x00
    uint16_t count;  // +0x04
    uint16_t _pad06;
};

struct CacheKeyNode {
    CacheKeyCount entry;  // +0x00
    CacheKeyNode* next;   // +0x08  next node in the same bucket
};

struct CacheKeyMap {
    uint32_t       bucketCount;  // +0x00  power of two
    uint32_t       nodeCount;    // +0x04
    CacheKeyNode** buckets;      // +0x08
    CacheKeyNode*  freeNodes;    // +0x0C  ph_A808 takes new nodes from here

    CacheKeyNode* Find(const CacheKeyCount& probe) const;
};

// Pool of fragment cache entries at g_creatureManager+0x2F0. Acquire
// (0x821263B8) takes a free entry while used < capacity, otherwise it steals
// one whose instance's world bound sphere (inst+0x70 / +0x80) lies outside
// the six view planes at g_creatureManager+0x1D0.
// Acquire stamps every entry it hands out with currentStamp, and steals only
// entries stamped before currentStamp - 1.
struct fragCachePool {
    uint8_t      _pad00[0x08];  // capacity +0x00, used +0x04
    uint32_t     currentStamp;  // +0x08
    uint8_t      _pad0C[0x10];  // free list +0x0C
    CacheKeyMap* keyCounts;     // +0x1C
};

struct pongCreatureSkeleton;  // defined with the pongCreature lifts below

// Entry of that pool, reduced to what these methods read.
struct fragCacheEntry {
    uint8_t               _pad000[0x0C];
    uint32_t              lastUsedStamp;  // +0x0C  fragCachePool::currentStamp when last used
    uint8_t               _pad010[0x1D4];
    pongCreatureSkeleton* skeleton;       // +0x1E4  pongCreature::SyncFragmentPose copies its pose here
    uint8_t               _pad1E8[0x18];
    rage::phInstBehavior* behavior;       // +0x200  ApplyToRope casts it to phRope
};

// Callback object (rage::Functor1 layout, assumed): the caller loads the
// thunk from +0x0C and passes the callback itself plus one argument.
struct fragInstCallback {
    uint8_t _pad00[0x0C];  // callee + member-function pointer
    void  (*thunk)(const fragInstCallback* self, void* managerHandle);  // +0x0C
};

// The object behind g_creatureManager (0x826063B8), reduced to what these
// methods touch. Its fragInst callbacks sit 0x10 apart from +0x32C: attach,
// detach (DetachFromScene), bound moved, create (fragInst's resource
// constructor passes the instance and keeps the result at inst+0xC0) and
// destroy (fragInst's destructor passes that result back).
struct fragInstManager {
    uint8_t          _pad000[0x2F0];
    fragCachePool*   cachePool;     // +0x2F0
    uint8_t          _pad2F4[0x38];
    fragInstCallback onAttach;      // +0x32C
    fragInstCallback onDetach;      // +0x33C
    fragInstCallback onBoundMoved;  // +0x34C
    fragInstCallback onCreate;      // +0x35C  thunk returns the handle (not called here)
    fragInstCallback onDestroy;     // +0x36C
};

// The parts of rage::phArchetype / rage::phBound read below. phBound's
// SetCentroidOffset (0x8228D178) stores the vector at +0x30; +0x08 is the
// radius of the bounding sphere around that centroid.
struct phBoundView {
    void**   vtable;                // +0x00
    uint8_t  _pad04[0x04];
    float    radiusAroundCentroid;  // +0x08
    uint8_t  _pad0C[0x24];
    float    centroidOffset[4];     // +0x30  w unused
    uint8_t  _pad40[0x30];
    void**   parts;                 // +0x70  part pointers, null for an empty slot
    uint8_t  _pad74[0x04];
    void*    partMatrices;          // +0x78  64-byte part matrices (GetEntityByIndex)
    uint8_t  _pad7C[0x06];
    uint16_t partCount;             // +0x82

    // Slots 2 and 3, called by pongCreature::SyncFragmentPose: slot 3 gets the
    // instance's world matrix, but only when slot 2 says yes.
    bool vfn_2() { return reinterpret_cast<bool (*)(phBoundView*)>(vtable[2])(this); }
    void vfn_3(const void* worldMatrix) {
        reinterpret_cast<void (*)(phBoundView*, const void*)>(vtable[3])(this, worldMatrix);
    }
};

struct phArchetypeView {
    uint8_t      _pad00[0x0C];
    phBoundView* bound;  // +0x0C
};

struct pongCreatureInstLayout;

// Object at fragInst+0x94: supplies the instance's fragType when set, and
// lists the attached instances that point at it (linked through +0x58/+0x5C).
struct fragTypeHolder {
    uint8_t                 _pad00[0x18];
    fragType*               type;            // +0x18
    uint8_t                 _pad1C[0x20];
    pongCreatureInstLayout* instancesHead;   // +0x3C
    pongCreatureInstLayout* instancesTail;   // +0x40
    uint32_t                instanceCount;   // +0x44
};

static const uint32_t FRAG_INST_FLAG_ATTACHED = 0x1;  // set by AttachToScene, cleared by DetachFromScene

// pongCreatureInst as laid out in the binary (rage::phInst, then rage::fragInst,
// then pongCreatureInst's own members), reduced to what these methods use.
struct pongCreatureInstLayout {
    void**                  vtable;            // +0x00
    phArchetypeView*        archetype;         // +0x04  rage::phInst; released by ~phInst (0x822C8FD0)
    uint16_t                levelIndex;        // +0x08  slot in the physics level
    uint8_t                 _pad0A[0x06];
    float                   matrix[4][4];      // +0x10  world matrix, translation in row 3 (+0x40)
    uint32_t                flags;             // +0x50  FRAG_INST_FLAG_*
    fragCacheEntry*         cacheEntry;        // +0x54  set when ph_A700 (0x8212A700) binds an entry
    pongCreatureInstLayout* prevInHolder;      // +0x58
    pongCreatureInstLayout* nextInHolder;      // +0x5C
    uint8_t                 _pad60[0x10];
    float                   worldBoundCenter[4];  // +0x70  w lane is not meaningful
    float                   worldBoundRadius;  // +0x80
    uint8_t                 _pad84[0x0C];
    fragType*               type;              // +0x90  used when typeHolder is null
    fragTypeHolder*         typeHolder;        // +0x94
    uint32_t                cacheKey;          // +0x98  counted in fragCachePool::keyCounts, 0 = none
    uint8_t                 _pad9C[0x24];
    void*                   managerHandle;     // +0xC0  returned by the manager's create callback
    uint8_t                 _padC4[0x1C];
    float                   lastMatrix[4][4];  // +0xE0  pongCreatureInst's; Get/SetLastMatrix
    uint8_t                 flag120;           // +0x120  pongCreature::StepLocomotion does nothing while clear
    uint8_t                 _pad121[0x03];
    void*                   bounds;            // +0x124  atArray of 0x100-byte phBound objects
    uint16_t                boundCount;        // +0x128
    uint16_t                boundCapacity;     // +0x12A

    // Inlined wherever fragInst needs its type (also ph_A700, ph_A808, 0x8211FA00)
    fragType* ResolvedType() const { return typeHolder ? typeHolder->type : type; }
};

extern void* g_creatureManager;  // @ 0x826063B8 — see fragInstManager

// @ 0x821263B8 (pongCreatureInst_63B8) — takes an entry from the pool, or null
extern fragCacheEntry* fragCachePool_Acquire(fragCachePool* pool);
// @ 0x8212A700 (ph_A700) — binds the entry to the instance (entry+0x1B4 = inst,
// inst+0x54 = entry). With a type, the last three go to ph_A808, which sets
// bit `index` of the entry's bitset at +0x1CC when markIndex is set; without
// one, arg5 and index are only stored at entry+0x1B8 / +0x1BC. index comes
// in r8 (stored with sth) and arg5 in r9.
extern void fragCacheEntry_Init(fragCacheEntry* entry, fragTypeHolder* typeHolder, fragType* type,
                                const float* matrix, pongCreatureInst* inst, uint16_t index,
                                void* arg5, bool markIndex);
// @ 0x82120120 (fragInst_vfn_30), not lifted. Returns null unless flag 0x2 at
// +0x50 is set, and the instance at once unless bit 0 of its fragType's byte
// +0x1AF is set. Otherwise gets a cache entry through slot 43 if there is none
// (null if that fails), hands the pointer at entry+0x1EC out through outObject,
// sets flag 0x2 again and returns the instance (one more check can return
// null). It also restamps the cache entry of a fragInst found through arg2..arg4.
extern void* fragInst_PrepareForActivation(pongCreatureInst* inst, void** outObject,
                                           void* arg2, void* arg3, void* arg4);
// @ 0x823458F0 (pongCreatureInst_58F0_wrh). Splits vec between the two
// particles at the ends of the rope's segment `segment` (segments at rope+0x08,
// 0x60 bytes each, particle indices at +0x34/+0x38; particles at rope+0x0C,
// 0x170 bytes each), each particle's share being the other one's distance from
// point over the sum of both distances, and adds the shares to the particles'
// +0xC0 vectors.
extern void phRope_ApplyAtSegment(rage::phRope* rope, const float* vec, const float* point, int segment);

// MSVC RTTI type descriptors (.data, decorated name at +8)
struct RTTITypeDescriptor;
extern RTTITypeDescriptor g_typeDescriptor_phInstBehavior;  // @ 0x825D4520  ".?AVphInstBehavior@rage@@"
extern RTTITypeDescriptor g_typeDescriptor_phRope;          // @ 0x825D4544  ".?AVphRope@rage@@"
// @ 0x82430978: MSVC's __RTDynamicCast
extern "C" void* RTDynamicCast(void* object, int32_t vfDelta, RTTITypeDescriptor* sourceType,
                               RTTITypeDescriptor* targetType, int32_t isReference);

// dynamic_cast<rage::phRope*>(behavior), the call the compiler emitted
static rage::phRope* AsRope(rage::phInstBehavior* behavior) {
    return static_cast<rage::phRope*>(
        RTDynamicCast(behavior, 0, &g_typeDescriptor_phInstBehavior, &g_typeDescriptor_phRope, 0));
}

// .data vector at 0x82606750; probably zero (0x823458F0 falls back to it for a
// zero length), but the bytes aren't in the repo
extern "C" const float lbl_82606750[4];

static const uintptr_t FRAG_INST_VTABLE = 0x82032D2C;  // rage::fragInst

static fragInstManager* FragInstManager() {
    return static_cast<fragInstManager*>(g_creatureManager);
}

static pongCreatureInstLayout* Layout(pongCreatureInst* inst) {
    return reinterpret_cast<pongCreatureInstLayout*>(inst);
}

// Bob Jenkins' 32-bit integer hash, inlined at both users of the key map
static uint32_t HashCacheKey(uint32_t key) {
    uint32_t hash = key;
    hash += hash << 12;
    hash ^= hash >> 22;
    hash += hash << 4;
    hash ^= hash >> 9;
    hash += hash << 10;
    hash ^= hash >> 2;
    hash += hash << 7;
    hash ^= hash >> 12;
    return hash;
}

/**
 * CacheKeyMap::Find @ 0x82121660 | size: 0xB0  (was pongCreatureInst_1660_w)
 *
 * Returns the node holding probe.key, or null. Only the key is compared; the
 * count in the probe is ignored. A hash of 0 is bumped to 1 before masking.
 */
CacheKeyNode* CacheKeyMap::Find(const CacheKeyCount& probe) const {
    uint32_t hash = HashCacheKey(probe.key);
    if (hash == 0)
        hash = 1;

    for (CacheKeyNode* node = buckets[hash & (bucketCount - 1)]; node != nullptr; node = node->next) {
        if (node->entry.key == probe.key)
            return node;
    }
    return nullptr;
}

/**
 * pongCreatureInst::ScalarDeletingDtor @ 0x820C8EE0 | size: 0x9C  [vtable slot 0]
 *
 * Destroys the embedded bound array, runs fragInst's destructor and frees
 * the object when bit 0 of flags is set. Returns this, like every MSVC
 * deleting destructor.
 */
void* pongCreatureInst::ScalarDeletingDtor(int flags) {
    pongCreatureInstLayout* self = Layout(this);

    // atArray destructor: delete[] the bounds when the array owns its storage.
    // MSVC keeps a 16-byte cookie starting with the element count in front of
    // the array; with elements left, the first one's vector deleting destructor
    // (flags 3) destroys them all and frees the block.
    if (self->boundCapacity != 0 && self->bounds != nullptr) {
        int32_t* cookie = (int32_t*)((char*)self->bounds - 16);
        if (*cookie != 0)
            VCALL(self->bounds, 0, void(*)(void*, int))(self->bounds, 3);
        else
            rage_free(cookie);
    }

    FragInstDtor();  // ~fragInst

    if (flags & 1)
        rage_free(this);
    return this;
}

/**
 * pongCreatureInst::FragInstDtor @ 0x8211D470 | size: 0x58  (was Detach)
 *
 * rage::fragInst's destructor body: restores the fragInst vtable, hands the
 * manager's destroy callback (+0x36C) the handle its create callback returned
 * for this instance, then runs ~phInst (0x822C8FD0).
 */
void pongCreatureInst::FragInstDtor() {
    pongCreatureInstLayout* self    = Layout(this);
    fragInstManager*        manager = FragInstManager();

    self->vtable = reinterpret_cast<void**>(FRAG_INST_VTABLE);
    manager->onDestroy.thunk(&manager->onDestroy, self->managerHandle);

    pongCreatureInst_Cleanup(this);  // ~phInst
}

/**
 * pongCreatureInst::AttachToScene @ 0x8211D0E0 | size: 0x13C  [vtable slot 41]
 *
 * Marks the instance attached and tells the manager (callback +0x32C). With
 * rejectIfKeyCached it first refuses (returns false) when the instance's
 * cache key is already counted in the fragment cache pool, i.e. another
 * cached instance uses it. An instance with a type gets vtable slot 48; one
 * with a type holder is pushed onto the front of the holder's instance list.
 */
bool pongCreatureInst::AttachToScene(bool rejectIfKeyCached) {
    fragInstManager*        manager = FragInstManager();
    pongCreatureInstLayout* self    = Layout(this);

    if (rejectIfKeyCached && self->cacheKey != 0) {
        CacheKeyCount probe;
        probe.key   = self->cacheKey;
        probe.count = 0;  // _pad06 stays unset, as in the original
        if (manager->cachePool->keyCounts->Find(probe) != nullptr)
            return false;
    }

    self->flags |= FRAG_INST_FLAG_ATTACHED;
    manager->onAttach.thunk(&manager->onAttach, self->managerHandle);

    // The game's slot 48 (InitializeTransform); the header's virtuals don't
    // follow the game's slot order, so a C++ virtual call would miss it.
    if (self->ResolvedType() != nullptr)
        VCALL(this, 48, void (*)(pongCreatureInst*))(this);

    fragTypeHolder* holder = self->typeHolder;
    if (holder == nullptr)
        return true;

    // Insert in front of the current head (written as a general insert-before)
    pongCreatureInstLayout* head = holder->instancesHead;
    if (head != nullptr) {
        pongCreatureInstLayout* prev = head->prevInHolder;
        self->prevInHolder = prev;
        if (prev != nullptr)
            prev->nextInHolder = self;
        else
            holder->instancesHead = self;
        head->prevInHolder = self;
        self->nextInHolder = head;
    } else {
        holder->instancesHead = self;
        holder->instancesTail = self;
        self->nextInHolder = nullptr;
        self->prevInHolder = nullptr;
    }
    holder->instanceCount++;
    return true;
}

/**
 * pongCreatureInst::AcquireCacheEntry @ 0x8211EFC0 | size: 0xA0  [vtable slot 43]
 *
 * Takes a fragment cache entry from the pool and binds it to this instance.
 * When the pool has none to give, calls vtable slot 57 and returns null.
 */
fragCacheEntry* pongCreatureInst::AcquireCacheEntry() {
    pongCreatureInstLayout* self = Layout(this);

    fragCacheEntry* entry = fragCachePool_Acquire(FragInstManager()->cachePool);
    if (entry == nullptr) {
        // Slot 57 is probably 0x8211FA00 (no direct callers), which logs "Fragment
        // cache entry could not be allocated for instance of type '%s' at <%f %f %f>"
        VCALL(this, 57, void(*)(pongCreatureInst*))(this);
        return nullptr;
    }

    // The game's slot 53 (GetPhysicsAllocator); a C++ virtual call would use
    // the header's slot order, which isn't the game's.
    void* arg5 = VCALL(this, 53, void* (*)(pongCreatureInst*))(this);
    fragCacheEntry_Init(entry, self->typeHolder, self->type, &self->matrix[0][0], this, 0xFF, arg5, false);
    return entry;
}

/**
 * pongCreatureInst::UpdateWorldBound @ 0x82121530 | size: 0x12C  [vtable slot 46]
 *
 * For a cached instance with a type: rebuilds the world bounding sphere the
 * cache pool culls against (bound centroid moved by the world matrix, bound
 * radius), tells the manager (callback +0x34C), then runs vtable slot 47.
 */
void pongCreatureInst::UpdateWorldBound() {
    pongCreatureInstLayout* self = Layout(this);

    if (self->cacheEntry == nullptr || self->ResolvedType() == nullptr)
        return;

    const phBoundView* bound = self->archetype->bound;
    const float (*m)[4] = self->matrix;

    // The original transposes the matrix and takes three 4-wide dot products
    // with (centroid.xyz, w): the mask at 0x82619BE0 keeps xyz and the
    // constant at 0x82619BD0 supplies w = 1.0. Both are zero in the image and
    // filled by static initializers: 0x8257DBF8 copies (0, 0, 0, 1) from
    // 0x825C5850, 0x8257DBD8 copies 0x82619C20, whose xyz 0x8257DB68 sets to
    // the all-ones word at 0x825CB7F0.
    const float cx = bound->centroidOffset[0];
    const float cy = bound->centroidOffset[1];
    const float cz = bound->centroidOffset[2];

    self->worldBoundRadius = bound->radiusAroundCentroid;
    for (int axis = 0; axis < 3; ++axis)
        self->worldBoundCenter[axis] = cx * m[0][axis] + cy * m[1][axis] + cz * m[2][axis] + m[3][axis];
    self->worldBoundCenter[3] = cx;  // leftover lane of the final vector merge

    fragInstManager* manager = FragInstManager();
    manager->onBoundMoved.thunk(&manager->onBoundMoved, self->managerHandle);

    // The game's slot 47 (SyncBoneMatrices); a C++ virtual call would use the
    // header's slot order, which isn't the game's.
    VCALL(this, 47, void (*)(pongCreatureInst*))(this);
}

// Slots 2 and 3: phInst's own slot 2 (0x823D8CD0) returns the current matrix at
// +0x10 and its slot 3 does nothing; callers such as 0x820C5FCC pass an instance
// its own +0x10 matrix through slot 3. pongCreatureInst keeps that copy at +0xE0.
// The names (last matrix) are inferred from that pattern.

/**
 * pongCreatureInst::GetLastMatrix @ 0x820C8ED8 | size: 0x8  [vtable slot 2]
 * (was GetEmbeddedObject)
 */
const float* pongCreatureInst::GetLastMatrix() {
    return Layout(this)->lastMatrix[0];
}

/**
 * pongCreatureInst::SetLastMatrix @ 0x820C8E98 | size: 0x40  [vtable slot 3]
 * (was GetSubObjectTransform)
 *
 * Copies the 4x4 at matrix into +0xE0 (four 16-byte vector loads and stores).
 */
void pongCreatureInst::SetLastMatrix(const float* matrix) {
    memcpy(Layout(this)->lastMatrix, matrix, sizeof(Layout(this)->lastMatrix));
}

// The game's slot 10 (ApplyAt). The header's virtuals have gaps, so a C++
// virtual call to ApplyAt would go through slot 8.
static void CallApplyAt(pongCreatureInst* inst, const float* vec, const float* point, int component,
                        int element) {
    VCALL(inst, 10, void (*)(pongCreatureInst*, const float*, const float*, int, int))(
        inst, vec, point, component, element);
}

/**
 * pongCreatureInst::ApplyAtPosition @ 0x822C90B0 | size: 0x1C  [vtable slot 9]
 *
 * rage::phInst's: tail-calls slot 10 with the matrix translation (+0x40) as
 * the point and component and element 0.
 */
void pongCreatureInst::ApplyAtPosition(const float* vec) {
    CallApplyAt(this, vec, Layout(this)->matrix[3], 0, 0);
}

/**
 * pongCreatureInst::ApplyAt @ 0x822C90A0 | size: 0x10  [vtable slot 10]
 *
 * rage::phInst's: tail-calls slot 15 with the same arguments. What element
 * means is unknown; slots 9 and 14 pass 0.
 */
void pongCreatureInst::ApplyAt(const float* vec, const float* point, int component, int element) {
    VCALL(this, 15, void(*)(pongCreatureInst*, const float*, const float*, int, int))(
        this, vec, point, component, element);
}

/**
 * pongCreatureInst::ApplyToRope @ 0x821210A8 | size: 0x8C  [vtable slot 11]
 *
 * rage::fragInst's. Calls slot 16 with the same arguments, which is all
 * phInst's slot 11 (0x822C90D0) does. Then, for a cached instance whose cache
 * entry's behaviour is a rage::phRope, spreads vec over the rope segment
 * `component` (see phRope_ApplyAtSegment).
 */
void pongCreatureInst::ApplyToRope(const float* vec, const float* point, int component) {
    VCALL(this, 16, void(*)(pongCreatureInst*, const float*, const float*, int))(
        this, vec, point, component);

    fragCacheEntry* entry = Layout(this)->cacheEntry;
    if (entry == nullptr)
        return;

    rage::phRope* rope = AsRope(entry->behavior);
    if (rope != nullptr)
        phRope_ApplyAtSegment(rope, vec, point, component);
}

/**
 * pongCreatureInst::ApplyAtComponent @ 0x822C90E0 | size: 0x14  [vtable slot 14]
 *
 * rage::phInst's: tail-calls slot 10 with element 0.
 */
void pongCreatureInst::ApplyAtComponent(const float* vec, const float* point, int component) {
    CallApplyAt(this, vec, point, component, 0);
}

/**
 * pongCreatureInst::TouchCacheEntry @ 0x8211DDB8 | size: 0x3C  [vtable slot 22]
 * (was GetBoneTransform)
 *
 * rage::fragInst's: stamps the instance's cache entry with the pool's current
 * stamp, which keeps fragCachePool_Acquire from stealing it for now. Always
 * returns true, like phInst's slot 22 (0x8210CBD0).
 */
bool pongCreatureInst::TouchCacheEntry() {
    fragCacheEntry* entry = Layout(this)->cacheEntry;
    if (entry != nullptr)
        entry->lastUsedStamp = FragInstManager()->cachePool->currentStamp;
    return true;
}

/**
 * pongCreatureInst::PrepareForActivation @ 0x820C8F80 | size: 0x24  [vtable slot 30]
 * (was GetCreatureInfo)
 *
 * Runs fragInst's slot 30 (0x82120120) with the same arguments, then returns
 * null where fragInst's returns the instance. Callers such as 0x822C4690 and
 * 0x822C4830 pass &out and three nulls and only go on with a non-null result;
 * the name is inferred from that.
 */
void* pongCreatureInst::PrepareForActivation(void** outObject, void* arg2, void* arg3, void* arg4) {
    fragInst_PrepareForActivation(this, outObject, arg2, arg3, arg4);
    return nullptr;
}

/**
 * pongCreatureInst::FillMatrixFromConstant @ 0x822C9200 | size: 0x38  [vtable slot 31]
 * (was GetPhysicsState)
 *
 * rage::phInst's: writes the 16-byte vector at 0x82606750 to all four rows of
 * outMatrix. this is not read.
 */
void pongCreatureInst::FillMatrixFromConstant(float* outMatrix) {
    for (int row = 0; row < 4; ++row)
        memcpy(outMatrix + row * 4, lbl_82606750, sizeof(lbl_82606750));
}

/**
 * pongCreatureInst::CountBoundParts @ 0x822C92D8 | size: 0x40  [vtable slot 37]
 * (was GetCollisionFlags)
 *
 * rage::phInst's: counts the non-null part pointers of the archetype's bound.
 */
int pongCreatureInst::CountBoundParts() {
    const phBoundView* bound = Layout(this)->archetype->bound;

    int count = 0;
    for (uint32_t i = 0; i < bound->partCount; ++i) {
        if (bound->parts[i] != nullptr)
            ++count;
    }
    return count;
}

/**
 * pongCreature::Relocate @ 0x820C8858 | size: 0x7C
 *
 * Relocates creature data pointers after a memory move. Sets vtable,
 * rebases the pointer at +4 using a stride table from the relocator,
 * then calls the fixup function.
 */
void pongCreature::Relocate(void* relocator) {  // 8858_p46

    // Set vtable
    *(void**)this = (void*)0x82028144;  // pongCreature vtable

    // Rebase field_4 pointer
    void* basePtr = (void*)this->field_0x0004;
    if (basePtr && relocator) {
        uint32_t* strideTable = *(uint32_t**)((char*)relocator + 4);
        uint32_t offset = strideTable[1];
        this->field_0x0004 = (uint32_t)(uintptr_t)((char*)basePtr + offset);
    }

    pongCreature_Fixup(this, relocator);
}

// ── COMPUTATION: Matrix/Vector Operations ──────────────────────────────────

// pongCreatureInst::SetMatrix (0x820D5040) and UpdateHeading (0x8228E828) were
// duplicate lifts: 0x820D5040 is CopyAndBuildTranslationMatrix below, and
// 0x8228E828 is pongCreatureInst_E828_v12, a rage::phBound function.

// ── LocomotionStateAnim ────────────────────────────────────────────────────

/**
 * LocomotionStateAnim::ResetAccumulators @ 0x820DB9F0 | size: 0x70
 *
 * Zeros 3 float weight values at +28, +32, +36 and 4 vec128
 * accumulators at +48, +64, +80, +96. Uses AltiVec vxor to clear
 * 16-byte aligned vectors.
 */
void LocomotionStateAnim::ResetAccumulators() {  // B9F0_w
    // Zero weight floats (loop 3 iterations: +0x1C, +0x20, +0x24)
    *(float*)&this->field_0x001c = 0.0f;
    *(float*)&this->field_0x0020 = 0.0f;
    *(float*)&this->field_0x0024 = 0.0f;

    // Zero interleaved counters at +0x10, +0x14, +0x18
    this->field_0x0010 = 0;
    this->field_0x0014 = 0;
    this->field_0x0018 = 0;

    // Zero 4 vec128 accumulators at +0x30, +0x40, +0x50, +0x60
    memset(&this->field_0x0030, 0, 64);
}

/**
 * LocomotionStateAnim::InitBoundCapsule @ 0x820C3D48 | size: 0x58
 *
 * Initializes a bounding capsule from float constants. Zeroes a vec128
 * and calls the capsule initialization helper.
 */
void LocomotionStateAnim::InitBoundCapsule() {  // 3D48_g

    float zeroVec[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    float radius = 0.0f;  // loaded from constant table
    LocomotionStateAnim_InitCapsuleImpl(this, radius, zeroVec);
}

/**
 * LocomotionStateAnim::SetGlobalInstance @ 0x820C34E8 | size: 0x58
 *
 * Swaps the global LocomotionStateAnim pointer at 0x8271A378.
 * Adds a reference to the new instance and releases the old one.
 */
void LocomotionStateAnim::SetGlobalInstance(void* newInstance) {  // 34E8_p46
    extern void* g_locomotionAnimInstance;  // @ 0x8271A378

    void* oldInstance = g_locomotionAnimInstance;
    if (newInstance) rage_AddRef(newInstance);
    g_locomotionAnimInstance = newInstance;
    if (oldInstance) rage_Release(oldInstance);
}

/**
 * LocomotionState::AdvanceNode @ 0x820DEFA0 | size: 0x54
 *
 * If the linked list at this+4 is non-empty, advances to the next
 * node using FindFirstActive and stores the result.
 */
void LocomotionState::AdvanceNode() {  // EFA0_h

    void* listHead = this->field_0x0004;
    if (listHead) {
        void* next = LocomotionState_FindFirstActive(listHead);
        this->field_0x0004 = next;
    }
}

/**
 * LocomotionState::FindFirstActive @ 0x820DEF38 | size: 0x68
 *
 * Walks a linked list, skipping sentinel nodes (field+0 == 0).
 * Returns the first node whose field+8 is non-null.
 */
void* LocomotionState::FindFirstActive(void* listHead) {  // EF38_p46
    char* node = (char*)listHead;
    while (node) {
        void* sentinel = *(void**)(node + 0);
        if (sentinel != nullptr) {
            void* data = *(void**)(node + 8);
            if (data) return node;
        }
        node = *(char**)(node + 4);  // next pointer
    }
    return nullptr;
}

/**
 * LocomotionStateAnim::DispatchAnimEvent @ 0x820DEEC8 | size: 0x6C
 *
 * Finds an animation via the BEF8 lookup function, then calls its
 * vtable slot 18 with the provided argument. Returns true if the
 * animation was found and the event dispatched.
 */
bool LocomotionStateAnim::DispatchAnimEvent(void* eventArg) {  // EEC8

    void* anim = LocomotionStateAnim_FindAnim(this);
    if (!anim) return false;

    return VCALL(anim, 18, bool(*)(void*, void*))(anim, eventArg);
}

/**
 * LocomotionStateAnim::GetAnimPosition @ 0x820CB800 | size: 0x74
 *
 * Finds an animation via BEF8, calls its vtable slot 14 to get a
 * position vector, and copies the result to the output pointer.
 */
void LocomotionStateAnim::GetAnimPosition(void* outPosition) {  // B800_g

    void* anim = LocomotionStateAnim_FindAnim(this);
    if (!anim) {
        memset(outPosition, 0, 16);
        return;
    }

    VCALL(anim, 14, void(*)(void*, void*))(anim, outPosition);
}

/**
 * LocomotionStateAnim::AccumulateOffset @ 0x8223BDB0 | size: 0x6C
 *
 * Cross-product helper: calls BBB0 to get a vec128, then adds
 * the result to the accumulator.
 */
void LocomotionStateAnim::AccumulateOffset(void* accumulator) {  // BDB0_g

    float offset[4];
    LocomotionStateAnim_ComputeOffset(this, offset);

    // Add to accumulator (vec128 addition)
    float* acc = (float*)accumulator;
    acc[0] += offset[0];
    acc[1] += offset[1];
    acc[2] += offset[2];
    acc[3] += offset[3];
}

/**
 * LocomotionStateAnim::AccumulateList @ 0x8214D480 | size: 0x6C
 *
 * Walks a linked list of animation nodes, calling two helpers per
 * node to accumulate contributions (7E68 + 3AD8).
 */
void LocomotionStateAnim::AccumulateList() {  // D480_w

    void* node = (void*)this->field_0x0004;
    while (node) {
        LocomotionStateAnim_ProcessNode(this, node);
        LocomotionStateAnim_AccumNode(this, node);
        node = *(void**)((char*)node + 4);  // next
    }
}

/**
 * LocomotionStateAnim::RebasePointers @ 0x823851A8 | size: 0x6C
 *
 * Rebases two pointers (+0 and +12) using a stride table provided
 * by the relocator at r4. Each pointer is offset by the corresponding
 * stride entry.
 */
void LocomotionStateAnim::RebasePointers(void* relocator) {  // 51A8_p46
    uint32_t* strideTable = *(uint32_t**)((char*)relocator + 4);

    void* ptr0 = (void*)this->vtable;
    if (ptr0) {
        this->vtable = (void**)((char*)ptr0 + strideTable[0]);
    }

    void* ptr12 = (void*)this->field_0x000c;
    if (ptr12) {
        this->field_0x000c = (uint32_t)(uintptr_t)((char*)ptr12 + strideTable[1]);
    }
}


/**
 * LocomotionStateAnim::AdvanceRingBuffer @ 0x823804C0 | size: 0x80
 *
 * Advances a ring buffer index (mod 4), decrements the remaining
 * count, and updates internal state pointers. Used for animation
 * sample buffering.
 */
void LocomotionStateAnim::AdvanceRingBuffer() {  // 04C0_fw
    int32_t index = (int32_t)this->field_0x0008;
    int32_t remaining = (int32_t)this->field_0x000c;

    index = (index + 1) & 3;  // mod 4
    remaining--;

    this->field_0x0008 = index;
    this->field_0x000c = remaining;

    // Update current pointer based on new index
    void** buffers = (void**)this->vtable;
    this->field_0x0010 = (uint32_t)(uintptr_t)buffers[index];
}

/**
 * LocomotionStateAnim::PushBack @ 0x82234190 | size: 0x80
 *
 * Pushes an element (key + vec128) onto a growable array. If the array
 * is full, grows it before insertion.
 */
void LocomotionStateAnim::PushBack(uint32_t key, const void* vecData) {  // 4190_g

    uint32_t count = (uint32_t)this->field_0x0008;
    uint32_t capacity = (uint32_t)this->field_0x000c;

    if (count >= capacity) {
        LocomotionStateAnim_GrowArray(this);
    }

    // Insert at end: entry = base + count * 20 (key=4 + vec=16)
    char* base = (char*)this->vtable;
    char* entry = base + count * 20;
    *(uint32_t*)entry = key;
    memcpy(entry + 4, vecData, 16);

    this->field_0x0008 = count + 1;
}

// ── LocomotionStateMf ──────────────────────────────────────────────────────

/**
 * LocomotionStateMf::UpdateBlend @ 0x8222C128 | size: 0x60
 *
 * Chains 5 internal helper calls to update a blend state: scale
 * weights, blend poses, update transforms, apply constraints, finish.
 */
void LocomotionStateMf::UpdateBlend() {  // C128_w

    LocomotionStateMf_ScaleWeights(this);
    LocomotionStateMf_BlendPoses(this);
    LocomotionStateMf_UpdateTransforms(this);
    LocomotionStateMf_ApplyConstraints(this);
    LocomotionStateMf_Finish(this);
}

/**
 * LocomotionStateMf::EraseRange @ 0x822331A8 | size: 0x64
 *
 * Erases elements in range [start, end) from a contiguous array via
 * memmove. Updates the end pointer at this+8.
 */
void LocomotionStateMf::EraseRange(void* rangeStart, void* rangeEnd) {  // 31A8
    char* endPtr = this->field_0x0008;
    size_t tailSize = endPtr - (char*)rangeEnd;

    if (tailSize > 0) {
        memmove(rangeStart, rangeEnd, tailSize);
    }

    // Update end pointer
    size_t erased = (char*)rangeEnd - (char*)rangeStart;
    this->field_0x0008 = endPtr - erased;
}

/**
 * LocomotionStateMf::ComputeWeightedSum @ 0x820E3148 | size: 0x68
 *
 * Computes a weighted sum: dot product of weight array with data
 * array, scaled by a factor from this+40.
 */
float LocomotionStateMf::ComputeWeightedSum(const float* weights, const float* data, int count) {  // 3148_h
    float scale = this->field_0x0028;  // LocomotionStateMf +0x28
    float sum = 0.0f;

    for (int i = 0; i < count; i++) {
        sum += weights[i] * data[i];
    }

    return sum * scale;
}

/**
 * LocomotionStateMf::SerializeTriple @ 0x82237480 | size: 0x78
 *
 * Calls vtable slot 2 on the serializer three times with consecutive
 * field offsets from the data pointer. Used for serializing a 3-component
 * vector (e.g., position XYZ).
 */
void LocomotionStateMf::SerializeTriple(void* serializer, void* data) {  // 7480_w
    typedef void (*SerializeFn)(void*, void*);
    SerializeFn serialize = VCALL(serializer, 2, SerializeFn);

    serialize(serializer, (char*)data + 0);
    serialize(serializer, (char*)data + 4);
    serialize(serializer, (char*)data + 8);
}



////////////////////////////////////////////////////////////////////////////////
// LocomotionStateAnim — Quaternion / Matrix / Animation Utilities
////////////////////////////////////////////////////////////////////////////////

// External helpers used by newly-lifted functions
extern float LocomotionStateAnim_A1F8_g(float value, float rangeMin, float rangeMax);
extern void LocomotionStateAnim_B218_g(float* out, const float* matrix); // @ 0x8223B218
// @ 0x8224C128 / 0x8224C288 — apply one animation entry to a skeleton. Both read
// the skeleton from r5 and never read r4; callers leave junk there.
extern void LocomotionStateAnim_C128_g(void* entry, void* unusedR4, void* skeleton, float weight);
extern void LocomotionStateAnim_C288_g(void* entry, void* unusedR4, void* skeleton, float weight);

/**
 * QuaternionToMatrix3x3 @ 0x8223AD30 | size: 0xAC
 *
 * Converts a unit quaternion (x, y, z, w) stored at src into a
 * 3x3 rotation matrix written in three four-float rows to dst.
 * Each component is first scaled by the float32 approximation of sqrt(2);
 * the products are then rounded before the additions and subtractions.
 *
 * @param dst  Output 3x3 matrix (at least 44 bytes)
 * @param src  Input quaternion as 4 floats (x, y, z, w)
 */
// LocomotionStateAnim_AD30_g @ 0x8223AD30
void LocomotionStateAnim_AD30_g(float* dst, const float* src) {
    float qx = src[0];
    float qy = src[1];
    float qz = src[2];
    float qw = src[3];

    // Float32 constant at 0x82079B3C.
    float s = 0x1.6a09e6p+0f;
    float x2 = qx * s;
    float y2 = qy * s;
    float z2 = qz * s;
    float w2 = qw * s;

    float zx = z2 * x2;
    float yx = y2 * x2;
    float wz = w2 * z2;
    float zy = z2 * y2;
    float wy = w2 * y2;
    float wx = w2 * x2;
    float yy = y2 * y2;
    float zz = z2 * z2;
    float xx = x2 * x2;

    // Off-diagonal elements
    dst[1]  = yx + wz;
    dst[4]  = yx - wz;
    dst[2]  = zx - wy;
    dst[8]  = zx + wy;
    dst[6]  = wx + zy;
    dst[9]  = zy - wx;

    // Diagonal elements.
    dst[0]  = 1.0f - (zz + yy);
    dst[5]  = 1.0f - (zz + xx);
    dst[10] = 1.0f - (yy + xx);
}

extern "C" const float g_twoPi; // @ 0x8202C02C

// @ 0x822347E8 — cache the translation and canonicalize the extracted Y angle.
// The zero and vector stores precede extraction, including when self aliases matrix.
void* LocomotionStateAnim_47E8_g(void* self, void* matrix) {
    auto* output = static_cast<uint8_t*>(self);
    *reinterpret_cast<float*>(output) = 0.0f;
    alignas(16) float translation[4];
    std::memcpy(translation, static_cast<uint8_t*>(matrix) + 0x30, 16);
    std::memcpy(output + 0x10, translation, 16);
    alignas(16) float angles[4];
    rage::mat33ToEulerXZY(static_cast<const float*>(matrix), angles);
    float heading = angles[1];
    if (heading < 0.0f) heading += g_twoPi;
    *reinterpret_cast<float*>(output) = heading;
    return self;
}

/**
 * HasAnimIDs5And6 @ 0x822E09A0 | size: 0x8C
 *
 * Checks whether the animation container has both animation IDs 5
 * and 6 present. Returns true only if both lookups succeed.
 */
// LocomotionStateAnim_09A0_g @ 0x822E09A0
bool LocomotionStateAnim_09A0_g(void* self) {
    // Check for anim ID 5
    void* anim5 = ((LocomotionStateAnim*)self)->FindAnimationByID(5, 0);
    bool has5 = (anim5 != nullptr);

    // Check for anim ID 6
    void* anim6 = ((LocomotionStateAnim*)self)->FindAnimationByID(6, 0);
    bool has6 = (anim6 != nullptr);

    return has5 && has6;
}

/**
 * ClampAndTransformVector @ 0x82138110 | size: 0x8C
 *
 * Converts a quaternion to Euler angles, clamps the angles to the supplied
 * bounds, then converts the constrained rotation back to a quaternion.
 */
// LocomotionStateAnim_8110_g @ 0x82138110
void LocomotionStateAnim_8110_g(void* quat, float* minVec, float* maxVec) {
    alignas(16) float matrix[16];
    alignas(16) float vec[4];

    // Build rotation matrix from quaternion
    LocomotionStateAnim_AD30_g(matrix, (const float*)quat);

    // Extract Euler angles from the rotation matrix.
    rage::mat33ToEuler(matrix, vec);

    // Clamp each component: LocomotionStateAnim_A1F8_g(value, min, max)
    vec[0] = LocomotionStateAnim_A1F8_g(vec[0], minVec[0], maxVec[0]);
    vec[1] = LocomotionStateAnim_A1F8_g(vec[1], minVec[1], maxVec[1]);
    vec[2] = LocomotionStateAnim_A1F8_g(vec[2], minVec[2], maxVec[2]);

    // Rebuild the rotation matrix from the constrained Euler angles.
    rage::mat33FromEuler(matrix, vec);

    // Convert the matrix back to the destination quaternion.
    LocomotionStateAnim_B218_g(static_cast<float*>(quat), matrix);
}

/**
 * SetupAnimNode @ 0x820E10D8 | size: 0x9C
 *
 * Sets up an animation node: configures container data with timing
 * parameters, fetches a quaternion/translation pair, builds the rotation
 * matrix, and copies the translation into dst+48.
 */
// LocomotionStateAnim_10D8 @ 0x820E10D8
void LocomotionStateAnim_10D8(void* self, void* dst, void* /*unusedR5*/, void* container, float time) {
    if (!container) container = animationField<void*>(self, 0x140);
    if (time < g_floatZero) time = animationField<float>(self, 0xB8);
    LocomotionStateAnim_88E0_g(container, dst, animationField<void*>(self, 0x1C), 0, 1, time);
    alignas(16) float pair[8] = {};
    LocomotionStateAnim_C358_g(animationField<void*>(self, 0x1C), 0, 1, 0, pair);
    LocomotionStateAnim_AD30_g(static_cast<float*>(dst), pair);
    // The second pair row is translation; AD30 builds only the rotation rows.
    const uintptr_t destination = (reinterpret_cast<uintptr_t>(dst) + 0x30) & ~uintptr_t(15);
    std::memcpy(reinterpret_cast<void*>(destination), pair + 4, 16);
}

/**
 * RebasePointers3 @ 0x82385340 | size: 0xA0
 *
 * Rebases three pointers at self+4, self+8, self+12 using a stride
 * table from the relocator. Each non-null pointer is adjusted by
 * computing its index into the table and adding the corresponding offset.
 */
// LocomotionStateAnim_5340_p46 @ 0x82385340
void LocomotionStateAnim_5340_p46(void* self, void* relocator) {
    LocomotionStateAnim* lsa = (LocomotionStateAnim*)self;
    uint32_t baseAddr = *(uint32_t*)((char*)relocator + 4);
    uint32_t stride   = *(uint32_t*)((char*)relocator + 76);

    // Rebase pointer at field_0x0004
    uint32_t ptr4 = lsa->field_0x0004;
    if (ptr4 != 0) {
        uint32_t idx = (ptr4 - baseAddr) / stride;
        uint32_t offset = ((uint32_t*)relocator)[idx + 2];
        lsa->field_0x0004 = offset + ptr4;
    }

    // Rebase pointer at field_0x0008
    uint32_t ptr8 = (uint32_t)lsa->field_0x0008;
    if (ptr8 != 0) {
        uint32_t idx = (ptr8 - baseAddr) / stride;
        uint32_t offset = ((uint32_t*)relocator)[idx + 2];
        lsa->field_0x0008 = offset + ptr8;
    }

    // Rebase pointer at field_0x000c
    uint32_t ptr12 = lsa->field_0x000c;
    if (ptr12 != 0) {
        uint32_t idx = (ptr12 - baseAddr) / stride;
        uint32_t offset = ((uint32_t*)relocator)[idx + 2];
        lsa->field_0x000c = offset + ptr12;
    }
}

/**
 * GetAnimWeight @ 0x822481A8 | size: 0xA4
 *
 * Looks up an animation entry by type (0 or 1) and retrieves its
 * blend weight from the weight array. Returns true if weight > 0.0.
 */
// LocomotionStateAnim_81A8 @ 0x822481A8
uint32_t LocomotionStateAnim_81A8(void* /*self*/, uint32_t type, uint32_t animID,
                                  void* userdata, float* outWeight) {
    const uint8_t channel = static_cast<uint8_t>(type);
    if (channel != 0 && channel != 1) {
        return false;
    }

    // Forward the entire ID word; 04F0 narrows it inside its lookup.
    auto** animPair = static_cast<void**>(userdata);
    uint16_t index;
    bool found = LocomotionStateAnim_04F0_g(animPair[0], animID, &index);

    if (!found) {
        return false;
    }

    // The weight object holds an array pointer at +0x10, not inline floats.
    float* weightArrayBase = *(float**)((char*)animPair[1] + 16);
    uint32_t arrayOffset = (uint32_t)index << 2;  // rotlwi r8,r9,2
    float weight = *(float*)((char*)weightArrayBase + arrayOffset);

    *outWeight = weight;

    return weight > g_floatZero;
}

/**
 * FetchTransformPair @ 0x8224C4A8 | size: 0xA4
 *
 * Fetches transform data from two animation entries identified by
 * animID1 and animID2. Finds both via FindAnimationByID, retrieves
 * their world-space transforms via vtable slots, builds rotation
 * matrix, and writes to outNode.
 */
// LocomotionStateAnim_C4A8_g @ 0x8224C4A8
bool LocomotionStateAnim_C4A8_g(void* self, uint16_t animID1, uint16_t animID2, void* outNode) {
    LocomotionStateAnim* lsa = (LocomotionStateAnim*)self;

    // Find first animation
    void* anim1 = lsa->FindAnimationByID(animID1, 0);
    // Find second animation
    void* anim2 = lsa->FindAnimationByID(animID2, 0);

    if (anim1 == nullptr || anim2 == nullptr) {
        return false;
    }

    // Get world-space transform from anim1 via vtable slot 14
    typedef void* (*GetTransformFn)(void*);
    void* transform1 = VCALL(anim1, 14, GetTransformFn)(anim1);

    // Copy 16 bytes from transform1 into outNode+48
    memcpy((char*)outNode + 48, transform1, 16);

    // Get world-space transform from anim2 via vtable slot 15
    void* transform2 = VCALL(anim2, 15, GetTransformFn)(anim2);

    // Build rotation matrix from transform2 into outNode
    LocomotionStateAnim_AD30_g((float*)outNode, (const float*)transform2);

    return true;
}

/**
 * LocomotionStateAnim_FindChannelByKey @ 0x8224A390 | size: 0xA8
 *
 * Binary search through a sorted channel key array to find an
 * entry matching a 24-bit key. The key is constructed from
 * (animID_high << 16) | animID_low. On match, writes the found
 * index to *outIndex and returns the entry pointer. On miss,
 * writes the insertion point to *outIndex and returns nullptr.
 */
// LocomotionStateAnim_FindChannelByKey @ 0x8224A390
void* LocomotionStateAnim_FindChannelByKey(void* self, uint8_t animID_high, uint16_t animID_low, int32_t* outIndex) {
    LocomotionStateAnim* lsa = (LocomotionStateAnim*)self;
    uint16_t count = *(uint16_t*)&lsa->field_0x0028;

    int high = (int)count - 1;
    int low = 0;

    if (high < 0) {
        *outIndex = low;
        return nullptr;
    }

    // Construct 24-bit search key: (high << 16) | low
    uint32_t searchKey = ((uint32_t)animID_high << 16) | animID_low;

    void** keyArray = (void**)lsa->field_0x0024;

    while (low <= high) {
        int mid = (low + high) / 2;
        *outIndex = mid;

        void* entry = keyArray[mid];

        // Extract 24-bit key from entry: (byte_at_0 << 16) | uint16_at_2
        uint8_t entryHigh = *(uint8_t*)((char*)entry + 0);
        uint16_t entryLow = *(uint16_t*)((char*)entry + 2);
        uint32_t entryKey = ((uint32_t)entryHigh << 16) | entryLow;

        if (entryKey == searchKey) {
            return entry;
        }

        if (entryKey > searchKey) {
            high = mid - 1;
        } else {
            low = mid + 1;
        }
    }

    *outIndex = low;
    return nullptr;
}

/**
 * SumWeightsAndNormalize @ 0x820DBB48 | size: 0xAC
 *
 * Sums blend weights from an array (starting at self+28, count+1
 * entries of 4 bytes each), then returns the ratio of the last
 * entry's weight to the total sum. Returns 0.0 if sum == 0.0.
 * The loop is unrolled 4x in the original PPC code.
 */
// LocomotionStateAnim_BB48_g @ 0x820DBB48
float LocomotionStateAnim_BB48_g(void* self, int count) {
    LocomotionStateAnim* lsa = (LocomotionStateAnim*)self;
    float total = 0.0f;

    float* weights = (float*)&lsa->field_0x001c;
    for (int i = 0; i <= count; i++) {
        total += weights[i];
    }

    if (total == 0.0f) {
        return 0.0f;
    }

    float lastWeight = weights[count];
    return lastWeight / total;
}


/**
 * GetTransformFromAnimPair @ 0x822E0A30 | size: 0xB4
 *
 * Checks if both animation IDs 5 and 6 exist. If so, fetches the
 * transform pair (IDs 5 and 6) and copies 4 rows of 16 bytes into
 * the destination. Otherwise, fetches transform pair (IDs 0 and 1).
 */
// LocomotionStateAnim_0A30_g @ 0x822E0A30
void* LocomotionStateAnim_0A30_g(void* dst, void* animSrc) {
    bool hasBoth = LocomotionStateAnim_09A0_g(animSrc);

    if (hasBoth) {
        // Fetch transform pair for IDs 5 and 6
        float outNode[16];
        LocomotionStateAnim_C4A8_g(animSrc, 5, 6, outNode);

        // Copy 4 x 16 bytes into dst (lvx/stvx pattern)
        memcpy((char*)dst + 0,  &outNode[0],  16);
        memcpy((char*)dst + 16, &outNode[4],  16);
        memcpy((char*)dst + 32, &outNode[8],  16);
        memcpy((char*)dst + 48, &outNode[12], 16);
    } else {
        // Fetch transform pair for IDs 0 and 1
        LocomotionStateAnim_C4A8_g(animSrc, 0, 1, dst);
    }

    return dst;
}

/**
 * LocomotionStateAnim_GetMappedWeight (was LocomotionStateAnim_8250_fw)
 * @ 0x82248250 | size: 0xB4
 *
 * Modes 0/1 resolve an animation ID, map it to a signed slot through
 * animPair[1], then read animPair[3][slot]. A miss, negative slot or other
 * mode leaves outWeight untouched. A resolved weight is always stored,
 * and only a strictly positive value returns true (NaN returns false).
 */
bool LocomotionStateAnim_GetMappedWeight(void* self, uint8_t mode, uint16_t animID,
                                        void** animPair, float* outWeight) {
    (void)self;
    if (mode > 1)
        return false;
    uint16_t index;
    if (!LocomotionStateAnim_04F0_g(animPair[0], animID, &index))
        return false;
    const int32_t slot = static_cast<const int32_t*>(animPair[1])[index];
    if (slot < 0)
        return false;
    const float weight = static_cast<const float*>(animPair[3])[slot];
    *outWeight = weight;
    return weight > 0.0f;
}

/**
 * LocomotionStateAnim_EvaluateChannel @ 0x82248828 | size: 0xB4
 *
 * Look up the destination DOF's type/id in the animation's channel table.
 * On a hit, evaluate it at time * (sampleCount - 1) / duration; otherwise reset
 * the destination. Keep the unused r4 slot so the destination stays in r5.
 */
bool LocomotionStateAnim_EvaluateChannel(void* self, void* /*unusedR4*/, void* destination, float time) {
    LocomotionStateAnim* lsa = static_cast<LocomotionStateAnim*>(self);
    const uint8_t* channel = static_cast<const uint8_t*>(destination);
    const uint8_t type = channel[5];
    const uint16_t id = *reinterpret_cast<const uint16_t*>(channel + 6);
    const float duration = *reinterpret_cast<const float*>(&lsa->field_0x000c);
    const float sampleRate = static_cast<float>(static_cast<int>(lsa->field_0x000a) - 1) / duration;
    const float sampleTime = sampleRate * time;

    int32_t index;
    void* found = LocomotionStateAnim_FindChannelByKey(self, type, id, &index);
    if (found) {
        void** channels = reinterpret_cast<void**>(lsa->field_0x0024);
        // The source is in r5 and time in f1; r4 is an unused FP argument slot.
        using Evaluate = void (*)(void*, void*, void*, float);
        VCALL(destination, 4, Evaluate)(destination, nullptr, channels[index], sampleTime);
        return true;
    }

    using Reset = void (*)(void*);
    VCALL(destination, 13, Reset)(destination);
    return false;
}


// ─────────────────────────────────────────────────────────────────────────────
// pongCreatureInst::BuildTranslationMatrix @ 0x820D50A0 | size: 0x94
// Constructs a 3x4 rotation matrix from a 4x4 basis matrix and computes
// the translation column as -(R^T * t), where R is the 3x3 rotation part
// and t is the translation vector from the source (offsets 48, 52, 56).
// This effectively builds the inverse view-style matrix.
// ─────────────────────────────────────────────────────────────────────────────
void pongCreatureInst::BuildTranslationMatrix(float* outMatrix, const float* srcBasis) {
    // Copy rotation rows from source (columns become rows in 4x3 layout)
    // Row 0: srcBasis[0], srcBasis[16], srcBasis[32]
    float r00 = srcBasis[0];
    float r01 = srcBasis[4];  // src+16 = float index 4
    float r02 = srcBasis[8];  // src+32 = float index 8

    outMatrix[0]  = r00;
    outMatrix[4]  = r01;  // out+16
    outMatrix[8]  = r02;  // out+32

    // Row 1: srcBasis[1], srcBasis[5], srcBasis[9]
    float r10 = srcBasis[1];  // src+4
    float r11 = srcBasis[5];  // src+20
    float r12 = srcBasis[9];  // src+36

    outMatrix[1]  = r10;  // out+4
    outMatrix[5]  = r11;  // out+20
    outMatrix[9]  = r12;  // out+36

    // Row 2: srcBasis[2], srcBasis[6], srcBasis[10]
    float r20 = srcBasis[2];  // src+8
    float r21 = srcBasis[6];  // src+24
    float r22 = srcBasis[10]; // src+40

    outMatrix[2]  = r20;  // out+8
    outMatrix[6]  = r21;  // out+24
    outMatrix[10] = r22;  // out+40

    // Translation vector from source
    float tx = srcBasis[12]; // src+48
    float ty = srcBasis[13]; // src+52
    float tz = srcBasis[14]; // src+56

    // Translation column = -(R^T * t)
    // outMatrix[12] = -(r00*tx + r01*ty + r02*tz)
    outMatrix[12] = -(r00 * tx + r01 * ty + r02 * tz);
    // outMatrix[13] = -(r10*tx + r11*ty + r12*tz)
    outMatrix[13] = -(r10 * tx + r11 * ty + r12 * tz);
    // outMatrix[14] = -(r20*tx + r21*ty + r22*tz)
    outMatrix[14] = -(r20 * tx + r21 * ty + r22 * tz);
}

// ─────────────────────────────────────────────────────────────────────────────
// pongCreatureInst::CopyAndBuildTranslationMatrix @ 0x820D5040 | size: 0x60
// Replaces matrix with BuildTranslationMatrix's inverse of itself: r3 is the
// matrix (not an instance), copied to the stack first because
// BuildTranslationMatrix can't read and write the same rows.
// ─────────────────────────────────────────────────────────────────────────────
void pongCreatureInst::CopyAndBuildTranslationMatrix(float* matrix) {
    float copy[16];
    memcpy(copy, matrix, sizeof(copy));
    BuildTranslationMatrix(matrix, copy);
}

// ─────────────────────────────────────────────────────────────────────────────
// pongCreatureInst::CopyBoneMatrix @ 0x821183B0 | size: 0x88
// Copies a 4x4 bone transform matrix into an output buffer.
// If the creature data has the "use accumulated list" flag (bit 3 at +20),
// it uses the accumulated bone list (field at +0) with stride 192.
// Otherwise, it uses the direct bone array (field at +20) with stride 64,
// and also calls AccumulateList on it.
// ─────────────────────────────────────────────────────────────────────────────
void pongCreatureInst::CopyBoneMatrix(int boneIndex, float* outMatrix) {
    // m_pCreatureData is at this+4
    void* creatureData = (void*)this->field_0x0004;
    uint32_t flags = *(uint32_t*)((char*)creatureData + 20);

    // Check bit 3 (0x8) of the flags
    bool useAccumulatedList = (flags & 0x8) != 0;

    if (!useAccumulatedList) {
        // Use the base bone pointer array at creatureData+0
        // Stride = boneIndex * 3 * 64 = boneIndex * 192
        void* boneArrayBase = *(void**)((char*)creatureData + 0);
        int offset = boneIndex * 192;  // index * 3 * 64
        float* boneMatrix = (float*)((char*)boneArrayBase + offset);

        // Tail-call to AccumulateList which processes and outputs the matrix
        ((LocomotionStateAnim*)boneMatrix)->AccumulateList();
        return;
    }

    // Use the direct bone array at this+20
    // Stride = boneIndex * 64
    void* directBoneArray = (void*)this->field_0x0014;
    int directOffset = boneIndex * 64;
    float* srcMatrix = (float*)((char*)directBoneArray + directOffset);

    // Copy 4 x 16-byte vectors (64 bytes total)
    memcpy(outMatrix, srcMatrix, 64);
}

// ─────────────────────────────────────────────────────────────────────────────
// pongCreatureInst::FindBonePairByName @ 0x82118C58 | size: 0xD4
// Searches the bone list for two bones matching the given names (case-insensitive).
// Stores the found indices into the mapping arrays at offsets +208 and +212.
// If the bone count is zero or either bone name is not found, logs a
// diagnostic message via the nop debug function and returns early.
// ─────────────────────────────────────────────────────────────────────────────
void pongCreatureInst::FindBonePairByName(int mappingIndex, const char* boneName1, const char* boneName2) {
    uint8_t boneCount = this->field_0x01aa;  // m_boneCount

    if (boneCount == 0) {
        // No bones available — log and return
        rage_DebugLogNop(boneName1, boneName2);
        return;
    }

    int foundIndex1 = -1;
    int foundIndex2 = -1;

    for (int i = 0; i < boneCount; i++) {
        // Bone pointer array at this+176 (0xB0)
        void** boneArray = (void**)this->field_0x00b0;  // m_boneArray
        void* boneEntry = boneArray[i];

        // Bone name string starts at boneEntry+29
        const char* entryName = (const char*)((char*)boneEntry + 29);

        if (_stricmp(entryName, boneName1) == 0) {
            foundIndex1 = i;
        } else if (_stricmp(entryName, boneName2) == 0) {
            foundIndex2 = i;
        }
    }

    if (foundIndex1 == -1 || foundIndex2 == -1) {
        // One or both bones not found — log and return
        rage_DebugLogNop(boneName1, boneName2);
        return;
    }

    // Store the found indices into the mapping arrays
    uint8_t* mappingArray1 = (uint8_t*)this->field_0x00d0;  // m_boneMapping1
    uint8_t* mappingArray2 = (uint8_t*)this->field_0x00d4;  // m_boneMapping2
    mappingArray1[mappingIndex] = (uint8_t)foundIndex1;
    mappingArray2[mappingIndex] = (uint8_t)foundIndex2;
}

// ─────────────────────────────────────────────────────────────────────────────
// pongCreatureInst::ReadBoneNamesAndMap @ 0x821190F8 | size: 0x88
// Reads two bone name strings (up to 39 chars each) from the XML node's
// data sub-object via vtable slot 1, increments the bone pair count at +424,
// and delegates to FindBonePairByName to resolve and store the indices.
// ─────────────────────────────────────────────────────────────────────────────
void pongCreatureInst::ReadBoneNamesAndMap(void* xmlNode) {
    // Get the data sub-object from xmlNode+4
    xmlCallbackNode* node = (xmlCallbackNode*)xmlNode;
    void* dataObj = node->dataObj;

    // Read first bone name (vtable slot 1, max length 39) into boneName1 buffer
    char boneName1[48];
    typedef void (*ReadStringFn)(void*, char*, int);
    ReadStringFn readString = VCALL(dataObj, 1, ReadStringFn);
    readString(dataObj, boneName1, 39);

    // Read second bone name into boneName2 buffer
    char boneName2[48];
    readString(dataObj, boneName2, 39);

    // Increment the bone pair count at +424 (0x1A8)
    uint8_t pairCount = (uint8_t)this->field_0x01a8;  // m_bonePairCount
    pairCount++;
    this->field_0x01a8 = pairCount;  // m_bonePairCount

    // Find and map the bone pair using the previous count as the mapping index
    FindBonePairByName((uint8_t)(pairCount - 1), boneName1, boneName2);
}

// ─────────────────────────────────────────────────────────────────────────────
// pongCreatureInst::StoreBoneResult @ 0x82118E70 | size: 0x40
// Reads a value from the XML node's data sub-object via vtable slot 4
// and stores the result byte at this+429 (m_boneParam at +0x1AD).
// ─────────────────────────────────────────────────────────────────────────────
void pongCreatureInst::StoreBoneResult(void* xmlNode) {
    void* dataObj = ((xmlCallbackNode*)xmlNode)->dataObj;
    int result = VCALL(dataObj, 4, int(*)(void*))(dataObj);
    this->field_0x01ad = (uint8_t)result;  // m_boneParam
}

// ─────────────────────────────────────────────────────────────────────────────
// pongCreatureInst::StoreBoneFlag @ 0x82118EB0 | size: 0x50
// Reads a value from the XML node's data sub-object via vtable slot 4
// and stores whether it is non-zero as a bool at this+445 (+0x1BD).
// ─────────────────────────────────────────────────────────────────────────────
void pongCreatureInst::StoreBoneFlag(void* xmlNode) {
    void* dataObj = ((xmlCallbackNode*)xmlNode)->dataObj;
    int result = VCALL(dataObj, 4, int(*)(void*))(dataObj);
    this->field_0x01bd = (result != 0) ? 1 : 0;  // m_boneFlag
}

// ─────────────────────────────────────────────────────────────────────────────
// pongCreatureInst::SetOrClearBoneFlag8 @ 0x82118F00 | size: 0x70
// Reads a value from the XML node's data sub-object via vtable slot 4.
// If non-zero, sets bit 3 (0x08) in the flags byte at this+431 (+0x1AF).
// If zero, clears bit 3.
// ─────────────────────────────────────────────────────────────────────────────
void pongCreatureInst::SetOrClearBoneFlag8(void* xmlNode) {
    void* dataObj = ((xmlCallbackNode*)xmlNode)->dataObj;
    int result = VCALL(dataObj, 4, int(*)(void*))(dataObj);

    if (result != 0) {
        this->field_0x01af |= 0x08;  // m_visibilityFlags
    } else {
        this->field_0x01af &= ~0x08;  // m_visibilityFlags
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// pongCreatureInst::StoreMirrorFlag @ 0x82118F70 | size: 0x50
// Reads a value from the XML node's data sub-object via vtable slot 4
// and stores whether it is non-zero as a bool at this+447 (+0x1BF).
// ─────────────────────────────────────────────────────────────────────────────
void pongCreatureInst::StoreMirrorFlag(void* xmlNode) {
    void* dataObj = ((xmlCallbackNode*)xmlNode)->dataObj;
    int result = VCALL(dataObj, 4, int(*)(void*))(dataObj);
    this->field_0x01bf = (result != 0) ? 1 : 0;  // m_mirrorFlag
}

// ─────────────────────────────────────────────────────────────────────────────
// pongCreatureInst::StoreBlendFlag @ 0x82119180 | size: 0x40
// Reads a value from the XML node's data sub-object via vtable slot 4
// and stores the result byte at this+446 (+0x1BE).
// ─────────────────────────────────────────────────────────────────────────────
void pongCreatureInst::StoreBlendFlag(void* xmlNode) {
    void* dataObj = ((xmlCallbackNode*)xmlNode)->dataObj;
    int result = VCALL(dataObj, 4, int(*)(void*))(dataObj);
    this->field_0x01be = (uint8_t)result;  // m_blendFlag
}

// ─────────────────────────────────────────────────────────────────────────────
// Partition-owned creature free-function stubs (synthetic linker names that
// wrap around real work still being lifted). Moved verbatim from stubs.cpp.
// No binary symbols match these names — the codebase references them as
// C-linkage bridges; we keep them here for correct partition placement.
// ─────────────────────────────────────────────────────────────────────────────
extern "C" {

void pongCreature_BaseDtor(void* a) { (void)a; }
void pongCreature_Fixup(void* a, void* b) { (void)a; (void)b; }
void pongCreature_UpdateReplay(void* a) { (void)a; }

} // extern "C"

// pongCreatureInst helpers — synthetic linker bridges (no binary symbol)
void pongCreatureInst_RegisterPhysics(void* a, void* b) { (void)a; (void)b; }

// pongCreatureInst_EDC0_g @ 0x820DEDC0 | size: 0x104
// Matrix helper, not an instance method: basis rows use vmsum3fp128;
// translation uses vmsum4fp128 with (bone.translation.xyz, 1).
void pongCreatureInst_EDC0_g(void* dst, void* bone, void* parent) {
    float* out = static_cast<float*>(dst);
    const float* local = static_cast<const float*>(bone);
    const float* world = static_cast<const float*>(parent);
    float result[16];

    for (int row = 0; row < 4; ++row) {
        for (int axis = 0; axis < 3; ++axis) {
            // Accumulate before rounding to float, as the VMX dot products do.
            double value = 0.0;
            for (int component = 0; component < 3; ++component)
                value += static_cast<double>(local[4 * row + component])
                       * static_cast<double>(world[4 * component + axis]);
            if (row == 3)
                value += world[12 + axis];
            result[4 * row + axis] = static_cast<float>(value);
        }
        // The final vmrghw merges leave the OLD destination row's x in w.
        result[4 * row + 3] = out[4 * row];
    }

    // The original loads every input before its first store, allowing aliases.
    memcpy(out, result, sizeof(result));
}

// ─────────────────────────────────────────────────────────────────────────────
// Additional creature/creature-inst free-function bridges (C++ linkage).
// Referenced from player/network/creature translation units; no binary symbol
// matches the name. Emitted as no-op stubs until lifted.
// ─────────────────────────────────────────────────────────────────────────────
void pongCreatureInst_9030_g(void* creatureInst, void* srcPayload) {
    (void)creatureInst; (void)srcPayload;
}
void pongCreatureInst_CopyTransform(void* dst, void* src, void* helper) {
    (void)dst; (void)src; (void)helper;
}

// @ 0x8228F3E0 — composite mass-property update.
extern "C" void pongCreatureInst_F3E0_v12(phBoundView* bound);

/**
 * pongCreatureInst_E828_v12 @ 0x8228E828 | size: 0x60
 *
 * Not a pongCreatureInst function: phBoundComposite's slot 37 (0x8228E820)
 * tail-calls it with flags 0. It runs 0x8228E888 on the bound, stores what
 * 0x8228ECB0 returns for the part matrices (+0x78) and the centroid (+0x30)
 * as the radius around the centroid (+0x08), and runs 0x8228F3E0 when the low
 * byte of flags is set. (pongCreatureInst::UpdateHeading was a wrong second
 * lift of this address.)
 */
extern "C" void pongCreatureInst_E828_v12(void* self, unsigned int flags) {
    rage::phBoundComposite_RebuildExtents(self);
    auto* values = static_cast<float*>(self);
    values[2] = rage::phBoundComposite_ComputeRadius(self, rage::load_ptr32<float>(self, 0x78), values + 12);
    if (static_cast<uint8_t>(flags) != 0)
        pongCreatureInst_F3E0_v12(static_cast<phBoundView*>(self));
}

// ── pongCreature vtable slots (batch 2) ────────────────────────────────────
//
// Small virtual methods recovered from pass5_final recomp. All four are tight
// dispatcher/trampoline helpers that read fields already documented in the
// header and either:
//   * forward to another virtual slot, or
//   * hand off to an already-declared free helper.
//
// No pseudocode was available in IDA for any of them; bodies below faithfully
// reproduce the recomp control flow at the C++ level.

// Forward-declared free helpers lifted elsewhere in the build.
extern "C" void rage_C668(void* charData, void* snapshot, int index);    // @ 0x8225C668
extern "C" void pongShadowMap_EC70_g(void* emitter, void* atlas, uint32_t charFlags,
                                     void* snapshot, int flags);        // @ 0x8213EC70
extern "C" void LocomotionState_CD70_g(void* skeleton, void* poseSnapshot);  // @ 0x8214CD70

// Physics-frame ring-buffer cursors used by the rollback / shadow hooks.
// Both are declared in include/globals.h — redeclared here as C++-linkage
// shims for this translation unit.
//   • g_phFrameCounter @ 0x825C4898 — base index for per-player rollback
//     descriptor arrays; `(g_phFrameCounter + 50) * 4` becomes the byte
//     offset inside pongCreature for the current tick's descriptor slot.
//   • g_phFrameIndex   @ 0x826065DC — secondary SDA cursor used by the pose
//     rollback restore path.
extern "C" uint32_t g_phFrameCounter;  // @ 0x825C4898
extern "C" uint32_t g_phFrameIndex;    // @ 0x826065DC

// Renderer-side shadow-atlas / light slot pointer (SDA+25424 = 0x82606350).
// Read as an opaque renderer handle by RegisterShadowCasters and passed
// straight through to pongShadowMap_EC70_g.
extern "C" void* g_phShadowAtlasSlot;  // @ 0x82606350

// ─────────────────────────────────────────────────────────────────────────────
// pongCreature::UpdateWithIdentity(int updateMode)
//                                [vtable 0x82027B08 slot 0 @ 0x820C6358 | size: 0x1C]
//
// (Was lifted as ~pongCreature; it destroys nothing.) Tail-calls slot 6 of the
// object's own vtable with the identity matrix at 0x825CB800 and the caller's
// argument: `mr r5, r4; addi r4, ..., -0x4800; lwz r9, 0x18(r10); bctr`.
// ─────────────────────────────────────────────────────────────────────────────
void pongCreature::UpdateWithIdentity(int updateMode) {
    VCALL(this, 6, void (*)(pongCreature*, const float*, int))(this, g_identityMatrixRef, updateMode);
}

// ─────────────────────────────────────────────────────────────────────────────
// pongCreature::DestroyThunk(int flags)
//                                [vtable 0x82027B08 slot 2 @ 0x820C8618 | size: 0x8]
//
// (Previously named "vfn_2" — renamed for clarity.)
//
// Multiple-inheritance adjust-and-dispatch thunk: `addi r3,r3,-16;
// b 0x820C5398`. Rewinds the phUpdateObject-base `this` to the object's start
// and tail-calls the scalar deleting destructor
// (pongCreature::ScalarDeletingDtor @ 0x820C5398) with the caller's flags,
// which stay in r4.
// ─────────────────────────────────────────────────────────────────────────────
void pongCreature::DestroyThunk(int flags) {
    pongCreature* primary = (pongCreature*)((char*)this - 16);
    primary->ScalarDeletingDtor(flags);
}

// ─────────────────────────────────────────────────────────────────────────────
// pongCreature::SavePoseSnapshot()
//                                [vtable 0x82027B08 slot 1 @ 0x820C67C0 | size: 0x80]
//
// (Was RestorePoseFromRollback; earlier misnamed "ScalarDtor".)
//
// `this` is the phUpdateObject base (creature + 0x10). Picks the pose
// snapshot for the current frame from the word table at this + 50*4, indexed
// by g_phFrameIndex, and writes the skeleton's pose into it:
//
//   • If bit 0 of the byte at +0x11 of the descriptor reached through
//     character (+0x90) → +0x14 → +0x40 → [0] → [0] is set, the
//     skeleton and the snapshot go to LocomotionState_CD70_g (tail call).
//   • Otherwise the skeleton's bone matrices (count * 64 bytes from its
//     +0x14) are copied into the snapshot.
// ─────────────────────────────────────────────────────────────────────────────
void pongCreature::SavePoseSnapshot() {
    void* const* snapshots = (void* const*)((char*)this + 50 * 4);
    void* snapshot = snapshots[g_phFrameIndex];
    if (snapshot == nullptr) return;

    void*   charObj   = *(void**)((char*)this + 0x90);   // creature +0xA0
    void*   charData  = *(void**)((char*)charObj + 0x14);
    void*   emitter   = *(void**)((char*)charData + 0x40);
    void*   holder    = *(void**)emitter;
    void*   desc      = *(void**)holder;
    uint8_t animFlags = *(uint8_t*)((char*)desc + 0x11);

    void* skeleton = *(void**)((char*)this + 0x9C);      // creature +0xAC
    if ((animFlags & 0x1) != 0) {
        LocomotionState_CD70_g(skeleton, snapshot);
        return;
    }

    void*    matrices = *(void**)((char*)skeleton + 0x14);
    void*    data     = *(void**)((char*)skeleton + 0x04);
    uint16_t count    = *(uint16_t*)((char*)data + 0x0C);
    memcpy(snapshot, matrices, (size_t)count << 6);  // 64 bytes per bone matrix
}

// ─────────────────────────────────────────────────────────────────────────────
// pongCreature::RegisterShadowCasters(bool useSecondaryEmitter)
//                                [vtable 0x82027B08 slot 5 @ 0x820C60C8 | size: 0xB4]
//
// (Previously named "vfn_5" — renamed for clarity.)
//
// `this` is the phUpdateObject base (creature + 0x10).
//
//   1. Fetch the snapshot for this frame from the same word table the pose
//      snapshot slot uses, indexed by g_phFrameCounter.
//   2. Walk character (+0x90) → +0x14:
//        • primary shadow emitter  : +0x40
//        • secondary shadow emitter: +0x48 (when useSecondaryEmitter)
//      A null emitter short-circuits — nothing to register.
//   3. rage_C668(charData, snapshot, -1), then pongShadowMap_EC70_g(emitter,
//      atlas, charData's +4 word, snapshot, flags) with flags
//        `(useSecondaryEmitter ? 0 : 0x10000) | 63`.
// ─────────────────────────────────────────────────────────────────────────────
void pongCreature::RegisterShadowCasters(bool useSecondaryEmitter) {
    void* const* snapshots = (void* const*)((char*)this + 50 * 4);
    void* snapshot = snapshots[g_phFrameCounter];

    void*    charObj   = *(void**)((char*)this + 0x90);   // creature +0xA0
    void*    charData  = *(void**)((char*)charObj + 0x14);
    void*    atlas     = g_phShadowAtlasSlot;
    uint32_t charFlags = *(uint32_t*)((char*)charData + 0x04);

    void* emitter = useSecondaryEmitter ? *(void**)((char*)charData + 0x48)
                                        : *(void**)((char*)charData + 0x40);
    if (emitter == nullptr) return;

    rage_C668(charData, snapshot, -1);

    const int flags = (useSecondaryEmitter ? 0 : 0x10000) | 63;
    pongShadowMap_EC70_g(emitter, atlas, charFlags, snapshot, flags);
}

// ─────────────────────────────────────────────────────────────────────────────
// pongCreature::Reset(void* world, void* scene)
//                                [vtable 0x82027B08 slot 3 @ 0x820C6840 | size: 0x160]
//
// Per-activation reset entry point. Runs the superclass phUpdateObject::Reset
// to rebind world/scene pointers, fixes up the locomotion state's transform
// cursor, kicks the anim blender, then snaps the mover back to its rest
// position.
//
// Control flow reconstructed from the recomp scaffold:
//
//   1. If this creature has an owning locomotion host (+224 byte != 0):
//        • Call vt[1] on host +228 and vt[5] on same, resetting its state.
//        • Call vt[1] on the collider block at +232 (another sub-state).
//        • Zero the host's live-anim fields (+60..+65) and mark the
//          "needs rebuild" bit at +64 on its local anim buffer (offset +16).
//        • If an active anim descriptor lives at host+48, zero its first
//          4 header bytes, the word at +8, its 16-byte vector at +16 and
//          the float at +32.
//
//   2. Forward-chain to phUpdateObject::vfn_3(this, world, scene) — the
//      actual physics-world bind step.
//
//   3. Patch the locomotion state cache:
//        • m_pCharCtx (+156)->+8   = m_pChar (+148) + 16   (transform ptr)
//        • util_C880 fx helper resolves live mesh bindings.
//
//   4. Run LocomotionStateAnim_BBC8_g on the mover-anim block (+172).
//
//   5. If this creature's own m_playerIndex (+188) matches the currently
//      bound render player (g_render_obj_ptr +296), pass `needsFlip=1`
//      to pongMover::Reset; otherwise `needsFlip=0`. Mover is at +152.
//
//   6. Patch the per-player input-slot transform table entry
//      ((g_input_obj_ptr)[m_playerIndex + 17]) back to m_pChar+16, and
//      clear flags at +180, +181, +214, +215 (stale-transform bits).
// ─────────────────────────────────────────────────────────────────────────────

// Helpers called from pongCreature::Reset.
extern "C" void phUpdateObject_Reset(void* self, void* world, void* scene);        // @ 0x8227D5B0
extern "C" void pongCreature_D938_wrh(void* charCtx, void* physicsPtr,
                                      void* descPtr, void* frameData,
                                      void* animPtr);                              // @ 0x820FD938
extern "C" void util_C880(void* charCtx);                                          // @ 0x8214C880
extern "C" void LocomotionStateAnim_BBC8_g(void* animBlock);                       // @ 0x820CBBC8

void pongCreature::Reset(void* world, void* scene) {
    // --- Step 1: tear down locomotion host, if present.
    uint8_t hasHost = *(uint8_t*)((char*)this + 224);
    if (hasHost != 0) {
        void*  host      = *(void**)((char*)this + 228);
        void** hostVt    = *(void***)host;
        ((void(*)(void*))hostVt[1])(host);  // vt[1] — teardown
        void** hostVt2   = *(void***)host;
        ((void(*)(void*, int))hostVt2[5])(host, 0);  // vt[5] — reset

        void*  colliderBlock = *(void**)((char*)this + 232);
        void*  colliderSub   = *(void**)((char*)colliderBlock + 52);
        void** subVt         = *(void***)colliderSub;
        ((void(*)(void*))subVt[1])(colliderSub);

        // Zero live-anim fields and mark rebuild bit.
        *(uint32_t*)((char*)colliderBlock + 60) = 0;
        *(uint8_t*)((char*)colliderBlock + 64)  = 0;
        *(uint8_t*)((char*)colliderBlock + 65)  = 0;
        // Zero 16-byte transform vector at +16 and set +16 byte to 1.
        uint8_t* animBuf = (uint8_t*)colliderBlock + 16;
        memset(animBuf, 0, 16);
        animBuf[16] = 1;

        // If an active anim descriptor exists at +48, zero its header bytes,
        // the vector at +16, the word at +8 and the float at +32 (the asm
        // loads 0.0f from 0x8202D110).
        void* activeAnim = *(void**)((char*)colliderBlock + 48);
        if (activeAnim != nullptr) {
            *(uint8_t*)((char*)activeAnim + 4) = 0;
            *(uint8_t*)((char*)activeAnim + 5) = 0;
            *(uint8_t*)((char*)activeAnim + 6) = 0;
            *(uint8_t*)((char*)activeAnim + 7) = 0;
            memset((char*)activeAnim + 16, 0, 16);
            *(uint32_t*)((char*)activeAnim + 8) = 0;
            *(float*)((char*)activeAnim + 32) = 0.0f;
        }
    }

    // --- Step 2: phUpdateObject::vfn_3 — bind world/scene.
    phUpdateObject_Reset(this, world, scene);

    // --- Step 3: locomotion state transform pointer + mesh binding refresh.
    void* charData    = *(void**)((char*)this + 148);
    void* charCtx     = *(void**)((char*)this + 156);
    *(void**)((char*)charCtx + 8) = (void*)((char*)charData + 16);
    util_C880(charCtx);

    // --- Step 4: kick anim blender.
    LocomotionStateAnim_BBC8_g(*(void**)((char*)this + 172));

    // --- Step 5: decide mover-flip based on render ownership.
    extern void* g_render_obj_ptr;  // @ 0x825EAB2C
    int32_t thisPlayer  = *(int32_t*)((char*)this + 188);
    void*   renderObj   = g_render_obj_ptr;  // not null-checked in the asm
    int32_t boundPlayer = *(int32_t*)((char*)renderObj + 296);
    bool    needsFlip   = (thisPlayer == boundPlayer);

    static_cast<pongMover*>(*(void**)((char*)this + 152))->Reset(needsFlip);

    // --- Step 6: patch per-player input-slot transform entry, clear stale bits.
    extern void* g_input_obj_ptr;  // @ 0x825EAB28
    void*    charData2    = *(void**)((char*)this + 148);
    int32_t  slot         = *(int32_t*)((char*)this + 188) + 17;
    void**   inputTable   = (void**)g_input_obj_ptr;
    inputTable[slot]      = (void*)((char*)charData2 + 16);

    *(uint8_t*)((char*)this + 180) = 0;
    *(uint8_t*)((char*)this + 181) = 0;
    *(uint8_t*)((char*)this + 214) = 0;
    *(uint8_t*)((char*)this + 215) = 0;
}



// ═════════════════════════════════════════════════════════════════════════════
// pongCreature — replay, teleport requests and the per-frame pose
// ═════════════════════════════════════════════════════════════════════════════
//
// The header's pongCreature fields don't match the binary, so these functions
// read the object through pongCreatureLayout, which holds only offsets their
// asm proves. Offsets in comments are the game's 32-bit ones, counted from the
// start of the object; vtable slot functions (StepLocomotion here) get the
// phUpdateObject base at +0x10 as `this` instead.

// 4x4 floats, 16-byte aligned in the game: rows a, b, c and the translation d.
struct pongCreatureMatrix {
    float a[4];
    float b[4];
    float c[4];
    float d[4];
};

// Bone count and flags of a skeleton; 0x8224C128 reads the same fields.
struct pongCreatureSkeletonData {
    uint8_t  _pad00[0x0C];
    uint16_t boneCount;  // +0x0C
    uint8_t  _pad0E[0x06];
    uint32_t flags;      // +0x14  SKELETON_FLAG_*
};

static const uint32_t SKELETON_FLAG_APPLY_C288 = 0x1;  // animations go through 0x8224C288, not 0x8224C128

// The skeleton at pongCreature+0xAC, and the one a fragment cache entry keeps
// at +0x1E4 (inferred: SavePoseSnapshot copies boneCount 64-byte rows
// from +0x14, and 0x8224C128 indexes 0x50-byte records at +0x0C).
struct pongCreatureSkeleton {
    uint8_t                   _pad00[0x04];
    pongCreatureSkeletonData* data;          // +0x04
    uint8_t                   _pad08[0x04];
    uint8_t*                  bones;         // +0x0C  BONE_RECORD_SIZE records, each starting with a 4x4
    uint8_t                   _pad10[0x04];
    pongCreatureMatrix*       boneMatrices;  // +0x14  one 4x4 per bone
};

static const uint32_t BONE_RECORD_SIZE = 0x50;

// pongCreature+0x24, inside the phUpdateObject base. RefreshBallSlot reads
// only its +0x04 → +0x14 flags word, the same path as the skeleton's.
struct pongCreatureObject24 {
    uint8_t                   _pad00[0x04];
    pongCreatureSkeletonData* data;  // +0x04
};

// Animation entries applied to a skeleton one by one (0x82386380 walks the
// same shape).
struct pongAnimEntryList {
    uint8_t  _pad00[0x08];
    void**   entries;  // +0x08
    uint16_t count;    // +0x0C
};

// The two objects at pongCreatureCharData+0xD8/+0xDC. KickWorkers gives each
// the frame's time step and the skeleton and sets its event, so they are
// taken to run on another thread (what they simulate is unproven).
struct pongCreatureWorker {
    uint8_t               _pad00[0x24];
    void*                 field24;    // +0x24  passed to RefreshBallSlot, which doesn't read it
    uint8_t               _pad28[0x2C];
    void*                 wakeEvent;  // +0x54  set through 0x82566C40 (NtSetEvent)
    uint8_t               _pad58[0x04];
    float                 timeStep;   // +0x5C
    uint8_t               kicked;     // +0x60
    uint8_t               _pad61[0x1B];
    pongCreatureSkeleton* skeleton;   // +0x7C
};

// pongCreature+0xA0 → +0x14. RegisterShadowCasters reads its shadow emitters
// at +0x40/+0x48; Teleport (0x820C7A28) also checks the workers.
struct pongCreatureCharData {
    uint8_t             _pad00[0xD8];
    pongCreatureWorker* workers[2];  // +0xD8, +0xDC
};

struct pongCreatureChar {
    uint8_t               _pad00[0x14];
    pongCreatureCharData* data;     // +0x14
    void*                 field18;  // +0x18  SyncFragmentPose does nothing while null
};

// pongCreature+0xBC: the header's pongPlayerState (pong_player.cpp lifts its
// predicates 0x820CD550..0x820CD6B8 and its update 0x820CD228).
struct pongPlayerStateView {
    uint8_t _pad00[0x20];
    float   lookAtTarget[4];  // +0x20  inferred: UpdateAnimation hands it to the look-at controller
    uint8_t _pad30[0x80];
    float   field_B0;         // +0xB0  UpdateReplay and 0x820CD228 test it for [0, 1]
};

// rage::phInst, as far as the physics level needs it.
struct phInstLevelView {
    void**   vtable;      // +0x00
    void*    archetype;   // +0x04
    uint16_t levelIndex;  // +0x08
};

// The cell pongCreature+0x160 points at; RefreshBallSlot copies the ball's
// instance into it.
struct pongBallInstSlot {
    phInstLevelView* inst;  // +0x00
};

// rage::phLevel and rage::phSimulator, reduced to the calls made here (the
// same reading as pong_player.cpp's phLevelView).
struct phLevelCreatureView {
    virtual void slot0();
    virtual void slot1();
    virtual void slot2();
    virtual void slot3();
    virtual void* GetActiveBody(uint16_t index); // slot 4
    virtual void slot5();
    virtual void slot6();
    virtual void slot7();
    virtual void slot8();
    virtual void slot9();
    virtual void slot10();
    virtual void UpdateObjectLocation(uint16_t index); // slot 11

    uint8_t  _pad04[0x18];
    uint8_t* objectStates; // +0x1C
    bool IsActive(uint16_t index) const { return (objectStates[index] & 7) == 0; }
};

struct phSimulatorCreatureView {
    void*                vtable;  // +0x00
    phLevelCreatureView* level;   // +0x04
};

extern phSimulatorCreatureView* g_pPhysicsSim;    // @ 0x825F5BD0
extern phLevelCreatureView*     g_pPhysicsLevel;  // @ 0x826065E4
extern phInstLevelView**        lbl_8271A2F4;     // @ 0x8271A2F4  *it is the ball's instance

// The replay data at *lbl_8271A2EC, as UpdateReplay and ReplayStarting read it
// (pong_game.cpp calls the same pointer a shadow/mode table root).
struct pongReplayFrame {
    uint8_t _pad00[0x10];
    float   position[4];  // +0x10  ReplayStarting turns the matrix by pi about y when z < 0
    float   field_20;     // +0x20  clamped to [0, 1] into pongReplayValues
};

struct pongReplayPlayerBlock {
    uint8_t         _pad0000[0xA8D0];
    pongReplayFrame frame;  // +0xA8D0
    uint8_t         _padA8F4[0x0C];
};  // 0xA900 bytes

struct pongReplayAnimSlot {
    pongAnimEntryList list;  // +0x00
    uint8_t           _pad10[0x20];
};  // 0x30 bytes

struct pongReplayData {
    uint8_t               _pad00000[0x11370];
    pongReplayPlayerBlock players[2];    // +0x11370  picked by playerIndex == 0 / != 0
    uint8_t               _pad26570[0x426FC];
    pongReplayAnimSlot    animLists[2];  // +0x68C6C  indexed by playerIndex
    uint8_t               _pad68CCC[0x24];
    uint32_t              field_68CF0;   // +0x68CF0  see UpdateAnimation
};

// *lbl_8271A2F0: one 16-byte record per player from +0x04.
struct pongReplayValueRecord {
    uint8_t _pad00[0x08];
    float   current;   // +0x08
    float   previous;  // +0x0C  ReplayStarting moves current here before writing it
};

struct pongReplayValues {
    uint8_t               _pad00[0x04];
    pongReplayValueRecord players[2];  // +0x04
};

extern void* lbl_8271A2EC;  // @ 0x8271A2EC
extern void* lbl_8271A2F0;  // @ 0x8271A2F0

// The .data block at 0x825CAEB8 (hud.cpp); +0x54 holds the 1/60 s tick.
struct frameTimingBlockView {
    uint8_t _pad00[0x54];
    float   tickSeconds;  // +0x54
};
extern const uint8_t g_hudShell_UpdateBlock[0x60];  // @ 0x825CAEB8

// rage::fragType's byte at +0x1AF, past what rage_grm.hpp's fragType covers.
struct fragTypeFlagsView {
    uint8_t _pad000[0x1AF];
    uint8_t flags1AF;  // +0x1AF  bit 2: SyncFragmentPose copies bone records instead of matrices
};

extern uint32_t lbl_825C9F3C[5];  // @ 0x825C9F3C  UpdateAnimation skips the look-at while [1] is nonzero
extern uint8_t  lbl_82606325;     // @ 0x82606325  ... or while this is set

struct pongCreatureLayout {
    void**                 vtable;                      // +0x000  0x82027AFC
    uint8_t                _pad004[0x0C];
    void**                 updateVtable;                // +0x010  rage::phUpdateObject base, 0x82027B08
    uint8_t                _pad014[0x10];
    pongCreatureObject24*  object24;                    // +0x024
    uint8_t                _pad028[0x78];
    pongCreatureChar*      character;                   // +0x0A0
    pongCreatureInst*      inst;                        // +0x0A4  rage::fragInst
    void*                  swingState;                  // +0x0A8  0x820CB208 gets it with the swing target
    pongCreatureSkeleton*  skeleton;                    // +0x0AC
    uint8_t                _pad0B0[0x0C];
    pongPlayerStateView*   state;                       // +0x0BC
    uint8_t                _pad0C0[0x0C];
    int32_t                playerIndex;                 // +0x0CC
    uint8_t                _pad0D0[0x15];
    uint8_t                teleportPending;             // +0x0E5  a deferred RequestTeleport waits
    uint8_t                _pad0E6[0x0A];
    uint8_t                lookAtEnabled;               // +0x0F0
    uint8_t                _pad0F1[0x07];
    pongLookAtController*  lookAt;                      // +0x0F8  inferred from the callees' addresses
    uint8_t                _pad0FC[0x14];
    pongCreatureMatrix     teleportMatrix;              // +0x110
    uint8_t                teleportResetWorkers;        // +0x150
    uint8_t                teleportKeepInstanceMatrix;  // +0x151  only UpdateReplay passes it on
    uint8_t                teleportHoldFrame;           // +0x152  UpdateReplay waits one call while set
    uint8_t                _pad153[0x0D];
    pongBallInstSlot*      ballSlot;                    // +0x160
};

// @ 0x820C7A28 — logs "pongCreature::Teleport() - teleporting player[%d] to
// [%f,%f,%f]"; with resetWorkers and a worker present it runs UpdateAnimation
// first (when updatePoseFirst) and resets the workers to the skeleton (0x820FAB78);
// unless keepInstanceMatrix it moves the instance there (0x820C8FA8).
extern void pongCreature_Teleport(pongCreature* creature, const pongCreatureMatrix* matrix,
                                  bool resetWorkers, bool updatePoseFirst, bool keepInstanceMatrix);
// @ 0x820CC5A8 — the player state's list for the replay list it is given
extern pongAnimEntryList* game_C5A8(pongPlayerStateView* state, pongAnimEntryList* replayList);
// @ 0x8214C8F8 (defined in locomotion.cpp)
extern void LocomotionStateAnim_C8F8_g(void* skeleton);
// @ 0x82566C40 — NtSetEvent(handle, 0); returns whether it worked
extern "C" void pg_6C40_g(void* handle);

// pongPlayerState's update and predicates (pong_player.cpp lifts them as
// pongPlayer members).
extern "C" void pongPlayer_D228_g(pongPlayerStateView* state);  // @ 0x820CD228
extern "C" bool pongPlayer_D550_g(pongPlayerStateView* state);  // @ 0x820CD550
extern "C" bool pongPlayer_D598_g(pongPlayerStateView* state);  // @ 0x820CD598
extern "C" bool pongPlayer_D5F0_g(pongPlayerStateView* state);  // @ 0x820CD5F0
// @ 0x820CD7B0 — writes the swing's target position to outTarget and returns it
extern float* pongPlayer_D7B0_g(float* outTarget, pongPlayerStateView* state);
// @ 0x820CB208
extern void pongPlayer_B208_g(void* swingState, const float* target, uint8_t flag);

// pongLookAtController (vtable 0x82027AEC, whose slot 1 is 0x820D28E0) calls.
extern void game_2950(pongLookAtController* lookAt);                                 // @ 0x820D2950

static pongCreatureLayout* CreatureLayout(pongCreature* creature) {
    return reinterpret_cast<pongCreatureLayout*>(creature);
}

// Vtable 0x82027B08's slots get the phUpdateObject base at +0x10.
static pongCreature* CreatureFromUpdateBase(pongCreature* updateBase) {
    return reinterpret_cast<pongCreature*>(reinterpret_cast<char*>(updateBase) - 0x10);
}

static pongReplayData* ReplayData() {
    return static_cast<pongReplayData*>(lbl_8271A2EC);
}

static const pongReplayFrame& ReplayFrame(int32_t playerIndex) {
    return ReplayData()->players[playerIndex == 0 ? 0 : 1].frame;
}

static pongReplayValueRecord& ReplayValue(int32_t playerIndex) {
    return static_cast<pongReplayValues*>(lbl_8271A2F0)->players[playerIndex];
}

static float FrameTickSeconds() {
    return reinterpret_cast<const frameTimingBlockView*>(g_hudShell_UpdateBlock)->tickSeconds;
}

// The asm's fsel pair against the doubles 0.0 (0x82079B00) and 1.0
// (0x82079B08): NaN and negatives give 0, anything from 1 up gives 1.
static float ClampUnit(float value) {
    const float floored = value >= 0.0f ? value : 0.0f;
    return floored - 1.0f >= 0.0f ? 1.0f : floored;
}

// Inlined in UpdateReplay (and in 0x82386380): every entry goes through
// 0x8224C128, or 0x8224C288 for skeletons flagged so, with weight 0.
static void ApplyAnimEntries(const pongAnimEntryList* list, pongCreatureSkeleton* skeleton) {
    typedef void (*ApplyFn)(void* entry, void* unusedR4, void* skeleton, float weight);
    const ApplyFn apply = (skeleton->data->flags & SKELETON_FLAG_APPLY_C288) != 0
                              ? LocomotionStateAnim_C288_g
                              : LocomotionStateAnim_C128_g;
    for (int i = 0; i < list->count; ++i)
        apply(list->entries[i], nullptr, skeleton, 0.0f);
}

// Inlined in UpdateReplay and StepLocomotion once a deferred teleport ran.
// Rows a, b, c get only x, y and z; d is cleared whole.
static void ClearTeleportRequest(pongCreatureLayout* self) {
    self->teleportPending = 0;
    pongCreatureMatrix& m = self->teleportMatrix;
    m.a[0] = 1.0f; m.a[1] = 0.0f; m.a[2] = 0.0f;
    m.b[0] = 0.0f; m.b[1] = 1.0f; m.b[2] = 0.0f;
    m.c[0] = 0.0f; m.c[1] = 0.0f; m.c[2] = 1.0f;
    memset(m.d, 0, sizeof(m.d));
    self->teleportResetWorkers = 0;
    self->teleportKeepInstanceMatrix = 0;
    self->teleportHoldFrame = 0;
}

// Inlined in UpdateReplay and StepLocomotion (two unrolled copies each).
static void KickWorkers(pongCreature* creature) {
    pongCreatureLayout* self = CreatureLayout(creature);
    pongCreatureCharData* data = self->character->data;
    for (int i = 0; i < 2; ++i) {
        pongCreatureWorker* worker = data->workers[i];
        if (worker == nullptr)
            continue;
        worker->timeStep = FrameTickSeconds();
        worker->skeleton = self->skeleton;
        pg_6C40_g(worker->wakeEvent);
        worker->kicked = 1;
        creature->RefreshBallSlot(data->workers[i]->field24, 0);
    }
}

/**
 * pongCreature::ReplayStarting @ 0x820C5780 | size: 0x138
 * (was pongCreature_ReplayStarting_5780)
 *
 * Called from 0x82196348. Builds a matrix at this player's replay frame
 * position, turned by pi about y when the frame's z is negative, records the
 * frame's [0, 1] value and asks for a deferred teleport there.
 */
void pongCreature::ReplayStarting(bool keepInstanceMatrix) {
    pongCreatureLayout* self = CreatureLayout(this);
    const pongReplayFrame& frame = ReplayFrame(self->playerIndex);

    pongCreatureMatrix matrix;
    memcpy(&matrix, g_identityMatrixRef, sizeof(matrix));
    if (frame.position[2] < 0.0f) {
        pongCreatureMatrix turn;
        rage::mat33RotationY(turn.a, 3.14159274f);  // 0x82079B30
        rage::mat33ComposeInPlace(reinterpret_cast<float*>(&matrix), reinterpret_cast<const float*>(&turn));
    }
    memcpy(matrix.d, frame.position, sizeof(matrix.d));

    pongReplayValueRecord& value = ReplayValue(self->playerIndex);
    value.previous = value.current;
    value.current = ClampUnit(frame.field_20);

    RequestTeleport("pongCreature::ReplayStarting", &matrix, true, false, keepInstanceMatrix);
}

/**
 * pongCreature::RefreshBallSlot @ 0x820C58B8 | size: 0x108
 * (was pongCreature_58B8_g)
 *
 * When bit 1 of object24's flags is set, copies the ball's instance into the
 * cell at +0x160 and, if the ball is active in the physics level, asks the
 * level for its body; if there is one, it checks and asks once more and drops
 * that answer. The asm stores both arguments to the caller's frame and never
 * reads them.
 */
void pongCreature::RefreshBallSlot(void* /*unusedArg*/, int /*unusedFlag*/) {
    pongCreatureLayout* self = CreatureLayout(this);
    if ((self->object24->data->flags & 0x2) == 0)
        return;

    self->ballSlot->inst = *lbl_8271A2F4;
    phInstLevelView* ball = self->ballSlot->inst;
    if (ball == nullptr)
        return;

    phLevelCreatureView* level = g_pPhysicsSim->level;
    if (!level->IsActive(ball->levelIndex))
        return;
    if (level->GetActiveBody(ball->levelIndex) == nullptr)
        return;

    ball = self->ballSlot->inst;
    level = g_pPhysicsSim->level;
    if (level->IsActive(ball->levelIndex))
        level->GetActiveBody(ball->levelIndex);
}

/**
 * pongCreature::UpdateReplay @ 0x820C59C0 | size: 0x358
 * (was pongCreature_59C0_g)
 *
 * Called from pongPlayer::UpdateReplay. Puts the instance at this player's
 * replay frame position, applies the replay animations to the skeleton (through
 * the player state's list while its +0xB0 is in [0, 1]), syncs the fragment
 * pose, records the frame's [0, 1] value, runs a deferred teleport unless
 * teleportHoldFrame asks to wait one more call, and wakes the workers.
 */
void pongCreature::UpdateReplay() {
    pongCreatureLayout* self = CreatureLayout(this);
    const pongReplayFrame& frame = ReplayFrame(self->playerIndex);

    // Slot 3 (SetLastMatrix) keeps the old matrix before it is overwritten.
    VCALL(self->inst, 3, void (*)(pongCreatureInst*, const float*))(self->inst, Layout(self->inst)->matrix[0]);
    pongCreatureInstLayout* inst = Layout(self->inst);
    memcpy(inst->matrix[3], frame.position, sizeof(inst->matrix[3]));
    g_pPhysicsLevel->UpdateObjectLocation(inst->levelIndex);

    pongAnimEntryList* list = &ReplayData()->animLists[self->playerIndex].list;
    pongPlayerStateView* state = self->state;
    if (state->field_B0 >= 0.0f && state->field_B0 <= 1.0f)
        list = game_C5A8(state, list);
    ApplyAnimEntries(list, self->skeleton);

    LocomotionStateAnim_C8F8_g(self->skeleton);
    SyncFragmentPose();

    ReplayValue(self->playerIndex).current = ClampUnit(frame.field_20);

    if (self->teleportPending) {
        if (self->teleportHoldFrame) {
            self->teleportHoldFrame = 0;
        } else {
            pongCreature_Teleport(this, &self->teleportMatrix, self->teleportResetWorkers, false,
                                  self->teleportKeepInstanceMatrix);
            ClearTeleportRequest(self);
        }
    }

    KickWorkers(this);
}

// pongPlayer::UpdateReplay (pong_player.cpp) declares 0x820C59C0 by its symbol name.
void pongCreature_59C0_g(void* creature) {
    static_cast<pongCreature*>(creature)->UpdateReplay();
}

/**
 * pongCreature::StepLocomotion @ 0x820C5D18 | size: 0x150  [vtable 0x82027B08 slot 7]
 * (was pongCreature_vfn_7)
 *
 * Per-frame step, skipped while the instance's +0x120 byte is clear: updates
 * the animation and the fragment pose, then either runs a deferred teleport
 * or wakes the workers.
 */
void pongCreature::StepLocomotion() {
    pongCreature* creature = CreatureFromUpdateBase(this);
    pongCreatureLayout* self = CreatureLayout(creature);
    if (Layout(self->inst)->flag120 == 0)
        return;

    creature->UpdateAnimation();
    creature->SyncFragmentPose();

    if (self->teleportPending) {
        pongCreature_Teleport(creature, &self->teleportMatrix, self->teleportResetWorkers, true, false);
        ClearTeleportRequest(self);
        return;
    }

    KickWorkers(creature);
}

/**
 * pongCreature::UpdateAnimation @ 0x820C69A0 | size: 0x1C8
 * (was pongPlayer_69A0_g)
 *
 * Called by StepLocomotion and Teleport. Updates the player state and, while
 * it reports a swing (0x820CD550, 0x820CD598 or 0x820CD5F0) for a creature
 * with a player index and swing state, hands the swing target to the swing
 * state. Then runs 0x8214C8F8 on the skeleton and, when the look-at is
 * enabled and neither global blocks it, aims the look-at controller at the
 * player state's target twice (which 0 and 1).
 */
void pongCreature::UpdateAnimation() {
    pongCreatureLayout* self = CreatureLayout(this);
    pongPlayerStateView* state = self->state;
    pongCreatureSkeleton* skeleton = self->skeleton;

    if (state != nullptr) {
        pongPlayer_D228_g(state);

        if (self->swingState != nullptr && self->playerIndex >= 0 &&
            !reinterpret_cast<const pongPlayerState*>(self->state)->IsCreatureStateReady()) {
            pongPlayerStateView* current = self->state;
            if (pongPlayer_D550_g(current) || pongPlayer_D598_g(current) || pongPlayer_D5F0_g(current)) {
                const bool flag = pongPlayer_D5F0_g(current);
                float target[4];
                const float* aim = pongPlayer_D7B0_g(target, current);
                pongPlayer_B208_g(self->swingState, aim, flag);
            }
        }

        // The asm tests ReplayData()->field_68CF0 == 0 && playerIndex >= 0
        // here, but both outcomes run the code below (duplicated tails).
    }

    LocomotionStateAnim_C8F8_g(skeleton);

    if (self->lookAtEnabled && lbl_825C9F3C[1] == 0 && lbl_82606325 == 0) {
        const float* target = self->state->lookAtTarget;  // not null-checked here in the asm either
        game_2950(self->lookAt);
        game_28F0(self->lookAt, target, 0);
        game_2A40(self->lookAt);
        game_28F0(self->lookAt, target, 1);
    }
}

/**
 * pongCreature::SyncFragmentPose @ 0x820C6B68 | size: 0x18C
 * (was pongCreature_6B68_g)
 *
 * Copies the skeleton's pose into the fragment cache entry's skeleton (the
 * leading 4x4 of every bone record when the fragType's flag asks for it,
 * otherwise all bone matrices in one memcpy), has the instance sync its bone
 * matrices (fragInst slot 47) and gives the archetype's bound the instance's
 * matrix when the bound's slot 2 says so. Does nothing without the character's
 * +0x18 object.
 */
void pongCreature::SyncFragmentPose() {
    pongCreatureLayout* self = CreatureLayout(this);
    if (self->character == nullptr || self->character->field18 == nullptr)
        return;

    pongCreatureInstLayout* inst = Layout(self->inst);
    pongCreatureSkeleton* source = self->skeleton;
    pongCreatureSkeleton* target = inst->cacheEntry->skeleton;
    const fragType* type = inst->ResolvedType();
    if (type != nullptr && (reinterpret_cast<const fragTypeFlagsView*>(type)->flags1AF & 0x4) != 0) {
        for (int i = 0; i < source->data->boneCount; ++i) {
            memcpy(target->bones + i * BONE_RECORD_SIZE, source->bones + i * BONE_RECORD_SIZE,
                   sizeof(pongCreatureMatrix));
        }
    } else {
        memcpy(target->boneMatrices, source->boneMatrices,
               static_cast<size_t>(source->data->boneCount) * sizeof(pongCreatureMatrix));
    }

    VCALL(self->inst, 47, void (*)(pongCreatureInst*))(self->inst);  // SyncBoneMatrices

    phBoundView* bound = Layout(self->inst)->archetype->bound;
    if (bound->vfn_2())
        bound->vfn_3(Layout(self->inst)->matrix);
}

// Only virtual dispatch lives in this view; fields use the existing instance
// layout. No destructor: the original has one deleting slot, not an ABI pair.
struct pongCreatureTeleportInstance {
    virtual void slot0();
    virtual void slot1();
    virtual void slot2();
    virtual void SetLastMatrix(const pongCreatureMatrix* matrix); // slot 3
    virtual void slot4();
    virtual void slot5();
    virtual void slot6();
    virtual void slot7();
    virtual void slot8();
    virtual void slot9();
    virtual void slot10();
    virtual void slot11();
    virtual void slot12();
    virtual void slot13();
    virtual void slot14();
    virtual void slot15();
    virtual void slot16();
    virtual void slot17();
    virtual void slot18();
    virtual void slot19();
    virtual void slot20();
    virtual void slot21();
    virtual void slot22();
    virtual void slot23();
    virtual void slot24();
    virtual void slot25();
    virtual void slot26();
    virtual void slot27();
    virtual void slot28();
    virtual void slot29();
    virtual void slot30();
    virtual void slot31();
    virtual void slot32();
    virtual void slot33();
    virtual void slot34();
    virtual void slot35();
    virtual void slot36();
    virtual void slot37();
    virtual void slot38();
    virtual void slot39();
    virtual void slot40();
    virtual void slot41();
    virtual void slot42();
    virtual void slot43();
    virtual void slot44();
    virtual void slot45();
    virtual void slot46();
    virtual void SyncBoneMatrices(); // slot 47
};

// Copy the world matrix, update the owning creature's pose, and notify physics.
// pongCreatureInst_ApplyTeleportMatrix (was pongCreature_8FA8_g) @ 0x820C8FA8 | size: 0xE8
void pongCreatureInst_ApplyTeleportMatrix(pongCreatureInst* inst, const pongCreatureMatrix* matrix) {
    auto* bytes = reinterpret_cast<uint8_t*>(inst);
    const auto* source = reinterpret_cast<const uint8_t*>(matrix);
    for (unsigned row = 0; row < 4; ++row)
        memcpy(bytes + 0x10 + row * 16, source + row * 16, 16);
    auto* owner = *reinterpret_cast<pongCreature**>(bytes + 0xD0);
    LocomotionStateAnim_C8F8_g(CreatureLayout(owner)->skeleton);
    auto* dispatch = reinterpret_cast<pongCreatureTeleportInstance*>(inst);
    dispatch->SetLastMatrix(matrix);
    owner = *reinterpret_cast<pongCreature**>(bytes + 0xD0);
    owner->SyncFragmentPose();
    dispatch->SyncBoneMatrices();
    const uint16_t index = *reinterpret_cast<const uint16_t*>(bytes + 8);
    if (index != 0xFFFF)
        g_pPhysicsLevel->UpdateObjectLocation(index);
}

extern void pongCreatureWorker_Reset(pongCreatureWorker* worker, pongCreatureSkeleton* skeleton); // @ 0x820FAB78
extern "C" uint8_t* g_large_buffer_ptr; // @ 0x8260637C

struct pongCreatureTeleportSignals {
    uint8_t _pad0000[0x1814];
    rage::ptr32<rage::ptr32<uint8_t>> entries; // +0x1814
    uint16_t count; // +0x1818
    uint8_t _pad181A[2];
    rage::ptr32<uint8_t> secondary; // +0x181C
};

static_assert(offsetof(pongCreatureTeleportSignals, count) == 0x1818);
static_assert(offsetof(pongCreatureTeleportSignals, secondary) == 0x181C);

// Apply a requested teleport and invalidate animation/physics caches.
// pongCreature_Teleport @ 0x820C7A28 | size: 0x24C
void pongCreature_Teleport(pongCreature* creature, const pongCreatureMatrix* matrix,
                           bool resetWorkers, bool updatePoseFirst, bool keepInstanceMatrix) {
    auto* self = CreatureLayout(creature);
    rage_DebugLogNop("pongCreature::Teleport() - teleporting player[%d] to [%f,%f,%f]",
                     self->playerIndex, double(matrix->d[0]), double(matrix->d[1]), double(matrix->d[2]));
    pongCreatureWorker* workers[2] = {self->character->data->workers[0], self->character->data->workers[1]};
    const bool haveWorkers = workers[0] || workers[1];
    if (resetWorkers && haveWorkers && updatePoseFirst)
        creature->UpdateAnimation();
    if (!keepInstanceMatrix)
        pongCreatureInst_ApplyTeleportMatrix(self->inst, matrix);
    if (resetWorkers && haveWorkers) {
        // Copy both poses before either worker reset can change them.
        for (auto* worker : workers) {
            if (!worker) continue;
            auto* pose = static_cast<uint8_t*>(worker->field24);
            const auto* root = *reinterpret_cast<const uint8_t* const*>(pose);
            for (unsigned row = 0; row < 4; ++row)
                memcpy(pose + 0xB0 + row * 16, root + 0x10 + row * 16, 16);
            memcpy(pose + 0xF0, pose + 0xE0, 16);
        }
        for (auto* worker : workers)
            if (worker) pongCreatureWorker_Reset(worker, self->skeleton);
    }
    const auto* table = reinterpret_cast<const uint32_t*>(g_plrPlayerMgr_state.get());
    const uint32_t entry = table[uint32_t(self->playerIndex) + 33];
    auto* signals = rage::load_ptr32<pongCreatureTeleportSignals>(table, uint32_t(entry + 29) * 4u);
    for (unsigned i = 0; i < signals->count; ++i)
        signals->entries.get()[i].get()[0x3E] = 1;
    if (signals->secondary)
        signals->secondary.get()[0xA4] = 1;
    g_large_buffer_ptr[g_phFrameIndex + 0x91] = 1;
}

/**
 * pongCreature::RequestTeleport @ 0x820C7CE8 | size: 0xCC
 * (was pongCreature_7CE8_g, and pongCreature_ApplyMatrix in pongMover::Reset)
 *
 * Logs "Function calling Teleport is %s (player %d)%s". Immediately: teleports
 * now (with updatePoseFirst set) and returns. Otherwise stores the request for
 * UpdateReplay or StepLocomotion; keepInstanceMatrix also sets the hold flag.
 */
void pongCreature::RequestTeleport(const char* caller, const pongCreatureMatrix* matrix,
                                   bool resetWorkers, bool immediately, bool keepInstanceMatrix) {
    pongCreatureLayout* self = CreatureLayout(this);
    rage_DebugLogNop("Function calling Teleport is %s (player %d)%s", caller, self->playerIndex,
                     immediately ? " (IMMEDIATELY)" : "(deferred)");

    if (immediately) {
        pongCreature_Teleport(this, matrix, resetWorkers, true, false);
        return;
    }

    self->teleportPending = 1;
    self->teleportMatrix = *matrix;
    self->teleportResetWorkers = resetWorkers;
    self->teleportKeepInstanceMatrix = keepInstanceMatrix;
    self->teleportHoldFrame = keepInstanceMatrix;
}



// ═════════════════════════════════════════════════════════════════════════════
// Stub implementations — lifted from stubs.cpp into correct partition
// ═════════════════════════════════════════════════════════════════════════════

// External helpers
// @ 0x822C9D98 — phArchetype release: does nothing (returns 1) while the byte at
// 0x826064E1 is clear; otherwise drops the u16 refcount at +0x1A and, when it
// reaches zero, calls slot 0 with flags 1 (deleteWhenUnused set) or slot 3.

/**
 * phInst::Cleanup @ 0x822C8FD0 | size: 0x5C
 *
 * rage::phInst's destructor body: sets the rage::phInst vtable, releases the
 * archetype at +4 (if any) through 0x822C9D98, nulls it, then sets the
 * rage::datBase vtable.
 *
 * Called from pongCreatureInst::FragInstDtor, pongBallInstance::~pongBallInstance,
 * phInst::~phInst, and phClothVerletInst::~phClothVerletInst.
 */
extern "C" void pongCreatureInst_Cleanup(void* obj) {
    uint8_t* self = (uint8_t*)obj;

    // Set vtable to rage::phInst @ 0x8205991C
    *(void**)self = (void*)0x8205991C;

    void* archetype = *(void**)(self + 4);
    if (archetype != nullptr)
        util_9D98(archetype, 1);

    *(void**)(self + 4) = nullptr;

    // Set vtable to rage::datBase @ 0x820276C4
    *(void**)self = (void*)0x820276C4;
}
