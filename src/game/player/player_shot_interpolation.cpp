// Spin-axis length and world-space conversion recovered from the original PPC.
#include <cstdint>
#include <cmath>

namespace {
// VMX arithmetic flushes subnormal operands/results while preserving zero's sign.
float flushVmx(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, sizeof bits);
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
        __builtin_memcpy(&value, &bits, sizeof value);
    }
    return value;
}
float multiplyVmx(float a, float b) {
    return flushVmx(flushVmx(a) * flushVmx(b));
}
}

// Clamp the xyz length; scaling also affects w, but the zero-length fallback
// writes only xyz. The bounds occupy f1 and f2, respectively.
// @ 0x821D4EA0 | size: 0xE0
void pongPlayer_4EA0_g(void* vector, float minLength, float maxLength) {
    auto* value = static_cast<float*>(vector);
    const float x = flushVmx(value[0]);
    const float y = flushVmx(value[1]);
    const float z = flushVmx(value[2]);
    const float lengthSq = flushVmx(static_cast<float>(
        double(x) * x + double(y) * y + double(z) * z));
    float bound;
    if (lengthSq > maxLength * maxLength) {
        bound = maxLength;
    } else {
        if (!(lengthSq < minLength * minLength)) return;
        if (lengthSq <= 1.0e-12f) {
            value[0] = 0.0f;
            value[1] = minLength;
            value[2] = 0.0f;
            return;
        }
        bound = minLength;
    }
    const float reciprocalLength = lengthSq == 0.0f ? 0.0f : 1.0f / std::sqrt(lengthSq);
    const float scale = reciprocalLength * bound;
    for (unsigned lane = 0; lane < 4; ++lane)
        value[lane] = multiplyVmx(value[lane], scale);
}
