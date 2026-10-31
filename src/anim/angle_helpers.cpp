// Wrapped angular limits used by creature rotation constraints.
#include "../game/creature/pong_creature.hpp"

extern "C" double fmod(double value, double period); // @ 0x82431D78

namespace {
constexpr float kPi = 0x1.921fb6p+1f;
constexpr float kTwoPi = 0x1.921fb6p+2f;
constexpr float kFullTurnThreshold = 0x1.921fb2p+2f;
}

// Canonicalize radians to (-pi, pi], rounding before and after the remainder.
// LocomotionStateAnim_WrapAngle (was util_F0A8) @ 0x820DF0A8 | size: 0x80
float LocomotionStateAnim_WrapAngle(float value) {
    const float offset = value < 0.0f ? -kPi : kPi;
    const float shifted = offset + value;
    const float remainder = static_cast<float>(fmod(shifted, double(kTwoPi)));
    const float result = remainder - offset;
    return result == -kPi ? kPi : result;
}

// The original reads only f1/f2/f3: there is no instance argument.
// LocomotionStateAnim::IsAngleCloser @ 0x823DA190 | size: 0x64
bool LocomotionStateAnim::IsAngleCloser(float target, float angle2, float angle3) {
    const float first = LocomotionStateAnim_WrapAngle(target - angle2);
    const float second = LocomotionStateAnim_WrapAngle(target - angle3);
    return __builtin_fabsf(first) < __builtin_fabsf(second);
}

// Normalize the interval and select its nearer endpoint when outside it.
// LocomotionStateAnim_A1F8_g @ 0x823DA1F8 | size: 0xE8
float LocomotionStateAnim_A1F8_g(float value, float rangeMin, float rangeMax) {
    const float wrapped = LocomotionStateAnim_WrapAngle(value);
    if (__builtin_fabsf(rangeMax - rangeMin) > kFullTurnThreshold)
        return wrapped;
    const float low = LocomotionStateAnim_WrapAngle(rangeMin);
    const float high = LocomotionStateAnim_WrapAngle(rangeMax);
    if (high < low) {
        const float upper = high + kTwoPi;
        if (wrapped >= low && wrapped <= upper)
            return wrapped;
    } else if (wrapped >= low && wrapped <= high) {
        return wrapped;
    }
    return LocomotionStateAnim::IsAngleCloser(wrapped, low, high) ? low : high;
}
