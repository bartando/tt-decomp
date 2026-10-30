// Swing input and court-bound position prediction, recovered from the PPC.
#include "pong_player.hpp"
#include "pong_gameplay_queries.hpp"

extern "C" void* g_input_obj_ptr; // @ 0x825EAB28
extern int io_Input_poll_9D68(void*); // @ 0x821C9D68
extern uint32_t pg_C7A0_g(pongAnimState*, float); // @ 0x820DC7A0
extern void game_AF18(vec3*, void*, const vec3*, const vec3*, const vec3*); // @ 0x820CAF18

namespace {
template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}

// Match VMX's default non-Java mode: flush subnormal operands/results,
// preserving the sign of zero (the scalar FPU does not do this).
float flushVmx(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, sizeof(bits));
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
        __builtin_memcpy(&value, &bits, sizeof(value));
    }
    return value;
}
float mulVmx(float a, float b) {
    return flushVmx(flushVmx(a) * flushVmx(b));
}
float addVmx(float a, float b) {
    return flushVmx(flushVmx(a) + flushVmx(b));
}

// fsubs followed by fsel: unordered selects the lower bound. The upper
// subtraction is double precision (fsub), not another rounded fsubs.
float clampCourt(float value, float lower, float upper) {
    float delta = value - lower;
    float raised = delta >= 0.0f ? value : lower;
    return double(raised) - double(upper) >= 0.0 ? upper : raised;
}
}

// r4 is unused; outputs are r5/r6. Vector arithmetic writes all four lanes.
// @ 0x820D42E0 | size: 0x14C
extern "C" void pongPlayer_42E0_g(pongSwingData* swing, void*, float* strength,
                                  vec3* target, float alpha) {
    const double amount = -double(alpha) >= 0.0 ? 0.0 : double(alpha);
    if (swing->m_swingType == 0) {
        *strength = 0.0f;
    } else if (swing->m_swingType == 9) {
        void* source = swing->m_pStrengthSource;
        auto fn = reinterpret_cast<float (*)(void*)>((*static_cast<void***>(source))[10]);
        const double raw = fn(source);
        const double nonnegative = raw >= 0.0 ? raw : 0.0;
        *strength = nonnegative - amount >= 0.0 ? amount : nonnegative;
    } else {
        *strength = amount;
    }

    const float power = *strength;
    void* creature = swing->m_pCreature;
    const vec3 origin = at<vec3>(at<void*>(creature, 0xA4), 0x40);
    // VMX multiplies round separately from the vector add.
    const vec3 scaled = {mulVmx(mulVmx(swing->m_baseDirection[0], 0.5f), power),
                         mulVmx(mulVmx(swing->m_baseDirection[1], 0.5f), power),
                         mulVmx(mulVmx(swing->m_baseDirection[2], 0.5f), power),
                         mulVmx(mulVmx(swing->m_baseDirection[3], 0.5f), power)};
    *target = {addVmx(origin.x, scaled.x), addVmx(origin.y, scaled.y),
               addVmx(origin.z, scaled.z), addVmx(origin._pad, scaled._pad)};
    vec3 lower, upper;
    pongMatchSettings_GetCourtBounds(g_input_obj_ptr, at<int32_t>(creature, 0xCC), &lower, &upper);
    target->x = clampCourt(target->x, lower.x, upper.x);
    target->z = clampCourt(target->z, lower.z, upper.z);
}

// @ 0x820C73E8 | size: 0x144
extern "C" uint32_t pongPlayer_73E8_g(pongPlayer* player, float inputValue) {
    if (!player->m_pPlayerState->CanAcceptSwingInput()) return 0;
    float strength = 0.0f;
    if (static_cast<uint8_t>(io_Input_poll_9D68(g_input_obj_ptr)) == 0) {
        pongPlayerState* state = player->m_pPlayerState;
        pongSwingData* swing = state->m_pSwingData;
        vec3 target = {};
        pongPlayer_42E0_g(swing, state, &strength, &target, 0.1f);
        swing->m_swingStrength = strength;
        swing->m_bTriggered = 1;
        __builtin_memcpy(swing->m_swingVec, &target, sizeof(target));
    } else {
        void* owner = at<void*>(player->m_pPhysicsBound, 0x70);
        auto* otherState = at<pongPlayerState*>(owner, 0xBC);
        if (pongSwingData* swing = otherState->m_pSwingData) swing->m_bAlternateTriggered = 1;
    }
    pongPlayerState* state = player->m_pPlayerState;
    if (!state->CanAcceptSwingInput()) return 0;
    pongAnimState* animation = state->m_pAnimState;
    if (strength > 0.0f) {
        animation->m_swingPhase = strength;
        return 1;
    }
    return pg_C7A0_g(animation, inputValue);
}

// @ 0x820CAB48 | size: 0x130
extern "C" vec3* pongPlayer_AB48_g(void* out, void* bound) {
    auto* position = static_cast<vec3*>(out);
    void* owner = at<void*>(bound, 0x70);
    auto* state = at<pongPlayerState*>(owner, 0xBC);
    if (pongSwingData* swing = state->m_pSwingData) {
        *position = at<vec3>(at<void*>(swing->m_pCreature, 0xA4), 0x40);
    } else {
        const vec3 origin = at<vec3>(at<void*>(owner, 0xA4), 0x40);
        vec3 velocity = {at<float>(bound, 0x30), 0.0f, at<float>(bound, 0x34), 0.0f};
        vec3 zero = {};
        vec3 delta;
        game_AF18(&delta, bound, &velocity, &zero,
                  &at<vec3>(at<void*>(owner, 0xA4), 0x40));
        *position = {addVmx(origin.x, delta.x), addVmx(origin.y, delta.y),
                     addVmx(origin.z, delta.z), addVmx(origin._pad, delta._pad)};
    }
    vec3 lower, upper;
    pongMatchSettings_GetCourtBounds(g_input_obj_ptr, at<int32_t>(bound, 0x44), &lower, &upper);
    position->x = clampCourt(position->x, lower.x, upper.x);
    position->z = clampCourt(position->z, lower.z, upper.z);
    return position;
}
