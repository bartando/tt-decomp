#pragma once
#include "rage/localized_font.hpp"

extern "C" void* g_sda_base; // @ 0x82600000

namespace {
class FontAllocator {
public:
    virtual void Destroy() = 0;
    virtual void* Allocate(uint32_t bytes, uint32_t alignment) = 0;
    virtual void Free(void* pointer) = 0;
};

inline FontAllocator* currentFontAllocator() {
    void* thread = rage::load_ptr32<void>(g_sda_base, 0);
    return rage::load_ptr32<FontAllocator>(thread, 4);
}
}
