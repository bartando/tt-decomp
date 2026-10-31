// Playback of the predicted flight and its table/net/player crossing messages.
#include "ball_predict.hpp"
#include "pong_ball.hpp"
#include "ball_visual_spin.hpp"
#include "ball_audio.hpp"
#include <cstdint>
#include <cmath>

namespace ballPlayback {
struct Matrix { bpVec4 a, b, c, d; };
struct Velocity { float x, y, z; };
struct Archetype {
    virtual void Slot0() = 0;
    virtual void Slot1() = 0;
    virtual void Slot2() = 0;
    virtual void Slot3() = 0;
    virtual void Slot4() = 0;
    virtual void Slot5() = 0;
    virtual void Slot6() = 0;
    virtual float GetMass() = 0;
    uint8_t _pad04[8];
    struct Bound { uint8_t _pad00[8]; float radius; }* bound; // +0x0C
};
struct Instance {
    virtual void Slot0() = 0;
    virtual void Slot1() = 0;
    virtual void Slot2() = 0;
    virtual void Slot3() = 0;
    virtual void GetVelocity(Velocity* out) = 0;
    Archetype* archetype;          // +0x04
    uint16_t levelIndex;           // +0x08
    uint8_t _pad0A[6];
    Matrix matrix;                // +0x10
    uint8_t _pad50[8];
    void* audio;                   // +0x58
    uint8_t _pad5C[4];
    Matrix previousMatrix;        // +0x60
    bpVec4 angularVelocity;       // +0xA0
    bpVec4 previousAngularVelocity; // +0xB0
};
struct Level {
    virtual void Slot0() = 0;
    virtual void Slot1() = 0;
    virtual void Slot2() = 0;
    virtual void Slot3() = 0;
    virtual void Slot4() = 0;
    virtual void Slot5() = 0;
    virtual void Slot6() = 0;
    virtual void Slot7() = 0;
    virtual void Slot8() = 0;
    virtual void Slot9() = 0;
    virtual void Slot10() = 0;
    virtual void UpdateTransform(uint16_t handle) = 0;
};
struct State {
    uint8_t _pad00[4];
    float previousWindow, blendDuration, hitTime;
    gdBallPredictData* prediction[2]; // +0x10/+0x14
    uint8_t _pad18[0x14];
    int32_t localBounces;          // +0x2C
    int32_t otherBounces;          // +0x30
};
struct Timing { uint8_t _pad00[0x30]; float now, previous; };
struct Table { uint8_t _pad00[0x10]; bpVec4 dimensions; };
struct Input {
    uint8_t _pad00[0x40];
    uint8_t localSide;
    uint8_t _pad41[3];
    struct Player { uint8_t _pad00[0x38]; float courtZ; }* players[2];
};
}

extern void* g_game_state_ptr;                  // @ 0x8271A2F8
extern void* g_pongMatchTiming;                 // @ 0x8271A2E8
extern void* g_pTableDims;                          // @ 0x8271A304
extern void* g_input_obj_ptr;                   // @ 0x825EAB28
extern void** g_ppBallInst;                     // @ 0x8271A2F4
extern void* g_pPhysicsLevel;                    // @ 0x826065E4
extern void* g_pPhysicsSim;                      // @ 0x825F5BD0
extern gmBallNode* g_activeBallNode;             // @ 0x82606570
extern const float g_kTransitionStep;              // @ 0x825CAEC0
extern const float g_lookAtMultiplier;           // @ 0x8202D184
extern "C" const float g_kFloatConst_D110;        // @ 0x8202D110
extern "C" const float g_kFloatConst_D108;        // @ 0x8202D108
extern "C" const float g_kFloatConst_D10C;        // @ 0x8202D10C
extern uint8_t g_typeDescriptor_phInst[];         // @ 0x825D2CB8
extern uint8_t g_typeDescriptor_pongBallInstance[]; // @ 0x825D2CD4
extern "C" void* RTDynamicCast(void*, int, const void*, const void*, int); // @ 0x82430978
extern uint32_t BallPredict_HasFlag9Crossing(gdBallPredictData* data); // @ 0x821D7D90
extern uint32_t BallPredict_ShouldUsePrevious(void* state); // @ 0x821D3390
extern void BallPredict_InterpolateSamples(void* ring, void* unusedR4, gdBallPredictSample* out, float time); // @ 0x821D95A8
extern void BallPredict_InterpolateState(void* state, void* unusedR4, gdBallPredictSample* out, float time); // @ 0x821D3C60
extern void BallPredict_AdvanceSamples(int bank, bool recordReplay); // @ 0x82287930
extern bool BallPhysics_QueueInactive(void* sim, uint16_t handle); // @ 0x822C1B98
extern void nop_8240E6D0(const char* format, ...); // @ 0x8240E6D0
extern void pg_E6E0(int message, int mask, int count, int args); // @ 0x8225E6E0

// @ 0x821D3390
// Previously called pongLerpQueue_CheckTimeWindow; the receiver is game state,
// and the clock/tolerance come from it, not floating-point arguments.
uint32_t BallPredict_ShouldUsePrevious(void* gameState) {
    auto* state = static_cast<ballPlayback::State*>(gameState);
    const auto* prediction = state->prediction[1];
    if (prediction->m_count <= 1) return false;
    const float sampleTime = prediction->m_samples[(prediction->m_tail + 2) % 120].time;
    return sampleTime - state->hitTime < state->previousWindow;
}

// @ 0x822870C8
void pg_70C8_g() {
    using namespace ballPlayback;
    auto* state = static_cast<State*>(g_game_state_ptr);
    gdBallPredictData* prediction = state->prediction[1];
    int local, other;
    prediction->CountBouncesSoFar(&local, &other);
    bool bounce = false;
    bool localBounce = false;
    if (local > state->localBounces) {
        bounce = true;
        localBounce = true;
    } else if (other > state->otherBounces) {
        bounce = true;
    }
    const bool flag9 = static_cast<uint8_t>(BallPredict_HasFlag9Crossing(prediction)) != 0;
    bool descending = false, belowTable = false, passedTable = false, passedNet = false, passedPlayer = false;
    int playerSide = -1;
    const float zero = g_kFloatConst_D110;
    const float one = g_kFloatConst_D108;
    if (prediction->m_count > 1 &&
        prediction->At(0).time < static_cast<Timing*>(g_pongMatchTiming)->previous) {
        auto* published = static_cast<Instance*>(*g_ppBallInst);
        const bpVec4 dimensions = static_cast<Table*>(g_pTableDims)->dimensions;
        const float radius = published ? published->archetype->bound->radius : zero;
        const float halfLength = __builtin_fmaf(dimensions.z, g_kFloatConst_D10C, radius);
        const float height = dimensions.y - radius;
        gdBallPredictSample previous;
        previous.time = previous.time2 = zero;
        previous.bounced = previous.flag9 = previous.hittable = 0;
        previous.pos = previous.vel = previous.angVel = bpVec4{zero, zero, zero, zero};
        previous.orient = bpVec4{zero, zero, zero, one};
        BallPredict_InterpolateSamples(prediction->m_samples, nullptr, &previous,
                                      static_cast<Timing*>(g_pongMatchTiming)->previous);
        gdBallPredictSample current;
        const gdBallPredictSample& tail = prediction->At(prediction->m_count - 1);
        current.time = tail.time;
        current.time2 = tail.time2;
        current.bounced = tail.bounced;
        current.flag9 = tail.flag9;
        current.hittable = tail.hittable;
        current.pos = tail.pos;
        current.vel = tail.vel;
        current.angVel = tail.angVel;
        current.orient = tail.orient;
        const float now = static_cast<Timing*>(g_pongMatchTiming)->now;
        if (prediction->At(prediction->m_count - 1).time >= now) {
            BallPredict_InterpolateSamples(prediction->m_samples, nullptr, &current, now);
        }
        descending = previous.vel.y > zero && current.vel.y <= zero;
        belowTable = __builtin_fabsf(previous.pos.y) >= height && __builtin_fabsf(current.pos.y) < height;
        passedTable = __builtin_fabsf(previous.pos.z) < halfLength && __builtin_fabsf(current.pos.z) >= halfLength;
        published = static_cast<Instance*>(*g_ppBallInst);
        const float crossingRadius = published ? published->archetype->bound->radius : zero;
        passedNet = previous.pos.y > crossingRadius && current.pos.y <= crossingRadius;
        auto* input = static_cast<Input*>(g_input_obj_ptr);
        playerSide = static_cast<uint8_t>(current.pos.z > zero) != input->localSide;
        const float playerZ = input->players[playerSide]->courtZ;
        const float threshold = __builtin_fabsf(playerZ) + one;
        passedPlayer = __builtin_fabsf(previous.pos.z) < threshold && __builtin_fabsf(current.pos.z) >= threshold;
        state = static_cast<State*>(g_game_state_ptr);
    }
    if (prediction->m_count > 1) {
        if (static_cast<uint8_t>(BallPredict_ShouldUsePrevious(state)) != 0) {
            BallPredict_AdvanceSamples(1, true);
            BallPredict_AdvanceSamples(0, false);
        } else {
            BallPredict_AdvanceSamples(1, true);
        }
    }
    auto* instance = static_cast<Instance*>(RTDynamicCast(*g_ppBallInst, 0,
        g_typeDescriptor_phInst, g_typeDescriptor_pongBallInstance, 0));
    if (prediction->m_count > 1) {
        gdBallPredictSample sample;
        sample.time = sample.time2 = zero;
        sample.bounced = sample.flag9 = sample.hittable = 0;
        sample.pos = sample.vel = sample.angVel = bpVec4{zero, zero, zero, zero};
        sample.orient = bpVec4{zero, zero, zero, one};
        BallPredict_InterpolateState(g_game_state_ptr, nullptr, &sample,
                                    static_cast<Timing*>(g_pongMatchTiming)->now);
        const bpVec4 spin = sample.angVel;
        instance->previousAngularVelocity = instance->angularVelocity;
        instance->angularVelocity = spin;
        Matrix matrix = instance->matrix;
        matrix.d = sample.pos;
        BallNode_IntegrateVisualSpin(g_activeBallNode, &instance->matrix.d.x, &spin.x, &matrix.a.x, g_kTransitionStep);
        instance->previousMatrix = instance->matrix;
        instance->matrix = matrix;
        static_cast<Level*>(g_pPhysicsLevel)->UpdateTransform(instance->levelIndex);
        if (prediction->m_count > 1) {
            BallPhysics_QueueInactive(g_pPhysicsSim, instance->levelIndex);
        }
    }
    Velocity velocity{zero, zero, zero};
    instance->GetVelocity(&velocity);
    if (descending) pg_E6E0(11, 0x40, 0, 0);
    const float impactScale = g_lookAtMultiplier;
    if (bounce) {
        nop_8240E6D0("Sending msgBall::kBounceTable%s now(%f)",
            localBounce ? "A" : "B",
            static_cast<Timing*>(g_pongMatchTiming)->now);
        pg_E6E0(localBounce ? 1 : 2, 0x40, 0, 0);
        const float vy = __builtin_fabsf(velocity.y);
        const float impulse = instance->archetype->GetMass() * vy;
        const float scaled = impulse * impactScale;
        BallAudio_PreImpact(instance->audio, nullptr, 2, &instance->matrix.d.x, 0, scaled * scaled);
    }
    if (flag9) {
        pg_E6E0(7, 0x40, 0, 0);
        const float vy = __builtin_fabsf(velocity.y);
        const float impulse = instance->archetype->GetMass() * vy;
        const float scaled = impulse * impactScale;
        BallAudio_PreImpact(instance->audio, nullptr, 3, &instance->matrix.d.x, 0, scaled * scaled);
    }
    if (passedTable) pg_E6E0(13, 0x40, 0, 0);
    if (belowTable) pg_E6E0(12, 0x40, 0, 0);
    if (passedNet) {
        pg_E6E0(10, 0x40, 0, 0);
        pg_E6E0(44, 0x40, 0, 0);
    }
    if (passedPlayer) pg_E6E0(14, (1u << playerSide) | 0x40, 0, 0);
}

namespace ballPlayback {
struct QueueLevel { uint8_t _pad00[0x1C]; uint8_t* states; };
struct QueueSimulator {
    void* vtable;
    QueueLevel* level;            // +0x04
    uint8_t _pad08[0x30];
    uint32_t count;               // +0x38
    uint16_t* handles;            // +0x3C
};
}

// @ 0x822C1B98
bool BallPhysics_QueueInactive(void* simulator, uint16_t handle) {
    auto* sim = static_cast<ballPlayback::QueueSimulator*>(simulator);
    if (sim->count >= 120 || (sim->level->states[handle] & 7) != 1) return false;
    sim->handles[sim->count] = handle;
    ++sim->count;
    return true;
}
