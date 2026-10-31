// Hittable windows, late exits and the bounded outcome forecast.
#include "ball_predict.hpp"
#include <stdint.h>

extern void* g_game_state_ptr;                   // @ 0x8271A2F8
extern void* g_pTableDims;                       // @ 0x8271A304
extern void** g_ppBallInst;                      // @ 0x8271A2F4
extern "C" float g_ballRecoveryHalfWidth;       // @ 0x825C7554
extern "C" float g_ballRecoveryHalfLength;      // @ 0x825C7558
extern void BallPredict_StepSample(gdBallPredictSample* sample, int bank); // @ 0x82288368
extern void nop_8240E6D0(const char* format, ...); // @ 0x8240E6D0

namespace {
struct State { uint8_t _pad00[0x14]; gdBallPredictData* prediction; };
struct Table { uint8_t _pad00[0x14]; float height; };
struct Bound { uint8_t _pad00[8]; float radius; };
struct Archetype { uint8_t _pad00[0xC]; Bound* bound; };
struct Instance { void* vtable; Archetype* archetype; };

float Radius() {
    auto* ball = static_cast<Instance*>(*g_ppBallInst);
    return ball ? ball->archetype->bound->radius : 0.0f;
}
}

// @ 0x821D38E8
void BallPredict_MarkHittableWindow(void* statePtr, int /*unusedBank*/, int from,
                                   int count, int /*unusedFlag*/) {
    auto* state = static_cast<State*>(statePtr);
    gdBallPredictData* data = state->prediction;
    // The leading run of contact samples is skipped before checking `count`.
    // Callers guarantee a later non-contact slot, even for an exhausted range.
    while (data->At(from).bounced != 0) ++from;
    for (int i = from; i < count; ++i) {
        gdBallPredictSample& sample = state->prediction->At(i);
        if (sample.pos.y <= Radius() || sample.bounced != 0) break;
        sample.hittable = 1;
    }
}

// @ 0x8228A4E8
void BallPredict_MarkLateTableExit(int /*unusedBank*/, void* idsArray, int from) {
    gdBallPredictData* data = static_cast<State*>(g_game_state_ptr)->prediction;
    const int count = data->m_count;
    const float threshold = static_cast<Table*>(g_pTableDims)->height + Radius();
    int i = from;
    for (; i < count; ++i) {
        if (data->At(i).pos.y <= threshold) break;
    }
    if (i >= count || i <= 0 || from + 2 >= i) return;
    const gdBallPredictSample& sample = data->At(i);
    if (sample.hittable == 0 || sample.bounced != 0) return;
    if (__builtin_fabsf(sample.pos.x) < g_ballRecoveryHalfWidth &&
        __builtin_fabsf(sample.pos.z) < g_ballRecoveryHalfLength) {
        auto** ids = static_cast<uint32_t**>(idsArray);
        (*ids)[0] |= 16;
    }
}

// @ 0x82280358
uint32_t BallPredict_IsFiniteXYZ(const bpVec4* vector) {
    const float* lanes = &vector->x;
    for (int i = 0; i < 3; ++i) {
        uint32_t bits;
        __builtin_memcpy(&bits, lanes + i, 4);
        if ((bits & 0x7F800000u) == 0x7F800000u) return 0;
    }
    return 1;
}

// @ 0x8228A688
void BallPredict_ForecastOutcome(gdBallPredictSample* sample, int* result, int /*unusedBank*/) {
    *result = 0;
    const float floor = static_cast<Table*>(g_pTableDims)->height - Radius();
    int steps = 0;
    for (;;) {
        if (static_cast<uint8_t>(BallPredict_IsFiniteXYZ(&sample->pos)) == 0 ||
            static_cast<uint8_t>(BallPredict_IsFiniteXYZ(&sample->vel)) == 0) {
            nop_8240E6D0("Invalid sample found while extrapolating next event.  See output for details.");
            break;
        }
        if (sample->bounced != 0) *result = sample->pos.z < 0.0f ? 2 : 1;
        if (sample->pos.y < floor && sample->vel.y < 0.0f) {
            *result = 3;
            break;
        }
        if (*result != 0) break;
        ++steps;
        BallPredict_StepSample(sample, 1);
        if (*result != 0) break;
        if (steps >= gdBallPredictData::kMaxSamples) break;
    }
    if (steps >= gdBallPredictData::kMaxSamples) {
        nop_8240E6D0("Could not extrapolate a ball event after computing %d extra samples!", gdBallPredictData::kMaxSamples);
    }
}
