#pragma once
#include <cstdint>
#include "rage/ptr32.hpp"

namespace rage {
struct XactFade {
    // Retail callbacks occupy slots 0/1; there is no destructor slot.
    virtual void FadeOutComplete() = 0;
    virtual void FadeInComplete() = 0;
    float value;
    uint16_t duration;
    uint16_t reserved;
    uint32_t curve;
    uint32_t state;
    float progress;
};
static_assert(sizeof(void*) != 4 || sizeof(XactFade) == 24);
void xactFade_ApplyCurve(XactFade* fade); // @ 0x82453A98
int32_t xactFade_Update(XactFade* fade); // @ 0x82453B48
} // namespace rage
