#include "rage/mat33.hpp"
#include <cstdint>

extern void ph_SinCos(float* cosine, float* sine, double angle); // @ 0x820D04F0

#if defined(__clang__)
#pragma clang fp contract(off)
#elif defined(__GNUC__)
#pragma GCC optimize("fp-contract=off")
#endif

namespace rage {

// These helpers are rotations, despite the generated capsule names. Keep their
// output in r3 and their double angle in f1, without a spurious this argument.
extern void mat33RotationX(float* out, double angle); // @ 0x820C3F10
extern void mat33RotationY(float* out, double angle); // @ 0x820C3F98
extern void mat33RotationZ(float* out, double angle); // @ 0x820C4020
extern void mat33RotationNormalizedAxis(float* out, const float* axis, double angle); // @ 0x820C40A8

namespace {

float flushRotationVmx(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, sizeof(bits));
    if ((bits & 0x7f800000u) == 0) {
        bits &= 0x80000000u;
        __builtin_memcpy(&value, &bits, sizeof(value));
    }
    return value;
}

} // namespace

// Formerly phBoundCapsule_3DA0_g. Build a row-vector axis-angle rotation;
// zero angle writes identity without touching the axis or any row's w padding.
// @ 0x820C3DA0 | size: 0x170
void mat33RotationAxisAngle(float* out, const float* axis, double angle) {
    if (angle == 0.0) {
        out[0] = 1.0f; out[1] = 0.0f; out[2] = 0.0f;
        out[4] = 0.0f; out[5] = 1.0f; out[6] = 0.0f;
        out[8] = 0.0f; out[9] = 0.0f; out[10] = 1.0f;
        return;
    }

    // Scalar comparisons precede VMX flushing. bgt skips the negation, so an
    // unordered coordinate also negates the angle; <= would miss that case.
    const float x = axis[0], y = axis[1], z = axis[2];
    if (x == 0.0f) {
        if (y == 0.0f) {
            mat33RotationZ(out, z > 0.0f ? angle : -angle);
            return;
        }
        if (z == 0.0f) {
            mat33RotationY(out, y > 0.0f ? angle : -angle);
            return;
        }
    } else if (y == 0.0f && z == 0.0f) {
        mat33RotationX(out, x > 0.0f ? angle : -angle);
        return;
    }

    // vmsum3fp sums the products before rounding. Retain the reciprocal-square-
    // root refinement and every VMX rounding/flush boundary, including lane w.
    float vector[4];
    for (unsigned lane = 0; lane < 4; ++lane)
        vector[lane] = flushRotationVmx(axis[lane]);
    double dot = 0.0;
    for (unsigned lane = 0; lane < 3; ++lane)
        dot += static_cast<double>(vector[lane]) * vector[lane];
    const float lengthSq = flushRotationVmx(static_cast<float>(dot));
    float reciprocal = flushRotationVmx(static_cast<float>(1.0 / __builtin_sqrt(static_cast<double>(lengthSq))));
    if (reciprocal == __builtin_inff()) reciprocal = 0.0f;
    const float squared = flushRotationVmx(reciprocal * reciprocal);
    const float product = flushRotationVmx(lengthSq * squared);
    alignas(16) float normalized[4];
    for (unsigned lane = 0; lane < 4; ++lane) {
        const float one = lane < 3 ? 1.0f : 0.0f;
        const float half = lane < 3 ? 0.5f : 0.0f;
        const float halfReciprocal = flushRotationVmx(half * reciprocal);
        const float error = -flushRotationVmx(product - one);
        const float correction = flushRotationVmx(error * halfReciprocal);
        const float scale = flushRotationVmx(correction + reciprocal);
        // Preserve a NaN already present in the source lane (not a NaN from
        // the scale); scalar PPC multiplication otherwise picks the latter.
        normalized[lane] = __builtin_isnan(vector[lane]) ? vector[lane] + 0.0f
                                                        : flushRotationVmx(vector[lane] * scale);
    }
    mat33RotationNormalizedAxis(out, normalized, angle);
}

// Former auto-name LocomotionStateAnim_8278_g. Row-vector XYZ Euler rotation.
// @ 0x82118278 | size: 0x138
void mat33FromEuler(float* out, const float* angles) {
    float sx = 0.0f, cx = 1.0f;
    float sy = 0.0f, cy = 1.0f;
    float sz = 0.0f, cz = 1.0f;
    if (angles[0] != 0.0f) ph_SinCos(&cx, &sx, angles[0]);
    if (angles[1] != 0.0f) ph_SinCos(&cy, &sy, angles[1]);
    if (angles[2] != 0.0f) ph_SinCos(&cz, &sz, angles[2]);
    // Snapshot every angle before stores: the input may overlap the output.
    const float czsy = cz * sy, szsy = sz * sy;
    const float szcx = sz * cx, czcx = cz * cx;
    const float szsx = sz * sx, czsx = cz * sx;
    out[0] = cz * cy;
    out[1] = sz * cy;
    out[2] = -sy;
    out[6] = cy * sx;
    out[4] = __builtin_fmaf(czsy, sx, -szcx);
    out[5] = __builtin_fmaf(szsy, sx, czcx);
    out[10] = cy * cx;
    out[8] = __builtin_fmaf(czsy, cx, szsx);
    out[9] = __builtin_fmaf(szsy, cx, -czsx);
}

} // namespace rage
