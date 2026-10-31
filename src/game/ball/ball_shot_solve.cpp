// BallShot_Solve — choose a launch from angle samples around the initial solve.
// The helpers perform the expensive trajectory search; this routine chooses its
// height bounds and selects the requested candidate from their two sample sets.
#include "ball_shot_solve.hpp"

#include <cmath>
#include <stdint.h>

namespace ballshot {
using Vec4 = BallFlightVec4;

struct ShotSolveEntry {
    uint8_t _pad000[0x50];
    Vec4 target;
    int32_t trajectoryIndex;             // +0x60: sign chooses the sample set
    uint8_t _pad064[0x2C];
    Vec4 launchPosition;                 // +0x90
    uint8_t _pad0A0[0x2C];
    int32_t swingType;                    // +0xCC
    uint8_t _pad0D0[0xA8];
    float maxAngle;                       // +0x178
    float chosenAngle;                    // +0x17C
};

struct SolveTable {
    uint8_t _pad00[0x14];
    float height;
    float halfWidth;
};
struct SolveInput {
    uint8_t _pad00[0x84];
    float nearMargin, farMargin;
};
struct SolveBound { uint8_t _pad00[8]; float radius; };
struct SolveArchetype { uint8_t _pad00[0x0C]; SolveBound* bound; };
struct SolveBall { void* vtable; SolveArchetype* archetype; };
}

using namespace ballshot;

extern "C" const uint32_t g_affineXYZMask[4];       // @ 0x82619BE0
extern "C" const uint32_t g_affineHomogeneousW[4];  // @ 0x82619BD0
extern "C" const float lbl_82619BF0[4];            // @ 0x82619BF0
extern "C" const float lbl_82606750[4];            // @ 0x82606750
extern "C" const float lbl_825CB7C0[4];            // @ 0x825CB7C0
extern "C" const float lbl_825CB7D0[4];            // @ 0x825CB7D0
extern void* g_pTableDims;                          // @ 0x8271A304
extern void* g_input_obj_ptr;                       // @ 0x825EAB28
extern void** g_ppBallInst;                         // @ 0x8271A2F4
extern int32_t g_currentInputSlot;                  // @ 0x82606578
extern uint8_t g_ballSplashArray[];                 // @ 0x8261A3D0
extern int32_t g_shotSolveState;                    // @ 0x82606580

extern double crt_acos(double value);               // @ 0x82430E90


namespace {
float FlushVmx(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, sizeof(bits));
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
        __builtin_memcpy(&value, &bits, sizeof(bits));
    }
    return value;
}

float FloatBits(uint32_t bits) {
    float value;
    __builtin_memcpy(&value, &bits, sizeof(value));
    return value;
}

float Dot3(const Vec4& a, const Vec4& b) {
    double sum = static_cast<double>(FlushVmx(a.x)) * FlushVmx(b.x);
    sum += static_cast<double>(FlushVmx(a.y)) * FlushVmx(b.y);
    sum += static_cast<double>(FlushVmx(a.z)) * FlushVmx(b.z);
    return FlushVmx(static_cast<float>(sum));
}

Vec4 Normalize3(const Vec4& vector) {
    const float squareLength = Dot3(vector, vector);
    const float estimate = FlushVmx(static_cast<float>(1.0 / __builtin_sqrt(static_cast<double>(squareLength))));
    Vec4 result;
    const float* input = &vector.x;
    float* output = &result.x;
    for (int lane = 0; lane < 4; ++lane) {
        const float y = estimate == FlushVmx(lbl_82619BF0[lane]) ? lbl_82606750[lane] : estimate;
        const float square = FlushVmx(FlushVmx(y) * FlushVmx(y));
        const float halfY = FlushVmx(FlushVmx(lbl_825CB7D0[lane]) * FlushVmx(y));
        const float error = FlushVmx(-FlushVmx(FlushVmx(squareLength * square)
                                                    - FlushVmx(lbl_825CB7C0[lane])));
        const float inverse = FlushVmx(FlushVmx(error * halfY) + FlushVmx(y));
        output[lane] = FlushVmx(FlushVmx(input[lane]) * inverse);
    }
    return result;
}

float BallHeight() {
    const auto* table = static_cast<const SolveTable*>(g_pTableDims);
    const auto* ball = static_cast<const SolveBall*>(*g_ppBallInst);
    const float radius = ball ? ball->archetype->bound->radius : 0.0f;
    return table->height + radius;
}
}

// @ 0x822851D0
int BallShot_Solve(void* entryPtr, const Vec4* start, const Vec4* target,
                   Vec4* spin, Vec4* velocity, float speed) {
    auto* entry = static_cast<ShotSolveEntry*>(entryPtr);
    const float* launch = &entry->launchPosition.x;
    const float* destination = &entry->target.x;
    bool allGreater = true;
    for (int lane = 0; lane < 4; ++lane) {
        uint32_t a, b;
        __builtin_memcpy(&a, launch + lane, sizeof(a));
        __builtin_memcpy(&b, destination + lane, sizeof(b));
        a = (a & g_affineXYZMask[lane]) | g_affineHomogeneousW[lane];
        b &= g_affineXYZMask[lane];
        allGreater &= FlushVmx(FloatBits(a)) > FlushVmx(FloatBits(b));
    }
    const float initialAngle = allGreater ? -0x1.921fb6p-4f : 0x1.921fb6p+0f;
    Vec4 raisedTarget = *target;
    raisedTarget.y = BallHeight();
    g_shotSolveState = 0;
    BallShot_SolveTrajectory(entry, start, &raisedTarget, 0, spin, 0, velocity, 0,
                            false, nullptr, speed, initialAngle);
    if (entry->swingType == 6 || entry->swingType == 11) return 1;

    Vec4 horizontal = *velocity;
    horizontal.y = 0.0f;
    const Vec4 normalized = Normalize3(*velocity);
    const Vec4 normalizedHorizontal = Normalize3(horizontal);
    const float angle = static_cast<float>(crt_acos(Dot3(normalized, normalizedHorizontal)));
    constexpr float step = 0.032258063554763794f;
    constexpr float epsilon = 0.0000009999999974752427f;
    SolveSampleSet increasing;
    increasing.lowAngle = angle;
    increasing.highAngle = entry->maxAngle;
    increasing.step = __builtin_fmaf(entry->maxAngle - angle, step, -epsilon);
    BallShot_SampleAngles(entry, start, &raisedTarget, 0, spin, &increasing, 1, speed);

    const float lowAngle = start->y > BallHeight() ? 0.0f : 0.009999999776482582f;
    SolveSampleSet decreasing;
    decreasing.lowAngle = lowAngle;
    decreasing.highAngle = angle;
    decreasing.step = __builtin_fmaf(angle - lowAngle, step, -epsilon);
    BallShot_SampleAngles(entry, start, &raisedTarget, 0, spin, &decreasing, 0, speed);

    const float halfWidth = static_cast<const SolveTable*>(g_pTableDims)->halfWidth;
    const auto* input = static_cast<const SolveInput*>(g_input_obj_ptr);
    const float half = halfWidth * 0.5f;
    const float lower = half + 0.20000000298023224f;
    const float upper = (__builtin_fmaf(halfWidth, 0.5f, input->farMargin) + input->nearMargin) + half;
    const float distance = __builtin_fabsf(entry->launchPosition.z);
    const float aboveLower = distance - lower;
    const float clampedLower = aboveLower >= 0.0f ? distance : lower;
    const double belowUpper = static_cast<double>(clampedLower) - upper;
    const float clamped = belowUpper >= 0.0 ? upper : clampedLower;
    float ratio = (clamped - lower) / (upper - lower);
    ratio = ratio >= 0.0f ? ratio : 0.0f;
    if (static_cast<double>(ratio) - 1.0 >= 0.0) ratio = 1.0f;
    const float threshold = __builtin_fmaf(-ratio, 30.0f, 62.0f) * 0.01745329238474369f;

    // The selected index comes from the active player's entry, not entryPtr.
    const uint32_t slot = static_cast<uint32_t>(g_currentInputSlot);
    int32_t selected;
    __builtin_memcpy(&selected, g_ballSplashArray + slot * 0x1A0u + 0x60, sizeof(selected));
    if (increasing.count <= 0) {
        entry->chosenAngle = angle;
        return 1;
    }
    const uint32_t magnitude = selected < 0 ? 0u - static_cast<uint32_t>(selected)
                                           : static_cast<uint32_t>(selected);
    const SolveSample* chosen;
    if (selected < 0) {
        chosen = &decreasing.samples[magnitude];
    } else {
        uint32_t index = magnitude;
        chosen = &increasing.samples[index];
        while (index > 0 && !(chosen->angle < threshold)) {
            chosen = &increasing.samples[--index];
        }
    }
    entry->chosenAngle = chosen->angle;
    velocity->x = chosen->velocity.x;
    velocity->y = chosen->velocity.y;
    velocity->z = chosen->velocity.z;
    return 1;
}
