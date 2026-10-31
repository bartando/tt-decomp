// Saturating sine/cosine curves used by pose crossfades.
#include <cstdint>

extern double crt_cos(double); // @ 0x824302B0

// Multiply rounds to float before entering CRT; unordered inputs map to zero.
// @ 0x820CB6F0 | size: 0x74
float util_B6F0(float value) {
    if (!(value > 0.0f)) return 0.0f;
    if (!(value < 1.0f)) return 1.0f;
    const float angle = value * 1.5707963705062866f;
    const float cosine = static_cast<float>(crt_cos(angle));
    return 1.0f - cosine;
}

// @ 0x820CB768 | size: 0x98
float cmSmoothRemap_B768(float value) {
    if (!(value > 0.0f)) return 0.0f;
    if (!(value < 1.0f)) return 1.0f;
    const float angle = value * 3.1415927410125732f;
    const float cosine = static_cast<float>(crt_cos(angle));
    const float shifted = 1.0f - cosine;
    return shifted * 0.5f;
}
