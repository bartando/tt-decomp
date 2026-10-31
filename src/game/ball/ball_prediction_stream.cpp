// Prediction-ring maintenance during ball playback.
#pragma clang fp contract(off)
#include "ball_predict.hpp"
#include "pong_ball.hpp"

struct RTTITypeDescriptor;
extern RTTITypeDescriptor g_typeDescriptor_phInst;           // @ 0x825D2CB8
extern RTTITypeDescriptor g_typeDescriptor_pongBallInstance;  // @ 0x825D2CD4
extern "C" void* RTDynamicCast(void* object, int32_t vfDelta, RTTITypeDescriptor* sourceType,
                                RTTITypeDescriptor* targetType, int32_t isReference); // @ 0x82430978
extern void* g_game_state_ptr;                             // @ 0x8271A2F8
extern pongBallInstance** g_ppBallInst;                     // @ 0x8271A2F4
extern void rage_debugLog(const char* format, ...);          // @ 0x8240E6D0
extern void BallPredict_StepSample(gdBallPredictSample* sample, int bank); // @ 0x82288368

namespace {
struct PredictionState {
    uint8_t _pad00[0x10];
    gdBallPredictData* banks[2];  // +0x10 / +0x14
};

PredictionState* CurrentState() {
    return static_cast<PredictionState*>(g_game_state_ptr);
}

// Copy only the fields written by the game's inlined sample assignment.
void CopySample(gdBallPredictSample& out, const gdBallPredictSample& source) {
    out.time = source.time;
    out.time2 = source.time2;
    out.bounced = source.bounced;
    out.flag9 = source.flag9;
    out.hittable = source.hittable;
    out.pos = source.pos;
    out.vel = source.vel;
    out.angVel = source.angVel;
    out.orient = source.orient;
}
}

// @ 0x82287930
void BallPredict_AdvanceSamples(int bank, bool recordReplay) {
    const int popped = CurrentState()->banks[bank]->PopElapsed(recordReplay);
    PredictionState* state = CurrentState();
    if (popped > 0) {
        gdBallPredictData* data = state->banks[bank];
        const gdBallPredictSample& last = data->At(data->m_count - 1);
        if (data->m_timeLimit == last.time) {
            // Deliberately the live bank, even when advancing bank zero.
            gdBallPredictData* live = state->banks[1];
            if (live->m_count != gdBallPredictData::kMaxSamples) {
                live->AppendRepeatOfLast();
            }
        } else if (data->m_complete == 0) {
            gdBallPredictSample sample;
            CopySample(sample, last);
            for (int i = 0; i < popped; ++i) {
                BallPredict_StepSample(&sample, bank);
                state = CurrentState();
                state->banks[bank]->AddSample(&sample);
            }
        }
    }

    gdBallPredictData* data = state->banks[bank];
    if (data->m_count < 2) {
        auto* ball = static_cast<pongBallInstance*>(RTDynamicCast(
            *g_ppBallInst, 0, &g_typeDescriptor_phInst,
            &g_typeDescriptor_pongBallInstance, 0));
        rage_debugLog("Hit end of buffer -- activating ball");
        ball->ActivateBall(nullptr);
    } else {
        data->ExtendBounceList(popped);
    }
}

namespace {
struct PredictionTiming {
    uint8_t _pad00[0x30];
    float now;
    float previous;
};

struct PredictionRing {
    gdBallPredictSample samples[gdBallPredictData::kMaxSamples];
    int32_t head;
    int32_t tail;
    int32_t count;

    gdBallPredictSample& At(int i) {
        return samples[(tail + i + 1) % gdBallPredictData::kMaxSamples];
    }
};
}
extern "C" PredictionTiming* g_pongMatchTiming;              // @ 0x8271A2E8
extern "C" const float g_kFloatConst_D108;                   // @ 0x8202D108
extern "C" const float g_kFloatConst_D110;                   // @ 0x8202D110

// @ 0x821D7D90
uint32_t BallPredict_HasFlag9Crossing(gdBallPredictData* data) {
    if (data->m_count <= 1) return false;
    const float now = g_pongMatchTiming->now;
    const float previous = g_pongMatchTiming->previous;
    for (int i = 1; i < data->m_count; ++i) {
        const gdBallPredictSample& sample = data->At(i);
        if (now >= sample.time && previous < sample.time && sample.flag9 != 0) {
            return true;
        }
        if (!(now >= sample.time)) return false;
    }
    return false;
}

// @ 0x821D96A0
bool BallPredict_FindNeighborIndices(void* ringPtr, void* /*unusedR4*/, int* first,
                                    int* second, float* factor, float time) {
    auto* ring = static_cast<PredictionRing*>(ringPtr);
    const int count = ring->count;
    if (count == 0) {
        rage_debugLog("pongLerpQueue::FindNeighborIndices - queue is empty!");
        return false;
    }
    if (count < 2) {
        rage_debugLog("Lerp Queue GetCount<2");
        *first = 0;
        *second = 0;
        *factor = g_kFloatConst_D110;
        return true;
    }
    if (time < ring->At(0).time) {
        rage_debugLog("Lerp Queue t<GetMinT()");
        *first = 0;
        *second = 1;
        *factor = g_kFloatConst_D110;
        return true;
    }
    if (time > ring->At(count - 1).time) {
        rage_debugLog("Lerp Queue t>GetMaxT()");
        *first = ring->count - 2;
        *second = ring->count - 1;
        *factor = g_kFloatConst_D108;
        return true;
    }
    for (int i = 0; i < count - 1; ++i) {
        if (ring->At(i).time <= time && ring->At(i + 1).time >= time) {
            const float duration = ring->At(i + 1).time - ring->At(i).time;
            if (duration > g_kFloatConst_D110) {
                *factor = (time - ring->At(i).time) / duration;
            } else {
                *factor = g_kFloatConst_D108;
            }
            *first = i;
            *second = i + 1;
            return true;
        }
    }
    return true;
}

extern void BallPredict_QuaternionSlerp(bpVec4* out, void* unusedR4, const bpVec4* first,
                                       const bpVec4* second, float factor); // @ 0x8223AED0

namespace {
float FlushPredictionVmx(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, 4);
    if ((bits & 0x7F800000u) == 0) bits &= 0x80000000u;
    __builtin_memcpy(&value, &bits, 4);
    return value;
}
}

// @ 0x821D72C0
void BallPredict_BlendSamples(gdBallPredictSample* out, void* /*unusedR4*/,
                             const gdBallPredictSample* first,
                             const gdBallPredictSample* second, float factor) {
    out->time = __builtin_fmaf(second->time - first->time, factor, first->time);
    out->time2 = __builtin_fmaf(second->time2 - first->time2, factor, first->time2);
    // The VMX factor is loaded from a single-precision stack spill.
    volatile float vectorFactor = factor;
    float* dst = &out->pos.x;
    const float* a = &first->pos.x;
    const float* b = &second->pos.x;
    for (int lane = 0; lane < 4; ++lane) {
        const float delta = FlushPredictionVmx(FlushPredictionVmx(b[lane]) - FlushPredictionVmx(a[lane]));
        const float product = FlushPredictionVmx(delta * FlushPredictionVmx(vectorFactor));
        dst[lane] = FlushPredictionVmx(product + FlushPredictionVmx(a[lane]));
    }
    out->vel = first->vel;
    out->angVel = first->angVel;
    out->bounced = first->bounced;
    out->flag9 = first->flag9;
    out->hittable = first->hittable != 0 && first->bounced == 0 &&
                    second->hittable != 0 && second->bounced == 0;
    bpVec4 orientation = first->orient;
    float dot = second->orient.y * orientation.y;
    dot = __builtin_fmaf(second->orient.z, orientation.z, dot);
    dot = __builtin_fmaf(second->orient.w, orientation.w, dot);
    dot = __builtin_fmaf(second->orient.x, orientation.x, dot);
    if (dot < g_kFloatConst_D110) {
        orientation = bpVec4{-orientation.x, -orientation.y, -orientation.z, -orientation.w};
    }
    BallPredict_QuaternionSlerp(&out->orient, nullptr, &orientation, &second->orient, factor);
}

// @ 0x821D95A8
void BallPredict_InterpolateSamples(void* ringPtr, void* unusedR4, gdBallPredictSample* out, float time) {
    int first = -1;
    int second = -1;
    float factor = g_kFloatConst_D110;
    if (BallPredict_FindNeighborIndices(ringPtr, unusedR4, &first, &second, &factor, time)) {
        auto* ring = static_cast<PredictionRing*>(ringPtr);
        BallPredict_BlendSamples(out, nullptr, &ring->At(first), &ring->At(second), factor);
    }
}

namespace {
struct CachedPredictionRing {
    PredictionRing ring;
    gdBallPredictSample cached;  // +0x2590 within the ring object
};
static_assert(__builtin_offsetof(CachedPredictionRing, cached) == 0x2590, "prediction cache offset");

struct TransitionState {
    uint8_t _pad00[4];
    float previousWindow;
    float blendRate;
    float hitTime;
    gdBallPredictData* banks[2];
};
}

extern uint32_t BallPredict_ShouldUsePrevious(void* state); // @ 0x821D3390
extern "C" const double g_kDoubleConst_79B00;               // @ 0x82079B00
extern "C" const double g_kDoubleConst_79B08;               // @ 0x82079B08

// @ 0x821D94B8
// An empty ring returns its existing cache without overwriting it.
gdBallPredictSample* BallPredict_GetInterpolatedSample(void* ringPtr, void* unusedR4, float time) {
    auto* ring = static_cast<CachedPredictionRing*>(ringPtr);
    int first = -1;
    int second = -1;
    float factor = g_kFloatConst_D110;
    if (BallPredict_FindNeighborIndices(ringPtr, unusedR4, &first, &second, &factor, time)) {
        BallPredict_BlendSamples(&ring->cached, nullptr, &ring->ring.At(first),
                                 &ring->ring.At(second), factor);
    }
    return &ring->cached;
}

// @ 0x821D7460
// Crossfade from the current trajectory toward the previous one, retaining the
// current ball height. Unlike within-trajectory interpolation, W is not written.
void BallPredict_BlendTransitionSamples(gdBallPredictSample* out, void* /*unusedR4*/,
                                       const gdBallPredictSample* first,
                                       const gdBallPredictSample* second, float factor) {
    out->time = __builtin_fmaf(second->time - first->time, factor, first->time);
    out->time2 = __builtin_fmaf(second->time2 - first->time2, factor, first->time2);
    out->pos.x = __builtin_fmaf(second->pos.x - first->pos.x, factor, first->pos.x);
    out->pos.y = first->pos.y;
    out->pos.z = __builtin_fmaf(second->pos.z - first->pos.z, factor, first->pos.z);
    out->vel = first->vel;
    out->angVel = first->angVel;
    out->bounced = first->bounced;
    out->flag9 = first->flag9;
    out->hittable = first->hittable != 0 && first->bounced == 0;
    bpVec4 orientation = first->orient;
    float dot = second->orient.y * orientation.y;
    dot = __builtin_fmaf(second->orient.z, orientation.z, dot);
    dot = __builtin_fmaf(second->orient.w, orientation.w, dot);
    dot = __builtin_fmaf(second->orient.x, orientation.x, dot);
    if (dot < g_kFloatConst_D110) {
        orientation = bpVec4{-orientation.x, -orientation.y, -orientation.z, -orientation.w};
    }
    BallPredict_QuaternionSlerp(&out->orient, nullptr, &orientation, &second->orient, factor);
}

// @ 0x821D3C60
void BallPredict_InterpolateState(void* statePtr, void* /*unusedR4*/, gdBallPredictSample* out, float time) {
    auto* state = static_cast<TransitionState*>(statePtr);
    if (static_cast<uint8_t>(BallPredict_ShouldUsePrevious(statePtr)) != 0) {
        gdBallPredictSample current;
        CopySample(current, *BallPredict_GetInterpolatedSample(state->banks[1]->m_samples, nullptr, time));
        gdBallPredictSample previous;
        CopySample(previous, *BallPredict_GetInterpolatedSample(state->banks[0]->m_samples, nullptr, time));
        const float raw = (time - state->hitTime) * state->blendRate;
        // PPC fsel chooses the lower bound for NaN and negative values.
        const double lower = raw >= 0.0f ? static_cast<double>(raw) : g_kDoubleConst_79B00;
        const float factor = static_cast<float>(lower - g_kDoubleConst_79B08 >= 0.0
                                                ? g_kDoubleConst_79B08 : lower);
        BallPredict_BlendTransitionSamples(out, nullptr, &current, &previous, factor);
    } else {
        BallPredict_InterpolateSamples(state->banks[1]->m_samples, nullptr, out, time);
    }
}
