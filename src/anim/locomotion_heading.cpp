#include "locomotion_heading.hpp"
#include "rage/ptr32.hpp"

float LocomotionStateAnim_WrapAngle(float value); // @ 0x820DF0A8

namespace {
constexpr float kQuarterPi = 0.7853981852531433f;
constexpr float kThreeQuarterPi = 2.356194496154785f;
constexpr float kHalfPi = 1.5707963705062866f;
constexpr float kPi = 3.1415927410125732f;
constexpr float kTwoPi = 6.2831854820251465f;

float clampCoordinate(float value, float low, float high) {
    const float difference = value - low;
    const float lowerClamped = difference >= 0.0f ? value : low;
    const double upperDifference = double(lowerClamped) - double(high);
    return upperDifference >= 0.0 ? high : lowerClamped;
}
float ramp(float distance, float start, float end) {
    const float numerator = distance - start;
    const float denominator = end - start;
    const float value = numerator / denominator;
    return -value >= 0.0f ? 0.0f : value;
}
const float* rangeFor(void* state) {
    auto* bytes = static_cast<uint8_t*>(state);
    const int32_t index = *reinterpret_cast<int32_t*>(bytes + 0x1c);
    const auto* entries = rage::load_ptr32<uint8_t>(state, 0x130);
    return reinterpret_cast<const float*>(entries + static_cast<int64_t>(index) * 68 + 0x38);
}
}

// @ 0x820E6E90
float LocomotionStateAnim_ClampHeading(void* state, float heading) {
    auto* ops = static_cast<LocomotionHeadingOps*>(state);
    alignas(16) LocomotionHeadingVector lower, upper;
    if ((ops->GetBounds(&lower, &upper) & 0xffu) == 0) return heading;
    const LocomotionHeadingVector position = ops->GetPosition();
    const float x = clampCoordinate(position.x, lower.x, upper.x);
    const float z = clampCoordinate(position.z, lower.z, upper.z);
    const float* range = rangeFor(state);
    const float start = range[0], end = range[1];
    const float magnitude = __builtin_fabsf(heading);
    // Both original unordered branches select the side sector.
    if (!(magnitude <= kQuarterPi) && !(magnitude >= kThreeQuarterPi)) {
        const float lowDistance = __builtin_fabsf(x - lower.x);
        const float highDistance = __builtin_fabsf(x - upper.x);
        const bool nearerLow = lowDistance < highDistance;
        const bool forward = (ops->IsForwardSide() & 0xffu) != 0;
        const bool towardsLow = forward ? magnitude < kHalfPi : magnitude > kHalfPi;
        if (towardsLow != nearerLow) return heading;
        const float difference = lowDistance - highDistance;
        const float distance = difference >= 0.0f ? highDistance : lowDistance;
        if (!(distance < end)) return heading;
        const float scale = ramp(distance, start, end);
        if (heading > 0.0f)
            return __builtin_fmaf(heading - kHalfPi, scale, kHalfPi);
        return __builtin_fmaf(heading - (-kHalfPi), scale, -kHalfPi);
    }
    const float lowDistance = __builtin_fabsf(z - lower.z);
    const float highDistance = __builtin_fabsf(z - upper.z);
    const bool nearerLow = lowDistance < highDistance;
    const bool forward = (ops->IsForwardSide() & 0xffu) != 0;
    const bool towardsLow = forward ? heading > 0.0f : heading < 0.0f;
    if (towardsLow != nearerLow) return heading;
    const float difference = lowDistance - highDistance;
    const float distance = difference >= 0.0f ? highDistance : lowDistance;
    if (!(distance < end)) return heading;
    const float scale = ramp(distance, start, end);
    if (magnitude <= kQuarterPi) return scale * heading;
    if (heading < 0.0f) heading += kTwoPi;
    const float adjusted = __builtin_fmaf(heading - kPi, scale, kPi);
    return LocomotionStateAnim_WrapAngle(adjusted);
}

extern "C" {
extern const float g_blendCurveScale; // @ 0x82079B20
extern float g_blendCurveOffset; // @ 0x825C8078
}

// @ 0x820E6DD8
float LocomotionStateAnim_6DD8_w(void* state, float maxWeight, float heading) {
    (void)LocomotionStateAnim_ClampHeading(state, heading);
    const float duration = static_cast<LocomotionHeadingOps*>(state)->GetAnimationDuration();
    const float* range = rangeFor(state);
    const float start = range[0], end = range[1];
    if (duration < start) return 0.0f;
    if (duration < end) {
        const float numerator = duration - start;
        const float denominator = end - start;
        const float factor = numerator / denominator;
        const float blend = __builtin_fmaf(factor, g_blendCurveScale, g_blendCurveOffset);
        const float difference = blend - maxWeight;
        return difference >= 0.0f ? maxWeight : blend;
    }
    return maxWeight;
}
