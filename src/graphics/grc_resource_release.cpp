#include "grc/resource_release.hpp"
#include "crt/crt_init.h"
#include <cstring>

extern "C" void DbgBreakPoint(); // @ 0x8258662C
extern "C" void grcTexture_ReleaseResource(void* resource); // @ 0x82352708

// Low eight flag bits hold the reference count. A type-4 resource can retain
// another resource at +0x2C; release it before reloading the parent's flags.
// @ 0x82352EE0 | size: 0x80
uint32_t grcResource_ReleaseRef(void* resource) {
    auto* flags = static_cast<uint32_t*>(resource);
    if ((*flags & 255) == 1) {
        if ((*flags & 0x70000u) == 0x40000u) {
            if (void* linked = rage::load_ptr32<void>(resource, 0x2C))
                grcResource_ReleaseRef(linked);
        }
        if ((*flags & 0xF80000u) == 0) {
            grcTexture_ReleaseResource(resource);
            return 0;
        }
    }
    *flags -= 1;
    return *flags & 255;
}

// Drop an owned allocation reference, assert that no other owners remain,
// and clear the four-byte holder only after the deallocator/debug callback.
// @ 0x82151068 | size: 0x5C
void grcDevice_cleanupInternal(void* holder) {
    auto* slot = static_cast<rage::ptr32<void>*>(holder);
    if (void* resource = slot->get()) {
        auto* references = reinterpret_cast<uint32_t*>(static_cast<uint8_t*>(resource) + 4);
        *references -= 1;
        if (*references == 0) _locale_register(resource, 0x24800000);
        else DbgBreakPoint();
        *slot = nullptr;
    }
}

// Retail order is the second surface, first surface, singleton surface, then
// singleton texture. Callbacks may replace slots; each processed slot is cleared.
// @ 0x8214F338 | size: 0xC4
void grcDevice_releaseSharedResources() {
    rage::ptr32<void>* slots[] = {&g_grcSharedSurfacePair[1], &g_grcSharedSurfacePair[0],
                                  &g_grcSharedSurface, &g_grcSharedTexture};
    for (auto* slot : slots) {
        if (void* resource = slot->get()) {
            if (grcResource_ReleaseRef(resource) != 0) DbgBreakPoint();
            *slot = nullptr;
        }
    }
}
