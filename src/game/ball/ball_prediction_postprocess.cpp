// Final prediction timing and hit-ID bookkeeping.
#pragma clang fp contract(off)
#include "ball_predict.hpp"
#include "ball_prediction_postprocess.hpp"
#include <cmath>

namespace {
struct PredictionState {
    uint8_t _pad00[0x14];
    gdBallPredictData* prediction;
};
struct PredictionClock { uint8_t _pad00[0x30]; float now; };
}

extern void* g_game_state_ptr;                  // @ 0x8271A2F8
extern void* g_pongMatchTiming;                 // @ 0x8271A2E8
extern "C" const float lbl_825CB7C0[4];          // @ 0x825CB7C0
extern "C" const float lbl_825CB7D0[4];          // @ 0x825CB7D0
extern "C" const float lbl_82619BF0[4];          // @ 0x82619BF0
extern "C" const float lbl_82606750[4];          // @ 0x82606750
extern double crt_sin(double angle);             // @ 0x824301D8
extern void nop_8240E6D0(const char* format, ...); // @ 0x8240E6D0
extern void BallPredict_BuildHitIds(int bank);    // @ 0x82289B10
extern void BallPredict_RecoverHitIds(int bank);  // @ 0x82289E90

namespace {
float FlushVmx(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, 4);
    if ((bits & 0x7F800000u) == 0) bits &= 0x80000000u;
    __builtin_memcpy(&value, &bits, 4);
    return value;
}

float Dot3(const bpVec4& vector) {
    const double x = FlushVmx(vector.x);
    const double y = FlushVmx(vector.y);
    const double z = FlushVmx(vector.z);
    return FlushVmx(static_cast<float>((x * x + y * y) + z * z));
}

float RefinedLength(float square, float estimate) {
    const float y = estimate == FlushVmx(lbl_82619BF0[0]) ? lbl_82606750[0] : estimate;
    const float squareY = FlushVmx(FlushVmx(y) * FlushVmx(y));
    const float halfY = FlushVmx(FlushVmx(lbl_825CB7D0[0]) * FlushVmx(y));
    const float error = FlushVmx(-FlushVmx(FlushVmx(square * squareY) - FlushVmx(lbl_825CB7C0[0])));
    const float inverse = FlushVmx(FlushVmx(error * halfY) + FlushVmx(y));
    return FlushVmx(FlushVmx(square) * inverse);
}

float Length(const bpVec4& vector) {
    const float square = Dot3(vector);
    const float estimate = FlushVmx(static_cast<float>(1.0 / __builtin_sqrt(static_cast<double>(square))));
    return RefinedLength(square, estimate);
}
}

// @ 0x82289738
// The former ApplyLaunchSpin label was misleading: this changes only time.
// Start at the requested launch speed, then ease back to the original timing.
void BallPredict_RetimeSamplesForLaunchVelocity(const bpVec4* velocity, int /*unusedBank*/) {
    const bpVec4 requested = *velocity;
    const float requestedSquare = Dot3(requested);
    auto* prediction = static_cast<PredictionState*>(g_game_state_ptr)->prediction;
    if (requestedSquare < Dot3(prediction->At(1).vel)) return;
    float originalPreviousTime = prediction->At(1).time;
    if (prediction->m_count <= 2) return;
    const float requestedEstimate = FlushVmx(static_cast<float>(1.0 / __builtin_sqrt(static_cast<double>(requestedSquare))));
    for (int i = 2; i < prediction->m_count; ++i) {
        float factor = static_cast<float>(i - 2) * 0.06666667014360428f;
        const double lower = factor >= 0.0f ? static_cast<double>(factor) : 0.0;
        factor = static_cast<float>(lower - 1.0 >= 0.0 ? 1.0 : lower);
        const float eased = factor > 0.0f
            ? (factor < 1.0f ? static_cast<float>(crt_sin(factor * 1.5707963705062866f)) : 1.0f)
            : 0.0f;
        gdBallPredictSample& previous = prediction->At(i - 1);
        gdBallPredictSample& current = prediction->At(i);
        const float originalTime = current.time;
        const float originalDuration = originalTime - originalPreviousTime;
        originalPreviousTime = originalTime;
        bpVec4 displacement;
        const float* a = &previous.pos.x;
        const float* b = &current.pos.x;
        float* d = &displacement.x;
        for (int lane = 0; lane < 4; ++lane) {
            d[lane] = FlushVmx(FlushVmx(b[lane]) - FlushVmx(a[lane]));
        }
        const float distance = Length(displacement);
        const float speed = RefinedLength(requestedSquare, requestedEstimate);
        const float minimumDuration = distance / speed;
        const float delta = originalDuration - minimumDuration;
        const float duration = __builtin_fmaf(delta, eased, minimumDuration);
        current.time = previous.time + duration;
    }
}

// @ 0x82289A08
void BallPredict_ResetHitIds(int /*unusedBank*/) {
    auto* prediction = static_cast<PredictionState*>(g_game_state_ptr)->prediction;
    for (uint32_t i = 0; i < prediction->m_idCount; ++i) prediction->m_ids[i] = 0;
    prediction->m_idTime = -1.0f;
    BallPredict_BuildHitIds(1);
    if ((prediction->m_ids[0] & 1) == 0) BallPredict_RecoverHitIds(1);
    uint32_t* ids = prediction->m_ids;
    if ((ids[0] & 1) == 0) {
        nop_8240E6D0("Ball prediction outcome unknown!");
        ids[0] |= 1;
        prediction->m_ids[0] |= 2;
        prediction->m_idTime = static_cast<PredictionClock*>(g_pongMatchTiming)->now;
    }
}
