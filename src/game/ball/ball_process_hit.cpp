#include "game/game_message.hpp"
// Rebuild the prediction after a hit. The authoritative implementation is
// disasm/sections/.text.s, 0x82287B50..0x82288364.
#include "ball_predict.hpp"
#include "ball_prediction_postprocess.hpp"
#include "ball_flight.hpp"

#include <cmath>

namespace {

struct HitView {
    uint8_t _pad00[0x40];
    bpVec4 spinAxis;                  // +0x40
    uint8_t _pad50[0x10];
    bpVec4 position;                  // +0x60
    bpVec4 launchVelocity;                // +0x70
    uint8_t _pad80[4];
    float pace;                       // +0x84
    uint8_t _pad88[0x3E];
    uint16_t flags;                   // +0xC6
    uint8_t _padC8[0x6C];
    float time;                       // +0x134
};

struct GameStateView {
    uint8_t _pad00[0x14];
    gdBallPredictData* predict;        // +0x14
    uint8_t _pad18[0x10];
    float samplePeriod;               // +0x28
};

struct MatchClockView {
    uint8_t _pad00[0x30];
    float now;                        // +0x30
};

struct InputView {
    uint8_t _pad00[0x104];
    float pace;                       // +0x104
};

struct LoopView {
    uint8_t _pad00[0x208];
    float frameRate;                  // +0x208
};

struct BallCountersView {
    uint8_t _pad00[0xC0];
    uint32_t counterC0, counterC4;
};

struct BallBoundView {
    uint8_t _pad00[8];
    float radius;
};

struct BallArchetypeView {
    uint8_t _pad00[0xC];
    BallBoundView* bound;
};

struct BallInstanceView {
    void* vtable;
    BallArchetypeView* archetype;
};

struct ReplayView {
    uint8_t _pad00000[0xE8E8];
    int32_t sampleCount;              // +0x0E8E8
    uint8_t _pad0E8EC[0x68CF0 - 0xE8EC];
    uint32_t mode;                    // +0x68CF0
};

float FlushVmx(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, 4);
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
        __builtin_memcpy(&value, &bits, 4);
    }
    return value;
}

float SpinSquared3(const bpVec4& spin) {
    const double x = FlushVmx(spin.x);
    const double y = FlushVmx(spin.y);
    const double z = FlushVmx(spin.z);
    return FlushVmx(static_cast<float>((x * x + y * y) + z * z));
}

bpVec4 CopyVector(const BallFlightVec4& v) {
    return bpVec4{v.x, v.y, v.z, v.w};
}

} // namespace

extern void* g_game_state_ptr;                              // @ 0x8271A2F8
extern void* g_input_obj_ptr;                               // @ 0x825EAB28
extern void* g_loop_obj_ptr;                                // @ 0x825EAB30
extern void** g_ppBallInst;                                 // @ 0x8271A2F4
extern "C" void* g_pongMatchTiming;                         // @ 0x8271A2E8
extern "C" void* g_pReplayStateData;                        // @ 0x8271A2EC
extern "C" uint8_t g_replayStateData[20];                   // @ 0x825CB3C0

struct RTTITypeDescriptor;
extern RTTITypeDescriptor g_typeDescriptor_phInst;           // @ 0x825D2CB8
extern RTTITypeDescriptor g_typeDescriptor_pongBallInstance; // @ 0x825D2CD4
extern "C" void* RTDynamicCast(void*, int, const void*, const void*, int); // @ 0x82430978
extern int io_Input_poll_9D68(void* input);                  // @ 0x821C9D68
extern void nop_8240E6D0(const char* format, ...);            // @ 0x8240E6D0
extern void game_3860(void* state, int kind, const char* name); // @ 0x821D3860
extern void BallPredict_StepSample(gdBallPredictSample* sample, int bank); // @ 0x82288368
extern void BallReplay_RemoveSample(void* queue, int index); // @ 0x821CE910
extern void gdReplayMgr_RecordBallSample(void* replay, bpReplayBall* sample); // @ 0x821CD0F8
extern void BallPredict_Dump(gdBallPredictData* data);        // @ 0x821D9238
extern int BallPredict_GetInitialVelocities(gdBallPredictData* data, bpVec4* velocity,
                                            bpVec4* spin);  // @ 0x821D8C70
extern void pongPlayer_5010_g(void* sub, void* output, void* parent, int flag); // @ 0x821D5010
extern void pg_70C8_g();                                    // @ 0x822870C8

namespace {
GameStateView* GameState() { return static_cast<GameStateView*>(g_game_state_ptr); }
MatchClockView* Clock() { return static_cast<MatchClockView*>(g_pongMatchTiming); }
}

// @ 0x821E6470
// Assignment leaves the shot's padding bytes untouched, including +0xB5.
bpShot* ballPredict_CopyShot(bpShot* dst, const bpShot* src) {
    for (int i = 0; i < 3; ++i) dst->f00[i] = src->f00[i];
    dst->v10 = src->v10;
    dst->i20 = src->i20;
    dst->v30[0] = src->v30[0];
    dst->v30[1] = src->v30[1];
    dst->v50 = src->v50;
    dst->v60 = src->v60;
    for (int i = 0; i < 6; ++i) dst->f70[i] = src->f70[i];
    dst->i88 = src->i88;
    dst->i8C = src->i8C;
    dst->v90 = src->v90;
    dst->vA0 = src->vA0;
    dst->hB0 = src->hB0;
    dst->hB2 = src->hB2;
    dst->bB4 = src->bB4;
    dst->hB6 = src->hB6;
    return dst;
}

// @ 0x82287B50
void ballPredict_ProcessHit(void* hitPtr, const BallFlightVec4* velocity,
                            const BallFlightVec4* spin, int /*unusedR6*/,
                            int /*unusedR7*/, uint32_t updateNow, float time) {
    auto* hit = static_cast<HitView*>(hitPtr);
    bool live = static_cast<uint8_t>(io_Input_poll_9D68(g_input_obj_ptr)) != 0;
    if (!live) {
        uint32_t replayFlag;
        __builtin_memcpy(&replayFlag, g_replayStateData + 4, 4);
        live = replayFlag != 0;
    }
    const float pace = hit->pace;
    ballPredict_CopyShot(reinterpret_cast<bpShot*>(GameState()->predict->m_shot),
                         reinterpret_cast<const bpShot*>(static_cast<uint8_t*>(hitPtr) + 0x10));
    auto* ball = static_cast<BallCountersView*>(RTDynamicCast(*g_ppBallInst, 0,
        &g_typeDescriptor_phInst, &g_typeDescriptor_pongBallInstance, 0));
    if (!(SpinSquared3(CopyVector(*spin)) < 1000000.0f)) {
        nop_8240E6D0("ballPredict::ProcessHit() - postHitAngVel is bad");
    }

    GameStateView* state = GameState();
    ball->counterC0 = 0;
    ball->counterC4 = 0;
    gdBallPredictSample first{};
    first.orient.w = 1.0f;
    bpVec4 initialPosition;
    if (state->predict->m_count > 1 && !live && !(time >= 0.0f)) {
        const gdBallPredictSample& old = state->predict->At(0);
        first.time = old.time;
        first.time2 = old.time;
        initialPosition = old.pos;
        first.pos = initialPosition;
        first.vel = old.vel;
        first.angVel = old.angVel;
    } else {
        const float startTime = live ? (time >= 0.0f ? time : Clock()->now) : hit->time;
        first.time = startTime;
        first.time2 = startTime;
        initialPosition = hit->position;
        first.pos = initialPosition;
        first.vel = CopyVector(*velocity);
        first.angVel = CopyVector(*spin);
    }
    const float startTime = first.time;
    game_3860(state, 1, "ballPredict::ProcessHit");

    // Xenon's fsel implements a [-1,1] clamp with NaN choosing -1.
    const float lowerTest = pace - -1.0f;
    const double lower = lowerTest >= 0.0f ? static_cast<double>(pace) : -1.0;
    const double clamped = lower - 1.0 >= 0.0 ? 1.0 : lower;
    const float matchPace = static_cast<InputView*>(g_input_obj_ptr)->pace;
    float paceFactor;
    if (clamped <= 0.0) {
        const float delta = matchPace - 1.0f;
        paceFactor = __builtin_fmaf(delta, __builtin_fabsf(static_cast<float>(clamped)), 1.0f);
    } else {
        const float reciprocal = 1.0f / matchPace;
        const float delta = reciprocal - 1.0f;
        paceFactor = __builtin_fmaf(delta, static_cast<float>(clamped), 1.0f);
    }
    state = GameState();
    const float reciprocalRate = 1.0f / static_cast<LoopView*>(g_loop_obj_ptr)->frameRate;
    state->samplePeriod = reciprocalRate * paceFactor;
    state->predict->AddSample(&first);

    if (time < 0.0f) {
        auto* replay = static_cast<ReplayView*>(g_pReplayStateData);
        if (replay->mode == 0 && startTime != Clock()->now) {
            if ((hit->flags & 0x1000) != 0) {
                BallReplay_RemoveSample(static_cast<uint8_t*>(g_pReplayStateData) + 0x4020,
                                        replay->sampleCount - 1);
            }
            bpReplayBall record{};
            record.time = first.time;
            record.time2 = first.time2;
            record.pos = initialPosition;
            record.angVel = first.angVel;
            if (replay->mode == 0) gdReplayMgr_RecordBallSample(replay, &record);
        }
    }

    gdBallPredictSample sample{};
    sample.time = startTime;
    sample.time2 = startTime;
    sample.pos = initialPosition;
    sample.vel = CopyVector(*velocity);
    sample.angVel = CopyVector(*spin);
    sample.orient.w = 1.0f;
    state->predict->AddSample(&sample);

    int bounceRuns = 0;
    int expiredSteps = 0;
    float lastBounceZ = 0.0f;
    while (state->predict->m_count < gdBallPredictData::kMaxSamples) {
        BallPredict_StepSample(&sample, 1);
        state = GameState();
        if (sample.bounced != 0) {
            const gdBallPredictSample& previous = state->predict->At(state->predict->m_count - 1);
            const float z = sample.pos.z;
            if (previous.bounced == 0) {
                if ((z < 0.0f && lastBounceZ < 0.0f) ||
                    (z > 0.0f && lastBounceZ > 0.0f)) {
                    ++bounceRuns;
                } else {
                    bounceRuns = 1;
                }
            }
            lastBounceZ = z;
        }
        auto* instance = static_cast<BallInstanceView*>(*g_ppBallInst);
        const float radius = instance ? instance->archetype->bound->radius : 0.0f;
        if (sample.pos.y <= radius) ++expiredSteps;
        if (bounceRuns >= 2) ++expiredSteps;
        const bool complete = expiredSteps > 6 || bounceRuns > 2;

        // The original inlines AddSample here. Copy only the fields written by
        // gdBallPredictSample::operator=, preserving destination padding.
        gdBallPredictData* data = state->predict;
        if (data->m_count != gdBallPredictData::kMaxSamples) {
            if (++data->m_head == gdBallPredictData::kMaxSamples) data->m_head = 0;
            gdBallPredictSample& dst = data->m_samples[data->m_head];
            dst.time = sample.time;
            dst.time2 = sample.time2;
            dst.bounced = sample.bounced;
            dst.flag9 = sample.flag9;
            dst.hittable = sample.hittable;
            dst.pos = sample.pos;
            dst.vel = sample.vel;
            dst.angVel = sample.angVel;
            dst.orient = sample.orient;
            ++data->m_count;
        }
        if (complete) {
            state->predict->m_complete = 1;
            break;
        }
    }
    if (!live) BallPredict_RetimeSamplesForLaunchVelocity(&hit->launchVelocity, 1);
    BallPredict_ResetHitIds(1);
    state = GameState();
    state->predict->BuildBounceList(true);

    gdBallPredictData* data = state->predict;
    MatchClockView* clock = Clock();
    if (data->At(data->m_count - 1).time <= clock->now) {
        nop_8240E6D0("******** ballPredict::ProcessHit() - buffer will be immediately consumed! ********");
        nop_8240E6D0("Num samples: %d", data->m_count);
        BallPredict_Dump(state->predict);
        nop_8240E6D0("First Sample:");
        nop_8240E6D0("Last Sample:");
        nop_8240E6D0("RallyElapsedTime: %f", static_cast<double>(clock->now));
        nop_8240E6D0("ballPredict::ProcessHit() - buffer will be immediately consumed!");
    }
    if (static_cast<uint8_t>(updateNow) != 0) {
        pg_70C8_g();
        state = GameState();
    }
    bpVec4 outVelocity;
    bpVec4 outSpin;
    BallPredict_GetInitialVelocities(state->predict, &outVelocity, &outSpin);
    pongPlayer_5010_g(&hit->spinAxis, &outSpin, hit, 0);
    state = GameState();
    data = state->predict;
    if (!(SpinSquared3(outSpin) < 1000000.0f)) {
        nop_8240E6D0("gdBallPredictData::SetInitialBallAngVelocity() - angVelocity is bad");
    }
    data->m_hitVel = outSpin;
    state->predict->m_hitPos = outVelocity;
    PostGameMessageFmt(0x22, 0x40, "i", 1);
}
