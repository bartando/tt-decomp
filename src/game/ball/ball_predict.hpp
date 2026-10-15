// ball_predict.hpp — gdBallPredictData, the ball trajectory predictor
// Rockstar Presents Table Tennis (Xbox 360, 2006)
//
// After every hit, ballPredict::ProcessHit (0x82287B50) re-simulates the ball's flight
// (gravity, quadratic drag, Magnus lift, table/net contacts) into a ring of up to 120
// samples. Players and the AI pick their hit point from it; samples are popped as game
// time passes them. The game state keeps two of these (+0x10 and +0x14) and swaps them
// when a new shot is planned.
#pragma once

#include <cstdint>

struct alignas(16) bpVec4 {
    float x, y, z, w;
};

// One predicted ball state, 0x50 bytes. Bytes 0x0B..0x0F are padding: the game's
// assignment (0x820D6E58) leaves them alone.
struct gdBallPredictSample {
    float   time;        // +0x00  game time of this state
    float   time2;       // +0x04  second clock, moves with time
    uint8_t bounced;     // +0x08  this step ended in a contact
    uint8_t flag9;       // +0x09  carried through by the stepper
    uint8_t hittable;    // +0x0A  inside a player's hit window
    uint8_t _pad0B[5];
    bpVec4  pos;         // +0x10
    bpVec4  vel;         // +0x20
    bpVec4  angVel;      // +0x30
    bpVec4  orient;      // +0x40  quaternion, (0, 0, 0, 1) at launch

    gdBallPredictSample& operator=(const gdBallPredictSample& o);
};
static_assert(sizeof(gdBallPredictSample) == 0x50, "gdBallPredictSample is 0x50 bytes");

// A bound callback (16 bytes); the empty one is the zero template at 0x8261A0C0.
struct bpFunctor {
    uint32_t words[4];
};

struct gdBallPredictData {
    static constexpr int kMaxSamples = 120;

    bpVec4              m_hitVel;                  // +0x0000  (cleared by Reset)
    bpVec4              m_hitPos;                  // +0x0010
    gdBallPredictSample m_samples[kMaxSamples];    // +0x0020
    int32_t             m_head;                    // +0x25A0  slot of the newest sample
    int32_t             m_tail;                    // +0x25A4  slot before the oldest sample
    int32_t             m_count;                   // +0x25A8
    uint8_t             _pad25AC[0x2600 - 0x25AC];
    uint8_t             m_complete;                // +0x2600  the simulation ran to its end
    uint8_t             _pad2601[3];
    float               m_timeLimit;               // +0x2604  < 0: none
    uint32_t*           m_ids;                     // +0x2608  atArray<u32>
    uint16_t            m_idCount;                 // +0x260C
    uint16_t            m_idCapacity;              // +0x260E
    float               m_idTime;                  // +0x2610
    uint8_t             _pad2614[0x2630 - 0x2614];
    uint8_t             m_shot[0xB8];              // +0x2630  the shot this prediction was made for
    uint8_t             _pad26E8[0x27E0 - 0x26E8];
    uint32_t            m_27E0;                    // +0x27E0
    uint8_t             m_27E4;                    // +0x27E4
    uint8_t             _pad27E5[3];
    bpFunctor           m_onPop;                   // +0x27E8  called with each popped sample

    // Sample i counted from the oldest.
    gdBallPredictSample& At(int i) { return m_samples[(m_tail + i + 1) % kMaxSamples]; }

    void  Reset(const char* caller);
    int   PopElapsed(bool recordReplay);
    void  AddSample(const gdBallPredictSample* s);
    void  AppendRepeatOfLast();
    gdBallPredictSample* FindNearestHittableSample(const gdBallPredictSample* target, int* outIndex);
    int   FindLastBounceAtOrBefore(int index);
    int   FindFirstHittable();
    int   FindFirstUnhittableFrom(int index);
};
#if UINTPTR_MAX == 0xFFFFFFFFu
static_assert(__builtin_offsetof(gdBallPredictData, m_head) == 0x25A0, "gdBallPredictData layout");
static_assert(__builtin_offsetof(gdBallPredictData, m_onPop) == 0x27E8, "gdBallPredictData layout");
#endif

// Per-player shot tuning (0x1A0 bytes each, two at 0x8261A3D0); only the field the
// flight model reads is named.
struct bpShotParams {
    uint8_t _pad00[0xCC];
    int32_t spinType;     // +0xCC  10 drags harder (0.011 instead of 0.010)
};

namespace ballPredict {
// Acceleration of a ball moving at vel with spin angVel: Magnus + drag + gravity.
void ComputeAccel(bpVec4* out, const bpShotParams* params, const bpVec4* vel, const bpVec4* angVel);
}
