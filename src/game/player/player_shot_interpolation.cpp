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

extern "C" void* g_gameDataMgr; // @ 0x8271A2E4
extern "C" void* g_pCameraSharedState; // @ 0x8271A32C
extern "C" float g_spinAxisRotation; // @ 0x82606498
extern "C" const float g_phTwoPi; // @ 0x8202C02C
extern "C" const float lbl_82606750[4]; // @ 0x82606750
extern int fxBallSplash2D_5998_g(void*); // @ 0x821D5998
extern float util_E1B0(void*, uint32_t, int32_t, uint8_t); // @ 0x8220E1B0
extern void phBoundCapsule_RotateAxisXZ(float*, float); // @ 0x8223AB00
extern uint8_t pongPlayer_7CC0_g(void*); // @ 0x821E7CC0
extern void phBoundCapsule_2E70_fw(void*, float*); // @ 0x82282E70

namespace {
template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}
}

// Convert a shot's local spin axis to world space. The final flag uses its low
// byte only, as does the camera-side predicate's integer return.
// @ 0x821D5010 | size: 0x118
void pongPlayer_5010_g(void* axis, void* output, void* hit, int adjustForTable) {
    const uint8_t special = (at<uint16_t>(hit, 0xC6) & 0x1000) != 0;
    const uint32_t kind = fxBallSplash2D_5998_g(hit);
    const float turns = util_E1B0(at<void*>(g_gameDataMgr, 0x14), kind,
                                  at<int32_t>(hit, 0x9C), special);
    const float scale = turns * g_phTwoPi;
    auto* source = static_cast<float*>(axis);
    auto* spin = static_cast<float*>(output);
    for (unsigned lane = 0; lane < 4; ++lane)
        spin[lane] = multiplyVmx(source[lane], scale);
    phBoundCapsule_RotateAxisXZ(spin, g_spinAxisRotation);
    if (!(at<float>(hit, 0x68) > 0.0f)) {
        for (unsigned lane = 0; lane < 4; ++lane)
            spin[lane] = flushVmx(flushVmx(lbl_82606750[lane]) - flushVmx(spin[lane]));
    }
    const uint8_t side = pongPlayer_7CC0_g(g_pCameraSharedState);
    if (static_cast<uint8_t>(side) == 0) spin[1] = -spin[1];
    if (static_cast<uint8_t>(adjustForTable) != 0)
        phBoundCapsule_2E70_fw(hit, spin);
}

extern "C" const float lbl_825C5938; // @ 0x825C5938

// Classify the dominant local spin axis. Equal nonzero magnitudes prefer y;
// zero/unordered components contribute no direction. Positive x maps to 1,
// negative x to 0, positive y to 2 and negative y to 3.
// @ 0x821D5998 | size: 0x140
int fxBallSplash2D_5998_g(void* hit) {
    const float rawX = at<float>(hit, 0x40);
    const float rawY = at<float>(hit, 0x44);
    float x = rawX < 0.0f ? -rawX : rawX > 0.0f ? rawX * lbl_825C5938 : 0.0f;
    float y = rawY > 0.0f ? rawY * lbl_825C5938 : rawY < 0.0f ? -rawY : 0.0f;
    if (std::fabs(x) > 0.0f && std::fabs(y) > 0.0f) {
        if (std::fabs(x) > std::fabs(y)) y = 0.0f;
        else x = 0.0f;
    }
    if (std::fabs(x) > 0.0f) return x < 0.0f ? 1 : 0;
    if (std::fabs(y) > 0.0f) return y > 0.0f ? 3 : 2;
    return 0;
}
