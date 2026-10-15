// ball_predict.cpp — gdBallPredictData, the ball trajectory predictor
// Rockstar Presents Table Tennis (Xbox 360, 2006)

#include "ball_predict.hpp"

#include <cmath>

extern void        rage_debugLog(const char* fmt, ...);                        // @ 0x8240E6D0
extern const char* pongPlayer_1510_g(void* obj, int arg);                      // @ 0x82391510
extern "C" void    sysCallback_Invoke(bpFunctor* fn, void* arg);               // @ 0x8225FFF8

// What the replay keeps of the ball per frame (0x30 bytes; +0x08 is never written).
struct bpReplayBall {
    float    time;
    float    time2;
    uint32_t _pad08[2];
    bpVec4   pos;
    bpVec4   angVel;
};
extern void gdReplayMgr_RecordBallSample(void* replay, bpReplayBall* s);        // @ 0x821CD0F8

extern double crt_sqrt(double x);                                              // @ 0x824301D0
extern double crt_tan(double x);                                               // @ 0x82432628

// The ball instance's physics object; slot 12 returns the gravity scale.
struct bpPhysView {
    void** vtable;
};
struct bpBallInstView {
    uint32_t    _pad00;
    bpPhysView* phys;     // +0x04
};
extern "C" bpBallInstView** g_ppBallInst;           // @ 0x8271A2F4

struct bpMatchTiming {
    uint8_t _pad00[0x30];
    float   now;          // +0x30
};

extern "C" bpMatchTiming* g_pongMatchTiming;       // @ 0x8271A2E8
extern "C" uint8_t*       g_pReplayStateData;      // @ 0x8271A2EC
extern "C" void*          g_pAtSingletonPtr;       // @ 0x8271A328
extern "C" const bpFunctor g_defaultData16;        // @ 0x8261A0C0

namespace {
// *(u32*)(replay + 0x68CF0) != 0 while the replay is playing back rather than recording.
constexpr uint32_t kReplayPlayingOffset = 0x68CF0;

float Dist2(const bpVec4& a, const bpVec4& b) {
    float dx = a.x - b.x;
    float dy = a.y - b.y;
    float dz = a.z - b.z;
    return dx * dx + dy * dy + dz * dz;
}
}

// @ 0x820D6E58
gdBallPredictSample& gdBallPredictSample::operator=(const gdBallPredictSample& o) {
    time = o.time;
    time2 = o.time2;
    bounced = o.bounced;
    flag9 = o.flag9;
    hittable = o.hittable;
    pos = o.pos;
    vel = o.vel;
    angVel = o.angVel;
    orient = o.orient;
    return *this;
}

// @ 0x821D7750
void gdBallPredictData::Reset(const char* caller) {
    rage_debugLog("%s called BallPredictData::Reset() %s", caller,
                  pongPlayer_1510_g(g_pAtSingletonPtr, 0));
    m_count = 0;
    m_tail = 0;
    m_head = 0;
    for (uint32_t i = 0; i < m_idCount; ++i) {
        m_ids[i] = 0;
    }
    m_idTime = -1.0f;
    m_complete = 0;
    m_timeLimit = -1.0f;
    m_hitVel = bpVec4{0.0f, 0.0f, 0.0f, 0.0f};
    m_onPop = g_defaultData16;
    m_27E0 = 0;
    m_27E4 = 0;
}

// Drops the samples game time has passed (keeping the newest one passed, so there is
// always one sample at or before now), reporting each to the replay and the callback.
// @ 0x821D7840
int gdBallPredictData::PopElapsed(bool recordReplay) {
    int popped = 0;
    while (m_count > 1) {
        if (!(g_pongMatchTiming->now >= At(1).time)) {
            break;
        }
        if (!(m_timeLimit < 0.0f) && At(0).time >= m_timeLimit) {
            break;
        }
        if (recordReplay && *reinterpret_cast<uint32_t*>(g_pReplayStateData + kReplayPlayingOffset) == 0) {
            bpReplayBall rec;
            rec.time = At(1).time;
            rec.time2 = At(1).time2;
            rec.pos = At(1).pos;
            rec.angVel = At(0).angVel;
            gdReplayMgr_RecordBallSample(g_pReplayStateData, &rec);
        }
        if (m_onPop.words[3] != 0) {
            sysCallback_Invoke(&m_onPop, &At(0));
        }
        ++m_tail;
        --m_count;
        if (m_tail == kMaxSamples) {
            m_tail = 0;
        }
        ++popped;
    }
    return popped;
}

// @ 0x821D7C10
void gdBallPredictData::AddSample(const gdBallPredictSample* s) {
    if (m_count == kMaxSamples) {
        return;
    }
    if (++m_head == kMaxSamples) {
        m_head = 0;
    }
    m_samples[m_head] = *s;
    ++m_count;
}

// Pads the prediction with a copy of the last sample one second later.
// @ 0x821D7C88
void gdBallPredictData::AppendRepeatOfLast() {
    const gdBallPredictSample& last = At(m_count - 1);
    gdBallPredictSample s;
    s.time = last.time + 1.0f;
    s.time2 = last.time2 + 1.0f;
    s.bounced = 0;
    s.flag9 = last.flag9;
    s.hittable = 0;
    s.pos = last.pos;
    s.vel = last.vel;
    s.angVel = last.angVel;
    s.orient = last.orient;
    m_complete = 0;
    AddSample(&s);
    m_complete = 1;
}

// @ 0x821D8298
gdBallPredictSample* gdBallPredictData::FindNearestHittableSample(const gdBallPredictSample* target,
                                                                  int* outIndex) {
    *outIndex = -1;
    int first = FindFirstHittable();
    if (first < 0) {
        rage_debugLog("gdBallPredictData::FindNearestHittableSample - Could not find a hittable samples!");
        return nullptr;
    }
    int last = FindFirstUnhittableFrom(first) - 1;
    if (last < 0) {
        last = m_count - 1;
    }

    int best = first;
    float bestDist = Dist2(At(first).pos, target->pos);
    for (int i = first + 1; i <= last; ++i) {
        float d = Dist2(At(i).pos, target->pos);
        if (d < bestDist) {
            bestDist = d;
            best = i;
        }
    }
    *outIndex = best;
    return &At(best);
}

// Walks back from index to the latest sample that ended in a contact; 0 if none after 0.
// @ 0x821D8920
int gdBallPredictData::FindLastBounceAtOrBefore(int index) {
    for (; index > 0; --index) {
        if (At(index).bounced) {
            return index;
        }
    }
    return index;
}

// @ 0x821D8990
int gdBallPredictData::FindFirstHittable() {
    for (int i = 0; i < m_count; ++i) {
        const gdBallPredictSample& s = At(i);
        if (s.hittable && !s.bounced) {
            return i;
        }
    }
    return -1;
}

// @ 0x821D8A30
int gdBallPredictData::FindFirstUnhittableFrom(int index) {
    for (int i = index; i < m_count; ++i) {
        const gdBallPredictSample& s = At(i);
        if (!(s.hittable && !s.bounced)) {
            return i;
        }
    }
    return -1;
}

namespace ballPredict {

// @ 0x822832D0
void ComputeAccel(bpVec4* out, const bpShotParams* params, const bpVec4* vel, const bpVec4* angVel) {
    const bpVec4 v = *vel;
    const bpVec4 w = *angVel;

    // Magnus: angVel x vel. The w lane follows the vector code (0 for finite input).
    bpVec4 a;
    a.x = v.z * w.y - v.y * w.z;
    a.y = v.x * w.z - v.z * w.x;
    a.z = v.y * w.x - v.x * w.y;
    a.w = v.w * w.w - v.w * w.w;
    *out = a;

    // No sideways lift once the ball travels more across the table than along it
    // (|vx| >= |vz| * tan 60 deg).
    float k = static_cast<float>(crt_tan(1.0471975430846214));
    if (std::fabs(vel->x) >= std::fabs(vel->z) * k) {
        out->x = 0.0f;
        out->z = 0.0f;
    }

    const float speed2 = vel->x * vel->x + vel->y * vel->y + vel->z * vel->z;
    const float kMagnus = 0.004f;
    a = *out;
    a.x *= kMagnus;
    a.y *= kMagnus;
    a.z *= kMagnus;
    a.w *= kMagnus;
    *out = a;

    // Quadratic drag: a -= v * |v| * c.
    if (speed2 > 1e-6f) {
        const float c = (params->spinType == 10) ? 0.011f : 0.01f;
        const float s = static_cast<float>(crt_sqrt(speed2)) * c;
        a = *out;
        a.x -= v.x * s;
        a.y -= v.y * s;
        a.z -= v.z * s;
        a.w -= v.w * s;
        *out = a;
    }

    bpPhysView* phys = (*g_ppBallInst)->phys;
    const float g = reinterpret_cast<float (*)(bpPhysView*)>(phys->vtable[12])(phys);
    a = *out;
    a.y += -9.8f * g;
    a.x += 0.0f * g;
    a.z += 0.0f * g;
    a.w += 0.0f * g;
    *out = a;
}

}  // namespace ballPredict
