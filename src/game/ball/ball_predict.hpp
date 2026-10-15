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

// A predicted table contact.
struct bpBounceEvent {
    float   time;
    uint8_t onLocalSide;  // +0x04  the contact is on the side the local player's flag names
    uint8_t _pad05[3];
};

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
    uint8_t             _pad26E8[0x2790 - 0x26E8];
    bpBounceEvent       m_bounces[10];             // +0x2790  no bounds check: an 11th lands on m_bounceCount
    int32_t             m_bounceCount;             // +0x27E0
    uint8_t             m_bouncesBuilt;            // +0x27E4
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
    int   FindNextBounce(int from);
    void  BuildBounceList(bool unused);
    void  ExtendBounceList(int lastN);
    void  CountBouncesSoFar(int* localSide, int* otherSide);
};
#if UINTPTR_MAX == 0xFFFFFFFFu
static_assert(__builtin_offsetof(gdBallPredictData, m_head) == 0x25A0, "gdBallPredictData layout");
static_assert(__builtin_offsetof(gdBallPredictData, m_onPop) == 0x27E8, "gdBallPredictData layout");
#endif

// The flight model the predictor steps (0x822832D0) is BallFlight_Acceleration in ball_flight.hpp.

// The shot a prediction was made for (0xB8 bytes); kept at gdBallPredictData+0x2630
// and compared to decide whether a new hit needs a new prediction. Field meanings
// aren't known yet.
struct bpShot {
    float    f00[3];      // +0x00
    uint32_t _pad0C;
    bpVec4   v10;         // +0x10
    int32_t  i20;         // +0x20
    uint32_t _pad24[3];
    bpVec4   v30[2];      // +0x30  compared as a pair (0x821D4F80)
    bpVec4   v50;         // +0x50
    bpVec4   v60;         // +0x60
    float    f70[6];      // +0x70
    int32_t  i88;         // +0x88
    int32_t  i8C;         // +0x8C
    bpVec4   v90;         // +0x90
    bpVec4   vA0;         // +0xA0
    uint16_t hB0;         // +0xB0
    uint16_t hB2;         // +0xB2
    uint8_t  bB4;         // +0xB4
    uint8_t  _padB5;
    uint16_t hB6;         // +0xB6  low 11 bits: shot id (0x82282A50); top 4 compared here
};

namespace ballPredict {
bool VecPairEqual(const bpVec4* a, const bpVec4* b);
bool ShotEqual(const bpShot* a, const bpShot* b);
}
