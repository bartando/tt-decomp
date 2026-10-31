#include "grc/resource_release.hpp"
#include "crt/crt_init.h"
#include "rage/grc_command_stream.hpp"
#include <cstring>

extern "C" void DbgBreakPoint(); // @ 0x8258662C
extern "C" void grcTexture_ReleaseResource(void* resource); // @ 0x82352708

namespace {
uint32_t grcCacheBase(uint32_t address) {
    return (address & 0x1FFFFFFFu) + (((address >> 20) + 0x200u) & 0x1000u)
           - 0x40000000u;
}

// The resource packs cache addresses as Xbox virtual-address words. Decode
// those words through the same arena translation as stored game pointers.
void* grcCachePointer(uint32_t address) {
    rage::ptr32<void> pointer;
    std::memcpy(&pointer, &address, sizeof(pointer));
    return pointer.get();
}
}

// Drop one page reference (bits 12..15). On the last reference, invalidate
// each packed 128-byte range before passing its decoded endpoints to the cache
// helper. That callback may change the second range or the address-mode flag.
// @ 0x82352CC8 | size: 0xF0
void grc_2CC8(void* resource, uint32_t data, uint32_t auxiliary) {
    auto* words = static_cast<uint32_t*>(resource);
    const uint32_t flags = words[0] - 0x1000u;
    words[0] = flags;
    if ((flags & 0xF000u) == 0) {
        const uint32_t first = words[2];
        if (first != 0xFFFF0000u) {
            words[2] = 0xFFFF0000u;
            const uint32_t base = flags & 0x40000000u ? data : grcCacheBase(data);
            rage_EEC0(grcCachePointer(base + ((first >> 16) << 7)),
                      grcCachePointer(base + ((first & 0xFFFFu) << 7)));
        }
        if (auxiliary != 0) {
            const uint32_t second = words[3];
            if (second != 0xFFFF0000u) {
                words[3] = 0xFFFF0000u;
                const uint32_t base = words[0] & 0x40000000u ? auxiliary : grcCacheBase(auxiliary);
                rage_EEC0(grcCachePointer(base + ((second >> 16) << 7)),
                          grcCachePointer(base + ((second & 0xFFFFu) << 7)));
            }
        }
    }
    __atomic_thread_fence(__ATOMIC_SEQ_CST);
}

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
