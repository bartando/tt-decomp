#pragma once
#include <cstdint>

namespace rage {
struct XactFade {
    void** vtable;
    float value;
    uint16_t duration;
    uint16_t reserved;
    uint32_t curve;
    uint32_t state;
    float progress;
};
int32_t xactFade_Update(XactFade* fade); // @ 0x82453B48
} // namespace rage
