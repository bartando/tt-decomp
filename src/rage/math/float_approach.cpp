#include "rage/float_approach.hpp"

// @ 0x820C99B0 | size: 0x5C
bool pongPlayer_99B0_g(float* value, float target, float rate, float deltaTime) {
    float current = *value;
    if (current < target) {
        current = __builtin_fmaf(rate, deltaTime, current);
        *value = current;
        if (current > target) *value = target;
    } else if (current > target) {
        current = -__builtin_fmaf(rate, deltaTime, -current);
        *value = current;
        if (current < target) *value = target;
    }
    return *value == target;
}
