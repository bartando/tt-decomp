// Quaternion interpolation used by ball prediction and animation helpers.
#include "ball_predict.hpp"
#include "../../rage/animation/rage_anim.hpp"

#include <cmath>

#pragma clang fp contract(off)

extern "C" const float g_kFloatConst_D108;  // @ 0x8202D108
extern "C" const float g_kFloatConst_D10C;  // @ 0x8202D10C
extern "C" const float g_kFloatConst_D110;  // @ 0x8202D110
extern const float g_lookAtMultiplier;      // @ 0x8202D184
extern const float lbl_825C5938;           // @ 0x825C5938
extern double crt_acos(double value);      // @ 0x82430E90
extern double crt_sin(double angle);       // @ 0x824301D8

// @ 0x82137BF8
float BallPredict_QuaternionAngle(const bpVec4* first, const bpVec4* second) {
    float dot = second->z * first->z;
    dot = __builtin_fmaf(second->w, first->w, dot);
    dot = __builtin_fmaf(second->y, first->y, dot);
    dot = __builtin_fmaf(second->x, first->x, dot);
    // Bounds are strict. Unordered dot products go through acos as in the PPC.
    if (!(dot <= lbl_825C5938) && !(dot >= g_kFloatConst_D108)) {
        const float angle = static_cast<float>(crt_acos(__builtin_fabsf(dot)));
        return angle * g_lookAtMultiplier;
    }
    return g_kFloatConst_D110;
}

// @ 0x8223AED0
void BallPredict_QuaternionSlerp(bpVec4* out, void* /*unusedR4*/, const bpVec4* first,
                                const bpVec4* second, float factor) {
    const float halfAngle = BallPredict_QuaternionAngle(first, second) * g_kFloatConst_D10C;
    const float sine = static_cast<float>(crt_sin(halfAngle));
    if (sine == g_kFloatConst_D110) {
        *out = *first;
        return;
    }
    const float scaledAngle = halfAngle * factor;
    const float reciprocal = g_kFloatConst_D108 / sine;
    const float firstWeight = static_cast<float>(crt_sin(halfAngle - scaledAngle)) * reciprocal;
    const float secondWeight = static_cast<float>(crt_sin(scaledAngle)) * reciprocal;
    // The first lane accumulates in the opposite order to the following lanes.
    out->x = __builtin_fmaf(first->x, firstWeight, second->x * secondWeight);
    out->y = __builtin_fmaf(second->y, secondWeight, first->y * firstWeight);
    out->z = __builtin_fmaf(second->z, secondWeight, first->z * firstWeight);
    out->w = __builtin_fmaf(second->w, secondWeight, first->w * firstWeight);
    rage::NormalizeQuaternion(&out->x);
}
