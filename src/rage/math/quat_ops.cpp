#include "rage/quat.hpp"
#include <cstdint>
#include <cstring>

void util_BBB0(const float* quaternion, const float* vector, float* out); // @ 0x8223BBB0
extern "C" const float lbl_82606750[4]; // @ 0x82606750

namespace {
float flushRelativeVmx(float value) {
    uint32_t bits;
    std::memcpy(&bits, &value, 4);
    if ((bits & 0x7f800000u) == 0) {
        bits &= 0x80000000u;
        std::memcpy(&value, &bits, 4);
    }
    return value;
}
}

namespace rage {
// @ 0x8223B9A8
void quatMultiplyConjugate(float* out, const float* left, const float* right) {
    const float zz = left[2] * right[2];
    const float xz = __builtin_fmaf(left[0], right[0], zz);
    const float xyz = __builtin_fmaf(left[1], right[1], xz);
    out[3] = __builtin_fmaf(right[3], left[3], xyz);
    for (unsigned axis = 0; axis < 3; ++axis) {
        const unsigned first = (axis + 1) % 3;
        const unsigned second = (axis + 2) % 3;
        const float product = left[3] * right[axis];
        const float difference = __builtin_fmaf(left[axis], right[3], -product);
        const float cross = -__builtin_fmaf(left[first], right[second], -difference);
        out[axis] = __builtin_fmaf(left[second], right[first], cross);
    }
}
}

// @ 0x8223BE20
void* LocomotionStateAnim_BE20_g(void* out, void* left, void* right) {
    auto* result = static_cast<float*>(out);
    const auto* a = static_cast<const float*>(left);
    const auto* b = static_cast<const float*>(right);
    for (unsigned axis = 0; axis < 3; ++axis) result[axis] = -b[axis];
    result[3] = b[3];
    util_BBB0(result, b + 4, result + 4);
    for (unsigned lane = 0; lane < 4; ++lane)
        result[4 + lane] = flushRelativeVmx(flushRelativeVmx(lbl_82606750[lane]) - flushRelativeVmx(result[4 + lane]));
    alignas(16) float inverseTranslation[4];
    std::memcpy(inverseTranslation, result + 4, 16);
    util_BBB0(a, inverseTranslation, result + 4);
    for (unsigned lane = 0; lane < 4; ++lane)
        result[4 + lane] = flushRelativeVmx(flushRelativeVmx(result[4 + lane]) + flushRelativeVmx(a[4 + lane]));
    rage::quatMultiplyConjugate(result, a, b);
    return out;
}
