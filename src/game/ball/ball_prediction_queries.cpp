// Readback and diagnostics shared by hit prediction and rigid-body playback.
#include "ball_predict.hpp"

namespace {
struct Collider {
    uint8_t _pad00[0xE0];
    bpVec4 velocity;
    bpVec4 angularVelocity;
};
struct Level {
    virtual void Slot0() = 0;
    virtual void Slot1() = 0;
    virtual void Slot2() = 0;
    virtual void Slot3() = 0;
    virtual Collider* GetActiveCollider(uint16_t handle) = 0;
    uint8_t _pad04[0x18];
    uint8_t* states;
};
struct Simulator { void* vtable; Level* level; };
struct Instance { void* vtable; void* archetype; uint16_t levelIndex; };
}

extern void* g_pPhysicsSim;                     // @ 0x825F5BD0
extern void** g_ppBallInst;                     // @ 0x8271A2F4
extern void nop_8240E6D0(const char* format, ...); // @ 0x8240E6D0

// @ 0x821D8C70
int BallPredict_GetInitialVelocities(gdBallPredictData* prediction, bpVec4* velocity, bpVec4* spin) {
    if (prediction->m_count > 1) {
        const gdBallPredictSample& sample = prediction->At(1);
        *velocity = sample.vel;
        *spin = sample.angVel;
        return 1;
    }
    auto* sim = static_cast<Simulator*>(g_pPhysicsSim);
    const uint16_t handle = static_cast<Instance*>(*g_ppBallInst)->levelIndex;
    if ((sim->level->states[handle] & 7) == 0) {
        Collider* collider = sim->level->GetActiveCollider(handle);
        if (collider != nullptr) {
            *velocity = collider->velocity;
            *spin = collider->angularVelocity;
            return 1;
        }
    }
    return 0;
}

// @ 0x821D9238
void BallPredict_Dump(gdBallPredictData* prediction) {
    int local = 0, other = 0;
    for (int i = 0; i < prediction->m_bounceCount; ++i) {
        if (prediction->m_bounces[i].onLocalSide != 0) ++local;
        else ++other;
    }
    nop_8240E6D0("num table bounces accumulated <%d,%d>", local, other);
    prediction->CountBouncesSoFar(&local, &other);
    nop_8240E6D0("num table bounces expired <%d,%d>", local, other);
}
